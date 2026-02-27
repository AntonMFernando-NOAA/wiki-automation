#!/usr/bin/env python3
"""
Generate a daily activity summary across all AntonMFernando-NOAA repositories.
Produces narrative bullet points per activity cluster plus a Context section,
matching the hand-written entry style used in the wiki.

Environment variables:
    GH_TOKEN         PAT with repo read scope.
    GITHUB_ACTOR     GitHub username to track (default: AntonMFernando-NOAA)
    SUMMARY_DATE     ISO date (YYYY-MM-DD). Defaults to yesterday.
"""

import os
import sys
import requests
from datetime import date, timedelta, timezone, datetime
from collections import defaultdict

# ── Config ────────────────────────────────────────────────────────────────────
TOKEN = os.environ.get("GH_TOKEN", "")
if not TOKEN:
    sys.exit("Error: GH_TOKEN is not set.")

GITHUB_ACTOR     = os.environ.get("GITHUB_ACTOR", "AntonMFernando-NOAA")
SUMMARY_DATE_STR = os.environ.get("SUMMARY_DATE", "").strip()
SUMMARY_DATE     = (date.fromisoformat(SUMMARY_DATE_STR) if SUMMARY_DATE_STR
                    else date.today() - timedelta(days=1))
DAY_START = datetime(SUMMARY_DATE.year, SUMMARY_DATE.month, SUMMARY_DATE.day,
                     0, 0, 0, tzinfo=timezone.utc)
DAY_END   = datetime(SUMMARY_DATE.year, SUMMARY_DATE.month, SUMMARY_DATE.day,
                     23, 59, 59, tzinfo=timezone.utc)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Theme detection keyword map (ordered: first match wins)
_THEMES = [
    ("EE2 compliance / environment variable rename",
     ["ee2", "rename", "homeglobal", "homegfs", "homeverif", "varglobal",
      "vargfs", "net-specific", "global naming", "nco", "compliance"]),
    ("submodule / dependency update",
     ["submodule", "ufs_utils", "ufs-utils", "hash", "gsi hash",
      "gdas", "jedi", "spack", "dependency"]),
    ("wiki / automation tooling",
     ["wiki", "automation", "summary", "schedule", "cron", "monthly",
      "weekly", "daily", "workflow_dispatch"]),
    ("CI / testing infrastructure",
     ["test", "ci ", "cmake", "build", "compile", "unit test",
      "consistency", "check"]),
    ("documentation / repository management",
     ["doc", "readme", "codeowner", "code owner", "copilot", "mcp",
      "guidance", "instruction"]),
    ("bug fix",
     ["fix", "bug", "error", "hotfix", "patch", "revert"]),
]

def _detect_theme(text: str) -> str:
    t = text.lower()
    for label, kws in _THEMES:
        if any(k in t for k in kws):
            return label
    return "general workflow / feature development"


# ── Helpers ───────────────────────────────────────────────────────────────────
def gh_get(url, params=None):
    results, p = [], {"per_page": 100, **(params or {})}
    while url:
        r = requests.get(url, headers=HEADERS, params=p)
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

def pr_short_body(pr_item) -> str:
    """Return first meaningful sentence of a PR body, or empty string."""
    body = (pr_item.get("body") or "").strip()
    # Strip markdown headers / checkboxes
    lines = [l.strip() for l in body.splitlines()
             if l.strip() and not l.strip().startswith(("#", "-", "[", ">"))
             and len(l.strip()) > 20]
    return lines[0][:200] if lines else ""


# ── Data Collection ───────────────────────────────────────────────────────────
def discover_repos():
    url   = f"https://api.github.com/users/{GITHUB_ACTOR}/repos"
    repos = gh_get(url, {"type": "all", "sort": "updated"})
    return [f"{r['owner']['login']}/{r['name']}"
            for r in repos if not r.get("archived", False)]

