#!/usr/bin/env python3
"""
Generate a monthly progress report as a series of weekly narrative paragraphs.
No PR/issue/commit metadata is included — output is plain narrative prose only.

Format:
  ## Progress Report — <Month Year>

  **Week of <Mon> – <Fri>**
  <narrative paragraph>

  ...

Environment variables:
    GH_TOKEN        PAT with repo read scope (also used for GitHub Models).
    GITHUB_ACTOR    GitHub username to track (default: repository owner).
    REPORT_MONTH    ISO year-month (YYYY-MM). Defaults to last month.
"""

import os, sys, requests, calendar
from datetime import date, timedelta, timezone, datetime

# ── Config ────────────────────────────────────────────────────────────────────
TOKEN = os.environ.get("GH_TOKEN", "")
if not TOKEN:
    sys.exit("Error: GH_TOKEN is not set.")

GITHUB_ACTOR = (
    os.environ.get("GITHUB_ACTOR")
    or os.environ.get("GITHUB_REPOSITORY_OWNER", "")
)
REPORT_MONTH_STR = os.environ.get("REPORT_MONTH", "").strip()

if REPORT_MONTH_STR:
    year, month = map(int, REPORT_MONTH_STR.split("-"))
else:
    today = date.today()
    last_month = today.replace(day=1) - timedelta(days=1)
    year, month = last_month.year, last_month.month

MONTH_START = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
MONTH_END   = datetime(
    year, month, calendar.monthrange(year, month)[1], 23, 59, 59,
    tzinfo=timezone.utc,
)
MONTH_LABEL = date(year, month, 1).strftime("%B %Y")

GH_HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# ── GitHub REST helper ────────────────────────────────────────────────────────
def gh_get(url, params=None):
    results, p = [], {"per_page": 100, **(params or {})}
    while url:
        r = requests.get(url, headers=GH_HEADERS, params=p)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "items" in data:
            results.extend(data["items"])
        elif isinstance(data, list):
            results.extend(data)
        else:
            results.append(data)
        url, p = None, {}
        for part in r.headers.get("Link", "").split(","):
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
    return results

def parse_iso(ts):
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

def discover_repos():
    repos = gh_get(
        f"https://api.github.com/users/{GITHUB_ACTOR}/repos",
        {"type": "all", "sort": "updated"},
    )
    return [
        f"{r['owner']['login']}/{r['name']}"
        for r in repos
        if not r.get("archived", False)
    ]

# ── Data collection ───────────────────────────────────────────────────────────
def collect_week_prs(monday, friday):
    """PRs merged by GITHUB_ACTOR during monday–friday."""
    try:
        items = gh_get(
            "https://api.github.com/search/issues",
            {
                "q": (
                    f"author:{GITHUB_ACTOR} is:pr is:merged "
                    f"merged:{monday.strftime('%Y-%m-%d')}"
                    f"..{friday.strftime('%Y-%m-%d')}"
                )
            },
        )
        return [
            {"title": pr["title"], "body": (pr.get("body") or "")[:300]}
            for pr in items
        ]
    except Exception as e:
        print(f"Warning — PRs for week {monday}: {e}", file=sys.stderr)
        return []

def collect_all_commits(repos):
    """All commits by GITHUB_ACTOR this month, with date."""
    commits = []
    for repo in repos:
        try:
            items = gh_get(
                f"https://api.github.com/repos/{repo}/commits",
                {
                    "since": MONTH_START.isoformat(),
                    "until": MONTH_END.isoformat(),
                    "author": GITHUB_ACTOR,
                },
            )
            for c in items:
                dt = parse_iso(c["commit"]["author"]["date"])
                if dt and MONTH_START <= dt <= MONTH_END:
                    commits.append({
                        "message": c["commit"]["message"].split("\n")[0],
                        "date": dt,
                    })
        except Exception as e:
            print(f"Warning: {repo}: {e}", file=sys.stderr)
    return commits

