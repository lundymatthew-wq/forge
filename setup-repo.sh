#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# FORGE — Repo Setup Script
# ═══════════════════════════════════════════════════════════════
# Run this once on your WSL2 machine to initialize the repo.
#
# Usage:
#   chmod +x setup-repo.sh
#   ./setup-repo.sh
#
# Prerequisites:
#   - git installed
#   - GitHub CLI (gh) installed, or manually add remote after
#   - Python 3.10+ with pyyaml (pip install pyyaml)
# ═══════════════════════════════════════════════════════════════

set -e

REPO_NAME="forge"
GITHUB_ORG="brave-alpaca"  # Change if different
DESCRIPTION="Factory for Orchestrated Runtime Generation of Engines — the machine that builds machines."

echo ""
echo "  ⬡ FORGE — Repo Setup"
echo "  ═══════════════════════════════════════"
echo ""

# ── Step 1: Verify we're in the right place ──
if [ ! -f "forge.py" ]; then
    echo "  ✗ forge.py not found. Run this from the forge/ directory."
    exit 1
fi
echo "  ✓ forge.py found"

# ── Step 2: Check Python + pyyaml ──
if ! python3 -c "import yaml" 2>/dev/null; then
    echo "  ⚠ pyyaml not found. Installing..."
    pip install pyyaml --break-system-packages -q
fi
echo "  ✓ Python + pyyaml ready"

# ── Step 3: Verify FORGE runs ──
echo "  ⬡ Verifying FORGE..."
python3 forge.py validate specs/coop-briefing.yaml
echo "  ✓ FORGE validated"

# ── Step 4: Git init ──
if [ -d ".git" ]; then
    echo "  ⚠ Git repo already exists. Skipping init."
else
    git init
    echo "  ✓ Git initialized"
fi

# ── Step 5: Configure git (skip if already set) ──
if [ -z "$(git config user.name)" ]; then
    git config user.name "Matt Lundy"
    git config user.email "lundymatthew@gmail.com"
    echo "  ✓ Git user configured"
else
    echo "  ✓ Git user already configured"
fi

# ── Step 6: Initial commit ──
git add -A
git commit -m "⬡ FORGE v1.0.0 — Initial commit

The machine that builds machines.

- forge.py: Core engine (Directive / Orchestration / Execution generators)
- specs/coop-briefing.yaml: First app spec (COOP Morning Briefing)
- templates/: Reusable HTML templates
- docs/: Architecture documentation

Brave Alpaca · COOP · Life Cockpit"

echo "  ✓ Initial commit created"

# ── Step 7: Create GitHub repo (if gh CLI available) ──
if command -v gh &> /dev/null; then
    echo ""
    echo "  ⬡ GitHub CLI detected."
    read -p "  Create GitHub repo ${GITHUB_ORG}/${REPO_NAME}? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Check if repo exists
        if gh repo view "${GITHUB_ORG}/${REPO_NAME}" &>/dev/null 2>&1; then
            echo "  ⚠ Repo already exists. Adding as remote..."
            git remote add origin "git@github.com:${GITHUB_ORG}/${REPO_NAME}.git" 2>/dev/null || true
        else
            gh repo create "${GITHUB_ORG}/${REPO_NAME}" \
                --private \
                --description "${DESCRIPTION}" \
                --source . \
                --push
            echo "  ✓ GitHub repo created and pushed"
        fi
    fi
else
    echo ""
    echo "  ⚠ GitHub CLI (gh) not found."
    echo "    To push manually:"
    echo ""
    echo "    # Create repo on GitHub first, then:"
    echo "    git remote add origin git@github.com:${GITHUB_ORG}/${REPO_NAME}.git"
    echo "    git branch -M main"
    echo "    git push -u origin main"
    echo ""
fi

# ── Step 8: Run first build as proof of life ──
echo ""
echo "  ⬡ Running first build..."
echo ""
python3 forge.py build specs/coop-briefing.yaml

echo ""
echo "  ═══════════════════════════════════════"
echo "  ⬡ FORGE is live."
echo ""
echo "  Next steps:"
echo "    1. Drop this folder at ~/forge/ on your WSL2 machine"
echo "    2. Run: chmod +x setup-repo.sh && ./setup-repo.sh"
echo "    3. Build apps: python forge.py build specs/your-app.yaml"
echo "    4. Improve the machine: iterate on forge.py"
echo "  ═══════════════════════════════════════"
echo ""
