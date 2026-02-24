#!/bin/bash
# Quick Start Script for Wiki Automation Setup

set -e

echo "==================================================================="
echo "Wiki Automation - Quick Setup"
echo "==================================================================="
echo ""
echo "Current directory: $(pwd)"
echo ""

# Check if we're in the right directory
if [ ! -f "generate_daily_summary.py" ]; then
    echo "ERROR: Not in wiki-automation directory!"
    exit 1
fi

# Check if remote already exists
if git remote get-url origin &>/dev/null; then
    echo "✅ Git remote 'origin' already configured:"
    git remote get-url origin
else
    echo "⚠️  Git remote 'origin' not configured yet."
    echo ""
    echo "Please run:"
    echo "  git remote add origin https://github.com/AntonMFernando-NOAA/wiki.git"
    echo ""
    read -p "Press Enter after adding remote, or Ctrl+C to exit..."
fi

echo ""
echo "==================================================================="
echo "Step 1: Rename branch to 'main'"
echo "==================================================================="
git branch -M main
echo "✅ Branch renamed to 'main'"

echo ""
echo "==================================================================="
echo "Step 2: Review what will be pushed"
echo "==================================================================="
git log --oneline --no-decorate | head -5
echo ""
git status

echo ""
echo "==================================================================="
echo "Step 3: Push to GitHub"
echo "==================================================================="
echo "Ready to push to GitHub?"
echo ""
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo 'NOT CONFIGURED')
echo "This will push to: $REMOTE_URL"
echo ""
read -p "Continue? Press Enter or Ctrl+C to abort..."

git push -u origin main

echo ""
echo "==================================================================="
echo "✅ SUCCESS! Repository pushed to GitHub"
echo "==================================================================="
echo ""
echo "🔧 Next steps (complete these on GitHub):"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. INITIALIZE WIKI (REQUIRED!)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Go to: https://github.com/AntonMFernando-NOAA/wiki/wiki"
echo "   Click: 'Create the first page'"
echo "   Title: Home"
echo "   Content:"
echo "     # Wiki Automation"
echo "     "
echo "     Daily activity summaries for AntonMFernando-NOAA repos."
echo "     "
echo "     See [[Daily Updates]] for automated summaries."
echo "   "
echo "   Click: 'Save Page'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. CREATE PERSONAL ACCESS TOKEN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   https://github.com/settings/tokens/new"
echo "   Scopes needed: ✅ repo, ✅ read:org"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. ADD SECRET TO REPOSITORY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   https://github.com/AntonMFernando-NOAA/wiki/settings/secrets/actions"
echo "   Name: WIKI_PAT"
echo "   Value: <paste your token>"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. ENABLE GITHUB ACTIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   https://github.com/AntonMFernando-NOAA/wiki/settings/actions"
echo "   ✅ Allow all actions"
echo "   ✅ Read and write permissions"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. TEST THE WORKFLOW"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   https://github.com/AntonMFernando-NOAA/wiki/actions"
echo "   Click: 'Daily Wiki Update' → 'Run workflow'"
echo "   Leave date blank → 'Run workflow'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📖 DOCUMENTATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Detailed instructions: cat SETUP_INSTRUCTIONS.md"
echo "   Wiki migration tool:   ./MIGRATE_WIKI.sh"
echo "   Full documentation:    cat README.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 WIKI LOCATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   https://github.com/AntonMFernando-NOAA/wiki/wiki"
echo "   (Daily updates will appear at: .../wiki/Daily-Updates)"
echo "==================================================================="
