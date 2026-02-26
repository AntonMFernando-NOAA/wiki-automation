#!/usr/bin/env python3
"""
Generate a daily activity summary across all AntonMFernando-NOAA repositories.
Only activity by GITHUB_ACTOR is tracked (commits filtered by author, PRs/issues
found via GitHub Search API so cross-org activity is captured correctly).

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

# ── Config ───────────────────────────────────────────────────────────────────
TOKEN = os.environ.get("GH_TOKEN", "")
if not TOKEN:
    sys.exit("Error: GH_TOKEN is not set.")

GITHUB_ACTOR = os.environ.get("GITHUB_ACTOR", "AntonMFernando-NOAA")
SUMMARY_DATE_STR = os.environ.get("SUMMARY_DATE", "").strip()
SUMMARY_DATE = date.fromisoformat(SUMMARY_DATE_STR) if SUMMARY_DATE_STR else date.today() - timedelta(days=1)
DAY_START = datetime(SUMMARY_DATE.year, SUMMARY_DATE.month, SUMMARY_DATE.day, 0, 0, 0, tzinfo=timezone.utc)
DAY_END   = datetime(SUMMARY_DATE.year, SUMMARY_DATE.month, SUMMARY_DATE.day, 23, 59, 59, tzinfo=timezone.utc)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def gh_get(url, params=None):
    """Paginated GitHub API GET request."""
    results, p = [], {"per_page": 100, **(params or {})}
    while url:
        r = requests.get(url, headers=HEADERS, params=p)
        r.raise_for_status()
        data = r.json()
        # Search API wraps results in {"items": [...]}
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

def discover_repos():
    """Auto-discover all non-archived repositories owned by GITHUB_ACTOR."""
    url = f"https://api.github.com/users/{GITHUB_ACTOR}/repos"
    repos = gh_get(url, {"type": "all", "sort": "updated"})
    return [f"{r['owner']['login']}/{r['name']}" for r in repos if not r.get('archived', False)]

def parse_iso(ts_str):
    """Parse ISO8601 timestamp to datetime."""
    if not ts_str:
        return None
    ts_str = ts_str.replace("Z", "+00:00")
    return datetime.fromisoformat(ts_str)

# ── Data Collection ───────────────────────────────────────────────────────────
def collect_commits(repos):
    """Collect commits authored by GITHUB_ACTOR from all repos within the date range."""
    commits_by_repo = defaultdict(list)

    for repo in repos:
        try:
            url = f"https://api.github.com/repos/{repo}/commits"
            # Pass author= so the API pre-filters; we still verify dates locally.
            commits = gh_get(url, {
                "since":  DAY_START.isoformat(),
                "until":  DAY_END.isoformat(),
                "author": GITHUB_ACTOR,
            })

            for c in commits:
                commit_date = parse_iso(c['commit']['author']['date'])
                if commit_date and DAY_START <= commit_date <= DAY_END:
                    commits_by_repo[repo].append({
                        'sha':     c['sha'][:7],
                        'message': c['commit']['message'].split('\n')[0],
                        'author':  c['commit']['author']['name'],
                        'url':     c['html_url'],
                    })
        except Exception as e:
            print(f"Warning: Could not fetch commits from {repo}: {e}", file=sys.stderr)

    return commits_by_repo

def collect_prs():
    """
    Collect PRs authored by GITHUB_ACTOR that were merged on SUMMARY_DATE.
    Uses the Search API so cross-org PRs (e.g. in NOAA-EMC repos) are included.
    """
    date_str = SUMMARY_DATE.isoformat()
    query = (
        f"author:{GITHUB_ACTOR} is:pr is:merged merged:{date_str}"
    )
    items = gh_get("https://api.github.com/search/issues", {"q": query})

    prs_by_repo = defaultdict(list)
    for pr in items:
        # repo_url looks like https://api.github.com/repos/owner/repo
        repo = pr.get("repository_url", "").replace("https://api.github.com/repos/", "")
        if repo:
            prs_by_repo[repo].append({
                'number': pr['number'],
                'title':  pr['title'],
                'author': pr['user']['login'],
                'url':    pr['html_url'],
            })

    return prs_by_repo

def collect_issues():
    """
    Collect issues opened OR closed by GITHUB_ACTOR on SUMMARY_DATE.
    Uses the Search API so activity in any org is captured.
    """
    date_str = SUMMARY_DATE.isoformat()
    issues_by_repo = defaultdict(lambda: {'created': [], 'closed': []})

    # Opened
    opened_items = gh_get(
        "https://api.github.com/search/issues",
        {"q": f"author:{GITHUB_ACTOR} is:issue created:{date_str}"},
    )
    for issue in opened_items:
        repo = issue.get("repository_url", "").replace("https://api.github.com/repos/", "")
        if repo:
            issues_by_repo[repo]['created'].append({
                'number': issue['number'],
                'title':  issue['title'],
                'url':    issue['html_url'],
            })

    # Closed
    closed_items = gh_get(
        "https://api.github.com/search/issues",
        {"q": f"author:{GITHUB_ACTOR} is:issue closed:{date_str}"},
    )
    for issue in closed_items:
        repo = issue.get("repository_url", "").replace("https://api.github.com/repos/", "")
        if repo:
            issues_by_repo[repo]['closed'].append({
                'number': issue['number'],
                'title':  issue['title'],
                'url':    issue['html_url'],
            })

    return issues_by_repo

# ── Summary Generation ────────────────────────────────────────────────────────
def generate_narrative(commits_by_repo, prs_by_repo, issues_by_repo):
    """Generate a narrative summary of the day's activity."""
    narrative_parts = []

    # PRs
    pr_repos = [r for r in prs_by_repo if prs_by_repo[r]]
    if pr_repos:
        pr_count = sum(len(prs_by_repo[r]) for r in pr_repos)
        pr_list = []
        for repo in sorted(pr_repos):
            for pr in prs_by_repo[repo]:
                repo_short = repo.split('/')[-1]
                pr_list.append(f"[{repo_short}#{pr['number']}]({pr['url']})")
        narrative_parts.append(f"**{pr_count} PR{'s' if pr_count > 1 else ''} merged**: {', '.join(pr_list)}")

    # Commits
    commit_repos = [r for r in commits_by_repo if commits_by_repo[r]]
    if commit_repos:
        commit_count = sum(len(commits_by_repo[r]) for r in commit_repos)
        repo_list = [r.split('/')[-1] for r in sorted(commit_repos)]
        narrative_parts.append(f"**{commit_count} commit{'s' if commit_count > 1 else ''} pushed** across {', '.join(repo_list)}")

    # Issues
    issues_created = sum(len(issues_by_repo[r]['created']) for r in issues_by_repo)
    issues_closed  = sum(len(issues_by_repo[r]['closed'])  for r in issues_by_repo)

    if issues_created:
        narrative_parts.append(f"**{issues_created} issue{'s' if issues_created > 1 else ''} opened**")
    if issues_closed:
        narrative_parts.append(f"**{issues_closed} issue{'s' if issues_closed > 1 else ''} closed**")

    if not narrative_parts:
        return "No activity recorded."

    return ". ".join(narrative_parts) + "."