def collect_commits(repos):
    commits_by_repo = defaultdict(list)
    for repo in repos:
        try:
            items = gh_get(
                f"https://api.github.com/repos/{repo}/commits",
                {"since": DAY_START.isoformat(), "until": DAY_END.isoformat(),
                 "author": GITHUB_ACTOR},
            )
            for c in items:
                dt = parse_iso(c["commit"]["author"]["date"])
                if dt and DAY_START <= dt <= DAY_END:
                    commits_by_repo[repo].append({
                        "sha":     c["sha"][:7],
                        "message": c["commit"]["message"].split("\n")[0],
                        "url":     c["html_url"],
                    })
        except Exception as e:
            print(f"Warning: {repo}: {e}", file=sys.stderr)
    return commits_by_repo

def collect_prs():
    date_str = SUMMARY_DATE.isoformat()
    items    = gh_get(
        "https://api.github.com/search/issues",
        {"q": f"author:{GITHUB_ACTOR} is:pr is:merged merged:{date_str}"},
    )
    prs_by_repo = defaultdict(list)
    for pr in items:
        repo = pr.get("repository_url", "").replace(
            "https://api.github.com/repos/", "")
        if repo:
            prs_by_repo[repo].append({
                "number": pr["number"],
                "title":  pr["title"],
                "body":   pr_short_body(pr),
                "url":    pr["html_url"],
            })
    return prs_by_repo

def collect_open_prs():
    """PRs opened today (not yet merged)."""
    date_str = SUMMARY_DATE.isoformat()
    items    = gh_get(
        "https://api.github.com/search/issues",
        {"q": f"author:{GITHUB_ACTOR} is:pr is:open created:{date_str}"},
    )
    prs_by_repo = defaultdict(list)
    for pr in items:
        repo = pr.get("repository_url", "").replace(
            "https://api.github.com/repos/", "")
        if repo:
            prs_by_repo[repo].append({
                "number": pr["number"],
                "title":  pr["title"],
                "body":   pr_short_body(pr),
                "url":    pr["html_url"],
            })
    return prs_by_repo

def collect_issues():
    date_str       = SUMMARY_DATE.isoformat()
    issues_by_repo = defaultdict(lambda: {"created": [], "closed": []})

    for state, key, q_suffix in [
        ("all", "created", f"created:{date_str}"),
        ("all", "closed",  f"closed:{date_str}"),
    ]:
        items = gh_get(
            "https://api.github.com/search/issues",
            {"q": f"author:{GITHUB_ACTOR} is:issue {q_suffix}"},
        )
        for issue in items:
            repo = issue.get("repository_url", "").replace(
                "https://api.github.com/repos/", "")
            if repo:
                issues_by_repo[repo][key].append({
                    "number": issue["number"],
                    "title":  issue["title"],
                    "url":    issue["html_url"],
                })
    return issues_by_repo


# ── Narrative generation ──────────────────────────────────────────────────────
def _repo_display(repo: str) -> str:
    """e.g. 'NOAA-EMC/GSI-Monitor' stays as-is; owner/repo for forks."""
    return repo

