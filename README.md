# Wiki Automation

Automated daily updates tracking all AntonMFernando-NOAA repositories.

## Overview

This repository contains GitHub Actions automation that:
- **Auto-discovers** all repositories under `AntonMFernando-NOAA`
- **Tracks daily activity**: commits, PRs, and issues
- **Updates THIS repository's wiki** with daily summaries at 06:00 UTC (weekdays only)

📖 **Wiki Location**: https://github.com/AntonMFernando-NOAA/wiki/wiki

## Features

- ✅ Automatic repository discovery (no manual configuration)
- ✅ Narrative summaries instead of raw commit lists
- ✅ Expandable details for full activity breakdown
- ✅ Weekday-only updates (Mon-Fri)
- ✅ Manual trigger support for custom dates
- ✅ Self-contained - wiki lives with the automation code

## Quick Start

### 1. Create GitHub Repository

```bash
# Create new repo at: https://github.com/new
# Repository name: wiki
# Description: Automated wiki updates for AntonMFernando-NOAA repositories
# Visibility: Public (or Private - wiki works either way)
# ✅ Check "Add a wiki" when creating
```

### 2. Push This Repository

```bash
cd /scratch3/NCEPDEV/global/Anton.Fernando/wiki-automation
./QUICK_START.sh
```

### 3. Configure GitHub Secrets

Go to: https://github.com/AntonMFernando-NOAA/wiki/settings/secrets/actions

Create secret `WIKI_PAT`:
- Generate token at: https://github.com/settings/tokens/new
- Scopes needed: `repo`, `read:org`

### 4. Enable GitHub Actions

Go to: https://github.com/AntonMFernando-NOAA/wiki/settings/actions
- ✅ Allow all actions
- ✅ Read and write permissions

### 5. Test It

Go to: https://github.com/AntonMFernando-NOAA/wiki/actions
- Click "Daily Wiki Update" → "Run workflow"
- Leave date blank
- Check wiki after run completes

## How It Works

### Scheduled Execution
- Runs Monday-Friday at 06:00 UTC
- Auto-discovers all `AntonMFernando-NOAA` repositories
- Collects activity from previous day
- Updates **this repository's wiki** with narrative summary

### Manual Execution
```bash
# Via GitHub UI: Actions → Daily Wiki Update → Run workflow
# Specify custom date or leave blank for yesterday
```

### Output Format

**Wiki page**: https://github.com/AntonMFernando-NOAA/wiki/wiki/Daily-Updates

Each entry includes:
- **Date header**: Tuesday, February 24, 2026
- **Narrative summary**: "3 PRs merged: global-workflow#123, GDASApp#456..."
- **Expandable details**: Full breakdown by repository

### Tracked Repositories

Auto-discovers all repositories including:
- global-workflow
- GDASApp  
- UFS_UTILS
- GSI
- Any other public/private repos under your account

## Repository Structure

```
wiki-automation/
├── .github/workflows/
│   └── daily-wiki-update.yml    # GitHub Actions workflow
├── generate_daily_summary.py    # Auto-discovery and summary generation
├── README.md                     # This file
├── SETUP_INSTRUCTIONS.md         # Detailed setup guide
├── QUICK_START.sh                # Automated setup script
└── MIGRATE_WIKI.sh               # Tool to migrate from other wikis
```

## Migrating Existing Wiki Content

If you have content in global-workflow wiki that you want to move here:

```bash
./MIGRATE_WIKI.sh
```

This will:
1. Clone the global-workflow wiki
2. Copy relevant pages to wiki-automation wiki
3. Update links and references
4. Push to wiki-automation wiki

## Customization

### Change Schedule
Edit `.github/workflows/daily-wiki-update.yml`:
```yaml
schedule:
  - cron: '0 12 * * *'  # Every day at noon UTC
```

### Track Different Organization
Edit `.github/workflows/daily-wiki-update.yml`:
```yaml
env:
  GITHUB_ACTOR: 'different-org-name'
```

### Update Wiki Manually
```python
# Set environment variables
export GH_TOKEN="your-github-token"
export GITHUB_ACTOR="AntonMFernando-NOAA"
export SUMMARY_DATE="2026-02-23"

# Run script
python generate_daily_summary.py
```

## Troubleshooting

### Workflow Not Running
- Verify default branch is `main`
- Check GitHub Actions is enabled
- Ensure `WIKI_PAT` secret is configured
- Verify wiki is enabled on the repository

### Permission Errors
- PAT needs `repo` scope for private repos
- PAT needs `read:org` for organization repos
- PAT needs wiki access (automatic with `repo` scope)

### No Activity Detected
- Check PAT has access to repositories
- Verify repositories aren't archived
- Run manually with yesterday's date to test

### Wiki Not Created
- Ensure "Wiki" is enabled in repository settings
- The first run will create the wiki structure
- Check Actions logs for detailed errors

## Advantages Over global-workflow Wiki

✅ **Self-contained**: Wiki lives with automation code  
✅ **Clean separation**: Doesn't clutter global-workflow  
✅ **Independent**: Can track any combination of repositories  
✅ **Flexible**: Easy to customize without affecting main repos  
✅ **Portable**: Can be forked/duplicated for other purposes  

## Maintenance

This automation is self-maintaining:
- No repository list updates needed
- Automatically includes new repositories
- Skips archived repositories
- Wiki format auto-adjusts

## Documentation

- **Quick setup**: `./QUICK_START.sh`
- **Detailed guide**: `SETUP_INSTRUCTIONS.md`
- **Migrate content**: `./MIGRATE_WIKI.sh`

## License

Personal automation utility. Use freely.