def write_summary(narrative, commits_by_repo, prs_by_repo, issues_by_repo):
    """Write the summary to daily_summary_patch.md."""
    output = []
    output.append(f"## {SUMMARY_DATE.strftime('%A, %B %d, %Y')}\n")
    output.append(f"{narrative}\n")

    if any(commits_by_repo.values()) or any(prs_by_repo.values()):
        output.append("\n<details>\n<summary>Details</summary>\n")

        if any(prs_by_repo.values()):
            output.append("\n### Pull Requests\n")
            for repo in sorted(prs_by_repo):
                if prs_by_repo[repo]:
                    output.append(f"\n**{repo}**\n")
                    for pr in prs_by_repo[repo]:
                        output.append(f"- [#{pr['number']}]({pr['url']}): {pr['title']}\n")

        if any(commits_by_repo.values()):
            output.append("\n### Commits\n")
            for repo in sorted(commits_by_repo):
                if commits_by_repo[repo]:
                    output.append(f"\n**{repo}**\n")
                    for commit in commits_by_repo[repo][:10]:
                        output.append(f"- [`{commit['sha']}`]({commit['url']}): {commit['message']}\n")
                    if len(commits_by_repo[repo]) > 10:
                        output.append(f"- _{len(commits_by_repo[repo]) - 10} more commits..._\n")

        output.append("\n</details>\n")

    output.append("\n---\n\n")

    with open("daily_summary_patch.md", "w") as f:
        f.write("".join(output))

    print("✓ Summary written to daily_summary_patch.md")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print(f"Tracking activity for {GITHUB_ACTOR} on {SUMMARY_DATE}...")

    repos = discover_repos()
    print(f"Found {len(repos)} repositories.")

    commits_by_repo  = collect_commits(repos)
    prs_by_repo      = collect_prs()
    issues_by_repo   = collect_issues()

    narrative = generate_narrative(commits_by_repo, prs_by_repo, issues_by_repo)
    print(f"Summary: {narrative}")

    write_summary(narrative, commits_by_repo, prs_by_repo, issues_by_repo)

if __name__ == "__main__":
    main()