def build_bullets(merged_prs, open_prs, commits_by_repo, issues_by_repo):
    """
    Return a list of narrative bullet strings, one per logical activity cluster.
    """
    bullets = []
    covered_repos = set()   # repos whose commits are already described via a PR bullet

    # ── Merged PRs ──────────────────────────────────────────────────────────
    for repo in sorted(merged_prs):
        for pr in merged_prs[repo]:
            theme = _detect_theme(pr["title"] + " " + pr["body"])
            repo_short = repo.split("/")[-1]
            link  = f"[{_repo_display(repo)}#{pr['number']}]({pr['url']})"
            desc  = pr["body"] if pr["body"] else pr["title"]
            # Pick a verb phrase based on theme
            verb = {
                "EE2 compliance / environment variable rename":
                    f"completing the EE2 environment variable rename in {repo_short}",
                "submodule / dependency update":
                    f"updating a submodule / dependency in {repo_short}",
                "wiki / automation tooling":
                    f"improving wiki/automation tooling in {repo_short}",
                "CI / testing infrastructure":
                    f"advancing CI/testing in {repo_short}",
                "documentation / repository management":
                    f"updating documentation/repo management in {repo_short}",
                "bug fix":
                    f"fixing a bug in {repo_short}",
            }.get(theme, f"completing work in {repo_short}")
            bullet = f"Merged {link}, {verb}. {desc}".rstrip(". ") + "."
            bullets.append(bullet)
            covered_repos.add(repo)

    # ── Opened (not yet merged) PRs ─────────────────────────────────────────
    for repo in sorted(open_prs):
        for pr in open_prs[repo]:
            link = f"[{_repo_display(repo)}#{pr['number']}]({pr['url']})"
            desc = pr["body"] if pr["body"] else pr["title"]
            bullet = f"Opened {link} — {desc}".rstrip(". ") + "."
            bullets.append(bullet)
            covered_repos.add(repo)

    # ── Commits not already covered by a PR bullet ──────────────────────────
    for repo in sorted(commits_by_repo):
        c_list = commits_by_repo[repo]
        if not c_list:
            continue
        # Deduplicate: skip if all commits look like merge-into-fork (single
        # commit whose message matches an already-covered PR title)
        repo_short = repo.split("/")[-1]
        msgs   = [c["message"] for c in c_list]
        links  = ", ".join(
            f"[`{c['sha']}`]({c['url']})" for c in c_list[:5]
        )
        if len(c_list) > 5:
            links += f" (+{len(c_list)-5} more)"

        theme  = _detect_theme(" ".join(msgs))
        action = {
            "EE2 compliance / environment variable rename":
                f"continued EE2 environment variable rename work in {repo_short}",
            "submodule / dependency update":
                f"updated submodules / dependencies in {repo_short}",
            "wiki / automation tooling":
                f"improved wiki/automation tooling in {repo_short}",
            "CI / testing infrastructure":
                f"advanced CI/testing infrastructure in {repo_short}",
            "documentation / repository management":
                f"updated documentation in {repo_short}",
            "bug fix":
                f"fixed bugs in {repo_short}",
        }.get(theme, f"pushed {len(c_list)} commit{'s' if len(c_list)>1 else ''} to {repo_short}")

        # Build a short commit message summary
        unique_msgs = list(dict.fromkeys(msgs))[:3]
        msg_summary = "; ".join(f'"{m}"' for m in unique_msgs)
        if len(msgs) > 3:
            msg_summary += f" (+{len(msgs)-3} more)"

        bullet = (
            f"{'C' if repo not in covered_repos else 'Also c'}ommitted to "
            f"{_repo_display(repo)}: {action} — {msg_summary} ({links})."
        )
        bullets.append(bullet)

    # ── Issues ───────────────────────────────────────────────────────────────
    for repo in sorted(issues_by_repo):
        created = issues_by_repo[repo]["created"]
        closed  = issues_by_repo[repo]["closed"]
        if created:
            for i in created:
                link = f"[{repo.split('/')[-1]}#{i['number']}]({i['url']})"
                bullets.append(f"Opened issue {link}: {i['title']}.")
        if closed:
            for i in closed:
                link = f"[{repo.split('/')[-1]}#{i['number']}]({i['url']})"
                bullets.append(f"Closed issue {link}: {i['title']}.")

    if not bullets:
        bullets = ["No activity recorded."]

    return bullets


def build_context(merged_prs, open_prs, commits_by_repo) -> str:
    """One-sentence context paragraph identifying the day's overall theme."""
    all_text = " ".join(
        pr["title"] for prs in merged_prs.values() for pr in prs
    ) + " " + " ".join(
        pr["title"] for prs in open_prs.values() for pr in prs
    ) + " " + " ".join(
        c["message"] for cs in commits_by_repo.values() for c in cs
    )
    theme = _detect_theme(all_text)
    active_repos = sorted({
        r.split("/")[-1]
        for r in list(merged_prs) + list(open_prs) + list(commits_by_repo)
    })
    repo_str = ", ".join(active_repos) if active_repos else "various repositories"

    context_map = {
        "EE2 compliance / environment variable rename":
            f"Work continues on the EE2 compliance effort, migrating environment "
            f"variables from NET-specific naming to global standards across "
            f"{repo_str}.",
        "submodule / dependency update":
            f"Submodule and dependency updates in {repo_str} support ongoing "
            f"integration and release preparation.",
        "wiki / automation tooling":
            f"Improvements to wiki automation tooling in {repo_str} enhance "
            f"automated activity tracking and reporting.",
        "CI / testing infrastructure":
            f"CI and testing infrastructure changes in {repo_str} improve build "
            f"reliability and test coverage.",
        "documentation / repository management":
            f"Documentation and repository management updates in {repo_str}.",
        "bug fix":
            f"Bug fixes applied in {repo_str}.",
    }
    return context_map.get(
        theme,
        f"Development activity across {repo_str}.",
    )


