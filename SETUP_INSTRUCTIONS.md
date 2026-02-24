# Setup Instructions for Wiki Automation

## ✅ Completed (Local Setup)

You have a complete wiki automation repository at:
`/scratch3/NCEPDEV/global/Anton.Fernando/wiki-automation`

**Repository contents:**
- `generate_daily_summary.py` - Auto-discovers and summarizes activity across all your repos
- `.github/workflows/daily-wiki-update.yml` - GitHub Actions workflow (runs weekdays at 06:00 UTC)
- `README.md` - Full documentation
- `MIGRATE_WIKI.sh` - Tool to migrate content from global-workflow wiki
- `.gitignore` - Proper exclusions

---

## 🔧 Next Steps (GitHub Setup)

### Step 1: Create GitHub Repository

1. Go to: https://github.com/new
2. Fill in:
   - **Repository name**: `wiki`
   - **Description**: `Automated daily wiki updates for AntonMFernando-NOAA repositories`
   - **Visibility**: Public (recommended) or Private
   - ✅ **Check "Add a wiki"** (important!)
   - **Do NOT** initialize with README, .gitignore, or license
3. Click **Create repository**

### Step 2: Push Local Repository

```bash
cd /scratch3/NCEPDEV/global/Anton.Fernando/wiki-automation
./QUICK_START.sh
```

Or manually:
```bash
git branch -M main
git remote add origin https://github.com/AntonMFernando-NOAA/wiki-automation.git
git push -u origin main
```

### Step 3: Initialize Wiki

**IMPORTANT**: GitHub wikis must have at least one page before cloning.

1. Go to: https://github.com/AntonMFernando-NOAA/wiki-automation/wiki
2. Click **Create the first page**
3. Title: `Home`
4. Content:
   ```markdown
   # Wiki Automation
   
   Daily activity summaries for all AntonMFernando-NOAA repositories.
   
   See [[Daily Updates]] for automated summaries.
   ```
5. Click **Save Page**

### Step 4: Create Personal Access Token (PAT)

1. Go to: https://github.com/settings/tokens/new
2. Fill in:
   - **Note**: `wiki-automation-bot`
   - **Expiration**: 90 days (or No expiration)
   - **Select scopes**:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `read:org` (Read org and team membership)
3. Click **Generate token**
4. **COPY THE TOKEN** - you won't see it again!

### Step 5: Configure Repository Secret

1. Go to: https://github.com/AntonMFernando-NOAA/wiki/settings/secrets/actions
2. Click **New repository secret**
3. Fill in:
   - **Name**: `WIKI_PAT`
   - **Value**: Paste the token from Step 4
4. Click **Add secret**

### Step 6: Enable GitHub Actions

1. Go to: https://github.com/AntonMFernando-NOAA/wiki/settings/actions
2. Under **Actions permissions**:
   - Select **Allow all actions and reusable workflows**
3. Under **Workflow permissions**:
   - Select **Read and write permissions**
   - ✅ Check **Allow GitHub Actions to create and approve pull requests**
4. Click **Save**

### Step 7: Test the Workflow

1. Go to: https://github.com/AntonMFernando-NOAA/wiki/actions
2. Click on **Daily Wiki Update** workflow
3. Click **Run workflow** button
4. Leave date blank (defaults to yesterday)
5. Click **Run workflow**

**Expected results:**
- Workflow should complete successfully (green checkmark)
- Wiki page updated at: https://github.com/AntonMFernando-NOAA/wiki-automation/wiki/Daily-Updates
- First entry should show yesterday's activity across all your repos

---

## 🔄 Migrating from global-workflow Wiki (Optional)

If you have existing content in global-workflow wiki that you want to move:

```bash
cd /scratch3/NCEPDEV/global/Anton.Fernando/wiki-automation
export WIKI_PAT='your-github-token-here'
./MIGRATE_WIKI.sh
```

This will:
1. Clone both wikis
2. Copy pages (excluding Daily-Updates which will be auto-generated)
3. Update wiki links
4. Push to wiki-automation wiki

After migration, you can disable the global-workflow wiki:
1. Go to: https://github.com/AntonMFernando-NOAA/global-workflow/settings
2. Under "Features", uncheck "Wikis"

---

## 🎯 What This Does

**Automatically tracks activity across ALL your repositories:**
- AntonMFernando-NOAA/global-workflow
- AntonMFernando-NOAA/GDASApp
- AntonMFernando-NOAA/UFS_UTILS
- Any other current or future repositories

**Creates daily summaries with:**
- Merged PRs with links
- Commit counts by repository
- Opened/closed issues
- Expandable details section

**Updates THIS repository's wiki at:**
- https://github.com/AntonMFernando-NOAA/wiki-automation/wiki/Daily-Updates
- Runs Monday-Friday at 06:00 UTC
- Newest entries appear at the top

---

## 📋 Verification Checklist

After completing all steps:

- [ ] GitHub repository created at: https://github.com/AntonMFernando-NOAA/wiki
- [ ] Wiki enabled and Home page created
- [ ] Local repository pushed successfully
- [ ] PAT created with `repo` and `read:org` scopes
- [ ] Secret `WIKI_PAT` configured in repository settings
- [ ] GitHub Actions enabled with read/write permissions
- [ ] Workflow test run completed successfully
- [ ] Wiki page exists at: https://github.com/AntonMFernando-NOAA/wiki-automation/wiki/Daily-Updates
- [ ] (Optional) Content migrated from global-workflow wiki
- [ ] (Optional) global-workflow wiki disabled

---

## 🔍 Troubleshooting

**Workflow fails with "GH_TOKEN is not set"**
→ Secret name must be exactly `WIKI_PAT` (case-sensitive)

**Workflow fails with "403 Forbidden"**
→ PAT needs `repo` scope and `read:org` scope

**Workflow fails with "fatal: could not access wiki"**
→ Wiki must be enabled in repository settings
→ Wiki must have at least one page (create Home page first)

**No repositories discovered**
→ Check PAT has access to AntonMFernando-NOAA organization/account

**Wiki URL returns 404**
→ Ensure wiki is enabled: Settings → Features → Wikis (checked)
→ Create at least one wiki page manually

**Manual workflow trigger not available**
→ Ensure GitHub Actions is enabled in repository settings
→ Check workflow file is in `.github/workflows/` directory

---

## 🎓 Advanced Usage

### Run for specific date
```bash
# Via GitHub Actions UI
Actions → Daily Wiki Update → Run workflow
Enter date: 2026-02-23
```

### Track different organization
Edit `.github/workflows/daily-wiki-update.yml`:
```yaml
env:
  GITHUB_ACTOR: 'different-org-name'
```

### Change schedule
Edit `.github/workflows/daily-wiki-update.yml`:
```yaml
schedule:
  - cron: '0 12 * * *'  # Every day at noon UTC
```

### Run locally
```bash
export GH_TOKEN='your-token'
export GITHUB_ACTOR='AntonMFernando-NOAA'
export SUMMARY_DATE='2026-02-23'
python generate_daily_summary.py
```

---

## 📞 Need Help?

1. Check workflow logs: https://github.com/AntonMFernando-NOAA/wiki/actions
2. Review README.md for full documentation
3. Test manually with yesterday's date first
4. Verify wiki is enabled and initialized

## ✅ Advantages of This Approach

✅ **Self-contained**: Wiki lives with automation code  
✅ **Clean**: Doesn't clutter global-workflow repository  
✅ **Focused**: Single-purpose repository for tracking  
✅ **Flexible**: Easy to customize without affecting main repos  
✅ **Portable**: Can be duplicated for other organizations  

Good luck! 🚀
