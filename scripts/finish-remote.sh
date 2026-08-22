#!/usr/bin/env bash
# Remaining CHP consolidation map steps that need live GitHub credentials.
# Run after: gh auth refresh -h github.com
set -euo pipefail

OWNER="${OWNER:-icohangar-ops}"

echo "== 1. PR #1 (package home) =="
gh pr view 1 --repo "$OWNER/consensus-hardening-protocol" --json state,mergeable,url \
  --jq '"\(.state) mergeable=\(.mergeable) \(.url)"' || true
echo "Merge when ready:"
echo "  gh pr merge 1 --repo $OWNER/consensus-hardening-protocol --merge"

echo
echo "== 2. Delete triplicate (keep governed-mcp-gateway) =="
for r in cfo-agent-mesh spend-mandate-plane; do
  if gh api "repos/$OWNER/$r" --jq .full_name >/dev/null 2>&1; then
    echo "  deleting $OWNER/$r"
    gh repo delete "$OWNER/$r" --yes
  else
    echo "  $OWNER/$r already gone / inaccessible"
  fi
done
if gh api "repos/$OWNER/governed-mcp-gateway" --jq .full_name >/dev/null 2>&1; then
  echo "  KEEP governed-mcp-gateway — still present"
else
  echo "  WARNING: governed-mcp-gateway missing — restore from backup if deleted by mistake"
fi

echo
echo "== 3. Push cubiczan-chp + chp-examples (if remotes not set) =="
echo "  cd ~/Desktop/cubiczan-chp && gh repo create $OWNER/cubiczan-chp --public --source=. --remote=origin --push"
echo "  cd ~/Desktop/chp-examples && gh repo create $OWNER/chp-examples --public --source=. --remote=origin --push"

echo
echo "== 4. Publish @cubiczan/chp =="
echo "  npm login   # must own @cubiczan scope"
echo "  cd ~/Desktop/cubiczan-chp && npm publish --access public"
