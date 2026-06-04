#!/bin/bash
# ============================================================
#  Chronicle — one-tap publisher to GitHub
#  Double-click this file. It signs you in to GitHub (once,
#  in your browser) and uploads your code. No coding needed.
# ============================================================

GH="$HOME/.chronicle-tools/bin/gh"

# Work from the folder this script lives in (your Chronicle project).
cd "$(cd "$(dirname "$0")" && pwd)" || exit 1

echo ""
echo "=================================================="
echo "   Publishing Chronicle to GitHub"
echo "=================================================="
echo ""

if [ ! -x "$GH" ]; then
  echo "Could not find the GitHub tool. Tell Claude and it will reinstall it."
  echo ""
  read -r -p "Press Enter to close."
  exit 1
fi

# --- Step 1: sign in to GitHub (only the first time) ---------
if ! "$GH" auth status >/dev/null 2>&1; then
  echo "STEP 1 of 2  —  Sign in to GitHub"
  echo "--------------------------------------------------"
  echo "A short code will appear below."
  echo "  1. Press Enter — your web browser will open."
  echo "  2. Paste/type the code shown here."
  echo "  3. Click the green 'Authorize' button."
  echo "(If you don't have a GitHub account yet, you can create"
  echo " one for free on that same page.)"
  echo ""
  "$GH" auth login --hostname github.com --git-protocol https --web || {
    echo ""
    echo "Sign-in didn't complete. Just run this again to retry."
    read -r -p "Press Enter to close."
    exit 1
  }
fi

WHO="$("$GH" api user --jq .login 2>/dev/null)"
echo ""
echo "OK — signed in to GitHub as: ${WHO:-unknown}"
echo ""

# --- Step 2: create the repo (if needed) and upload ----------
echo "STEP 2 of 2  —  Uploading your code…"
echo "--------------------------------------------------"
if git remote get-url origin >/dev/null 2>&1; then
  git push -u origin main || git push -u origin HEAD
else
  "$GH" repo create chronicle --private --source=. --remote=origin --push || {
    echo ""
    echo "Upload hit a snag. Tell Claude what the message above says."
    read -r -p "Press Enter to close."
    exit 1
  }
fi

URL="$("$GH" repo view --json url --jq .url 2>/dev/null)"
echo ""
echo "=================================================="
echo "   DONE — your code is now on GitHub:"
echo "   ${URL:-(open github.com to see your 'chronicle' repo)}"
echo "=================================================="
echo ""
echo "NEXT: turn it into a live website (free) on Render."
echo "Open DEPLOY.md, or just tell Claude: \"the code is on GitHub\"."
echo ""
read -r -p "Press Enter to close this window."