# ── Week splitting ────────────────────────────────────────────────────────────
def get_work_weeks():
    """Mon–Fri work weeks that overlap with the report month."""
    first = date(year, month, 1)
    last  = date(year, month, calendar.monthrange(year, month)[1])
    monday = first - timedelta(days=first.weekday())
    weeks = []
    while monday <= last:
        friday = monday + timedelta(days=4)
        if friday >= first:          # week overlaps the month
            weeks.append((monday, friday))
        monday += timedelta(days=7)
    return weeks

# ── Narrative generation ──────────────────────────────────────────────────────
def _template_narrative(monday, friday, prs, commits):
    week_label = (
        f"week of {monday.strftime('%B %d')}–{friday.strftime('%B %d, %Y')}"
    )
    if not prs and not commits:
        return f"No activity was recorded for the {week_label}."
    parts = []
    if prs:
        titles = "; ".join(p["title"] for p in prs[:3])
        parts.append(f"Work focused on {titles}.")
    if commits:
        msgs = "; ".join(c["message"] for c in commits[:3])
        parts.append(f"Commit activity included: {msgs}.")
    return " ".join(parts)

def generate_week_narrative(monday, friday, prs, commits):
    week_label = (
        f"week of {monday.strftime('%B %d')}–{friday.strftime('%B %d, %Y')}"
    )
    if not prs and not commits:
        return f"No activity was recorded for the {week_label}."

    pr_block = (
        "\n".join(
            f"- {p['title']}"
            + (f"\n  {p['body'][:200]}" if p["body"].strip() else "")
            for p in prs
        )
        or "None"
    )
    commit_block = (
        "\n".join(f"- {c['message']}" for c in commits[:20]) or "None"
    )

    prompt = (
        f"Below is the GitHub activity for the {week_label}.\n\n"
        f"Pull Requests:\n{pr_block}\n\n"
        f"Commits:\n{commit_block}\n\n"
        "Write a concise 2–4 sentence narrative work summary. "
        "Focus on the themes and goals of the work, not individual items. "
        "Do NOT mention PR numbers, issue numbers, commit hashes, or URLs. "
        "Do NOT use bullet points. "
        "Write in plain prose as a single cohesive paragraph. "
        "Output only the paragraph — no headings, no preamble."
    )

    try:
        resp = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a concise technical writer summarising a "
                            "software developer's weekly GitHub activity into "
                            "plain narrative prose. Be specific about what was "
                            "worked on; avoid generic filler sentences. Never "
                            "include PR numbers, issue numbers, commit hashes, "
                            "or URLs."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 300,
                "temperature": 0.3,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(
            f"Warning — GitHub Models API unavailable ({e}); using template.",
            file=sys.stderr,
        )
        return _template_narrative(monday, friday, prs, commits)

# ── Write output ──────────────────────────────────────────────────────────────
def write_summary(week_narratives):
    lines = [f"## Progress Report — {MONTH_LABEL}\n\n"]
    for monday, friday, narrative in week_narratives:
        week_label = (
            f"Week of {monday.strftime('%B %d')} – {friday.strftime('%B %d')}"
        )
        lines.append(f"**{week_label}**\n\n")
        lines.append(f"{narrative}\n\n")
    lines.append("---\n\n")

    with open("monthly_summary_patch.md", "w") as f:
        f.writelines(lines)
    print("✓ Monthly summary written to monthly_summary_patch.md")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"Generating monthly report for {MONTH_LABEL} ({GITHUB_ACTOR})...")

    repos       = discover_repos()
    all_commits = collect_all_commits(repos)
    weeks       = get_work_weeks()

    week_narratives = []
    for monday, friday in weeks:
        week_start = datetime(monday.year, monday.month, monday.day, 0, 0, 0, tzinfo=timezone.utc)
        week_end   = datetime(friday.year, friday.month, friday.day, 23, 59, 59, tzinfo=timezone.utc)

        prs = collect_week_prs(monday, friday)
        commits = [c for c in all_commits if week_start <= c["date"] <= week_end]

        print(
            f"  {monday.strftime('%b %d')}–{friday.strftime('%b %d')}: "
            f"{len(prs)} PRs, {len(commits)} commits"
        )
        narrative = generate_week_narrative(monday, friday, prs, commits)
        week_narratives.append((monday, friday, narrative))

    write_summary(week_narratives)

if __name__ == "__main__":
    main()