# ── Output ────────────────────────────────────────────────────────────────────
def write_summary(bullets, context, merged_prs, open_prs,
                  commits_by_repo, issues_by_repo):
    out = []
    out.append(f"## {SUMMARY_DATE.strftime('%A, %B %d, %Y')}\n\n")

    for b in bullets:
        out.append(f"- {b}\n")

    # Details block
    has_details = (any(merged_prs.values()) or any(open_prs.values())
                   or any(commits_by_repo.values()))
    if has_details:
        out.append("\n<details>\n<summary>Details</summary>\n")

        if any(merged_prs.values()):
            out.append("\n### Pull Requests\n")
            for repo in sorted(merged_prs):
                for pr in merged_prs[repo]:
                    out.append(
                        f"- [#{pr['number']}]({pr['url']}): {pr['title']}"
                        f" — **merged**\n"
                    )

        if any(open_prs.values()):
            out.append("\n### Opened Pull Requests\n")
            for repo in sorted(open_prs):
                for pr in open_prs[repo]:
                    out.append(
                        f"- [{_repo_display(repo)}#{pr['number']}]({pr['url']})"
                        f": {pr['title']}\n"
                    )

        if any(commits_by_repo.values()):
            out.append("\n### Commits\n")
            for repo in sorted(commits_by_repo):
                if commits_by_repo[repo]:
                    out.append(f"\n**{_repo_display(repo)}**\n")
                    for c in commits_by_repo[repo][:10]:
                        out.append(
                            f"- [`{c['sha']}`]({c['url']}): {c['message']}\n"
                        )
                    if len(commits_by_repo[repo]) > 10:
                        out.append(
                            f"- _{len(commits_by_repo[repo])-10} more..._\n"
                        )

        # Issues summary
        total_created = sum(
            len(issues_by_repo[r]["created"]) for r in issues_by_repo)
        total_closed  = sum(
            len(issues_by_repo[r]["closed"])  for r in issues_by_repo)
        if total_created or total_closed:
            out.append("\n### Issues\n")
            for repo in sorted(issues_by_repo):
                for i in issues_by_repo[repo]["created"]:
                    out.append(
                        f"- Opened [{repo.split('/')[-1]}#{i['number']}]"
                        f"({i['url']}): {i['title']}\n"
                    )
                for i in issues_by_repo[repo]["closed"]:
                    out.append(
                        f"- Closed [{repo.split('/')[-1]}#{i['number']}]"
                        f"({i['url']}): {i['title']}\n"
                    )

        out.append(f"\n### Context\n{context}\n")
        out.append("\n</details>\n")

    out.append("\n---\n\n")

    with open("daily_summary_patch.md", "w") as f:
        f.writelines(out)

    print("✓ Summary written to daily_summary_patch.md")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(f"Tracking activity for {GITHUB_ACTOR} on {SUMMARY_DATE}...")

    repos           = discover_repos()
    commits_by_repo = collect_commits(repos)
    merged_prs      = collect_prs()
    open_prs        = collect_open_prs()
    issues_by_repo  = collect_issues()

    bullets = build_bullets(merged_prs, open_prs, commits_by_repo, issues_by_repo)
    context = build_context(merged_prs, open_prs, commits_by_repo)

    for b in bullets:
        print(f"  • {b}")

    write_summary(bullets, context, merged_prs, open_prs,
                  commits_by_repo, issues_by_repo)


if __name__ == "__main__":
    main()
