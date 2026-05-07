#!/usr/bin/env bash
# ============================================================
# forge-ignite.sh — FORGE-RALPH Ignition Script
#
# Renders the four required artifacts (PRD.md, CLAUDE.md,
# verifier.md, stop-conditions.md) into a target repo, runs
# the Pre-Ignition Acceptance Checklist, and (if env is set)
# transitions the Notion Registry row to Ignited.
#
# Spec: docs/forge-ralph-integration-spec.md (v1.0)
# ============================================================

set -euo pipefail

# ---------- Defaults & paths ----------
FORGE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="${FORGE_DIR}/templates/forge-ralph"
DEFAULTS_FILE="${FORGE_DIR}/forge-defaults.yaml"

ITERATION_CAP_DEFAULT=5
COST_CAP_DEFAULT=25
FORGE_VERSION="1.0"

# ---------- Helpers ----------
err() { printf '\033[1;31m[ERR]\033[0m %s\n' "$*" >&2; }
ok()  { printf '\033[1;32m[OK]\033[0m  %s\n' "$*"; }
inf() { printf '\033[1;34m[..]\033[0m  %s\n' "$*"; }
warn(){ printf '\033[1;33m[!!]\033[0m  %s\n' "$*"; }

usage() {
  cat <<'EOF'
Usage: forge-ignite.sh --name <project_name> --spec-id <FORGE-YYYY-NNN> --target <path> [options]

Required:
  --name           Project name (e.g. "Rhed")
  --spec-id        Spec ID, format FORGE-YYYY-NNN (e.g. "FORGE-2026-002")
  --target         Path to the target repo where artifacts get written

Optional:
  --repo-url       Repo URL (e.g. https://github.com/matt/rhed)
  --registry-row   Notion Registry row URL (will be written into artifacts)
  --author         Author name for changelog (default: $USER)
  --iteration-cap  Override iteration cap (default 5; or read from forge-defaults.yaml)
  --cost-cap       Override cost cap USD (default 25; or read from forge-defaults.yaml)
  --check-only     Run Pre-Ignition Checklist on existing artifacts; don't render
  --no-notion      Skip Notion Registry writeback even if env vars are set
  --force          Overwrite existing artifacts (default: refuse if any exist)
  -h, --help       Show this help

Notion writeback (optional, both must be set to enable):
  NOTION_FORGE_TOKEN   Notion integration token, scoped to FORGE Registry DB
  REGISTRY_PAGE_ID     Notion page ID of the Registry row to update

Exit codes:
  0   ignition successful
  1   pre-ignition checklist failed
  2   bad arguments / missing templates
  3   notion writeback failed
EOF
}

# ---------- Parse args ----------
PROJECT_NAME=""
SPEC_ID=""
TARGET=""
REPO_URL=""
REGISTRY_ROW_URL=""
AUTHOR="${USER:-FORGE}"
ITERATION_CAP=""
COST_CAP=""
CHECK_ONLY=0
NO_NOTION=0
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)          PROJECT_NAME="$2"; shift 2 ;;
    --spec-id)       SPEC_ID="$2"; shift 2 ;;
    --target)        TARGET="$2"; shift 2 ;;
    --repo-url)      REPO_URL="$2"; shift 2 ;;
    --registry-row)  REGISTRY_ROW_URL="$2"; shift 2 ;;
    --author)        AUTHOR="$2"; shift 2 ;;
    --iteration-cap) ITERATION_CAP="$2"; shift 2 ;;
    --cost-cap)      COST_CAP="$2"; shift 2 ;;
    --check-only)    CHECK_ONLY=1; shift ;;
    --no-notion)     NO_NOTION=1; shift ;;
    --force)         FORCE=1; shift ;;
    -h|--help)       usage; exit 0 ;;
    *) err "Unknown arg: $1"; usage; exit 2 ;;
  esac
done

[[ -z "$PROJECT_NAME" ]] && { err "--name is required"; exit 2; }
[[ -z "$SPEC_ID"      ]] && { err "--spec-id is required"; exit 2; }
[[ -z "$TARGET"       ]] && { err "--target is required"; exit 2; }

# ---------- Validate ----------
if [[ ! "$SPEC_ID" =~ ^FORGE-[0-9]{4}-[0-9]{3}$ ]]; then
  err "Spec ID '$SPEC_ID' does not match format FORGE-YYYY-NNN"
  exit 2
fi

if [[ ! -d "$TARGET" ]]; then
  err "Target directory does not exist: $TARGET"
  exit 2
fi

# Read defaults from forge-defaults.yaml if present and not overridden
if [[ -z "$ITERATION_CAP" ]]; then
  if [[ -f "$DEFAULTS_FILE" ]]; then
    val=$(grep -E '^\s*iteration_cap:\s*[0-9]+' "$DEFAULTS_FILE" 2>/dev/null | head -1 | awk '{print $2}' || true)
    ITERATION_CAP="${val:-$ITERATION_CAP_DEFAULT}"
  else
    ITERATION_CAP="$ITERATION_CAP_DEFAULT"
  fi
fi
if [[ -z "$COST_CAP" ]]; then
  if [[ -f "$DEFAULTS_FILE" ]]; then
    val=$(grep -E '^\s*cost_cap_usd:\s*[0-9.]+' "$DEFAULTS_FILE" 2>/dev/null | head -1 | awk '{print $2}' || true)
    COST_CAP="${val:-$COST_CAP_DEFAULT}"
  else
    COST_CAP="$COST_CAP_DEFAULT"
  fi
fi

ISO_TS="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
ISO_DATE="$(date -u +"%Y-%m-%d")"

# ---------- Render templates ----------
render() {
  local src="$1" dst="$2"
  [[ ! -f "$src" ]] && { err "Template missing: $src"; exit 2; }

  if [[ -f "$dst" && $FORCE -eq 0 && $CHECK_ONLY -eq 0 ]]; then
    err "Target file exists: $dst (use --force to overwrite)"
    exit 2
  fi

  # Use sed with a delimiter unlikely to appear in URLs/values
  sed \
    -e "s|{{PROJECT_NAME}}|${PROJECT_NAME//|/\\|}|g" \
    -e "s|{{SPEC_ID}}|${SPEC_ID}|g" \
    -e "s|{{REGISTRY_ROW_URL}}|${REGISTRY_ROW_URL//|/\\|}|g" \
    -e "s|{{REPO_URL}}|${REPO_URL//|/\\|}|g" \
    -e "s|{{LIVE_URL_OR_PENDING}}|(pending — RALPH fills after deploy)|g" \
    -e "s|{{ISO_TIMESTAMP}}|${ISO_TS}|g" \
    -e "s|{{ISO_DATE}}|${ISO_DATE}|g" \
    -e "s|{{FORGE_VERSION}}|${FORGE_VERSION}|g" \
    -e "s|{{AUTHOR}}|${AUTHOR//|/\\|}|g" \
    -e "s|{{ITERATION_CAP}}|${ITERATION_CAP}|g" \
    -e "s|{{COST_CAP_USD}}|${COST_CAP}|g" \
    "$src" > "$dst"
}

if [[ $CHECK_ONLY -eq 0 ]]; then
  inf "Rendering artifacts into $TARGET"
  render "$TEMPLATE_DIR/PRD.md.template"             "$TARGET/PRD.md"
  render "$TEMPLATE_DIR/CLAUDE.md.template"          "$TARGET/CLAUDE.md"
  render "$TEMPLATE_DIR/verifier.md.template"        "$TARGET/verifier.md"
  render "$TEMPLATE_DIR/stop-conditions.md.template" "$TARGET/stop-conditions.md"
  ok "Templates rendered. Fill in {{PLACEHOLDERS}} before running --check-only."
  ok "Artifacts: PRD.md, CLAUDE.md, verifier.md, stop-conditions.md"
  echo ""
  warn "Templates contain placeholders that must be filled before ignition completes:"
  warn "  - PRD.md: Problem, Goal, Acceptance Criteria, Tech Stack, etc."
  warn "  - CLAUDE.md: tech stack, commands, conventions"
  warn "  - verifier.md: BUILD/TEST/LINT commands, acceptance criteria mapping"
  echo ""
  inf "Once filled in, re-run with --check-only to validate, then commit."
  exit 0
fi

# ---------- Pre-Ignition Acceptance Checklist ----------
inf "Running Pre-Ignition Acceptance Checklist on $TARGET"

failed=0
fail_msg=""

check() {
  local name="$1" passed="$2" detail="${3:-}"
  if [[ "$passed" == "1" ]]; then
    ok "$name"
  else
    err "$name${detail:+ — $detail}"
    failed=1
    fail_msg="${fail_msg}\n  - $name${detail:+: $detail}"
  fi
}

# --- Check 1: PRD exists with all 8 sections
prd="$TARGET/PRD.md"
if [[ -f "$prd" ]]; then
  required_sections=("Problem" "Goal" "Non-goals" "Users" "Acceptance Criteria" "Tech Stack" "Out of Scope" "Open Questions")
  missing=""
  for s in "${required_sections[@]}"; do
    grep -qE "^##\s+${s}\s*$" "$prd" || missing="${missing}${missing:+, }${s}"
  done
  if [[ -z "$missing" ]]; then
    check "PRD has all 8 required sections" 1
  else
    check "PRD has all 8 required sections" 0 "missing: $missing"
  fi
else
  check "PRD.md exists" 0 "$prd not found"
fi

# --- Check 2: PRD Open Questions empty
if [[ -f "$prd" ]]; then
  # Extract Open Questions section content (between "## Open Questions" and the next
  # heading or horizontal rule). Filter out blanks, HTML comments, and the literal "(none)".
  oq_content=$(awk '
    /^## Open Questions[[:space:]]*$/ { flag=1; next }
    /^## / || /^---[[:space:]]*$/ { flag=0 }
    flag
  ' "$prd" | \
    grep -v '^[[:space:]]*$' | \
    grep -v '^[[:space:]]*<!--' | \
    grep -v '^[[:space:]]*-->' | \
    grep -v '^[[:space:]]*HARD RULE' | \
    grep -v '^[[:space:]]*If any question' | \
    grep -v '^[[:space:]]*RALPH refuses' | \
    grep -v '^[[:space:]]*(none)' || true)
  if [[ -z "$oq_content" ]]; then
    check "PRD Open Questions is empty" 1
  else
    check "PRD Open Questions is empty" 0 "found content; resolve before ignition"
  fi
fi

# --- Check 3: CLAUDE.md exists
if [[ -f "$TARGET/CLAUDE.md" ]]; then
  check "CLAUDE.md exists in target" 1
else
  check "CLAUDE.md exists in target" 0
fi

# --- Check 4: verifier.md has ≥3 machine-readable checks
ver="$TARGET/verifier.md"
if [[ -f "$ver" ]]; then
  check_count=$(grep -cE '^[[:space:]]*-[[:space:]]+id:' "$ver" || true)
  if [[ "${check_count:-0}" -ge 3 ]]; then
    check "verifier.md has ≥3 machine-readable checks ($check_count found)" 1
  else
    check "verifier.md has ≥3 machine-readable checks" 0 "only $check_count found"
  fi
else
  check "verifier.md exists" 0
fi

# --- Check 5: stop-conditions.md has all 6 minimum conditions
sc="$TARGET/stop-conditions.md"
if [[ -f "$sc" ]]; then
  cond_keywords=("Success" "Iteration Cap" "Cost Cap" "Schema" "Hard Error" "Human Override")
  missing=""
  for k in "${cond_keywords[@]}"; do
    grep -qiE "^###[[:space:]]+[0-9]+\.[[:space:]]+${k}" "$sc" || missing="${missing}${missing:+, }${k}"
  done
  if [[ -z "$missing" ]]; then
    check "stop-conditions.md has all 6 minimum conditions" 1
  else
    check "stop-conditions.md has all 6 minimum conditions" 0 "missing: $missing"
  fi
else
  check "stop-conditions.md exists" 0
fi

# --- Check 6: Repo URL set
if [[ -n "$REPO_URL" ]]; then
  check "Repo URL provided" 1 "$REPO_URL"
elif [[ -d "$TARGET/.git" ]]; then
  detected=$(git -C "$TARGET" config --get remote.origin.url 2>/dev/null || true)
  if [[ -n "$detected" ]]; then
    check "Repo URL detected from git" 1 "$detected"
    REPO_URL="$detected"
  else
    check "Repo URL provided or detectable" 0 "pass --repo-url or set git remote"
  fi
else
  check "Repo URL provided" 0 "pass --repo-url"
fi

# --- Check 7: Spec ID format (already validated above; re-affirm here)
check "Spec ID matches FORGE-YYYY-NNN" 1 "$SPEC_ID"

# --- Check 8: .ralph-stop absent
if [[ -f "$TARGET/.ralph-stop" ]]; then
  check ".ralph-stop NOT present" 0 "remove $TARGET/.ralph-stop before ignition"
else
  check ".ralph-stop NOT present" 1
fi

# --- Check 9: Notion API credentials available (only if writeback intended)
if [[ $NO_NOTION -eq 0 ]]; then
  if [[ -n "${NOTION_FORGE_TOKEN:-}" && -n "${REGISTRY_PAGE_ID:-}" ]]; then
    check "Notion credentials available for writeback" 1
  else
    check "Notion credentials available for writeback" 0 "set NOTION_FORGE_TOKEN and REGISTRY_PAGE_ID, or pass --no-notion"
  fi
fi

if [[ $failed -ne 0 ]]; then
  echo ""
  err "Pre-Ignition Checklist FAILED. Row stays in Spec Drafting."
  printf '%b\n' "$fail_msg" >&2
  exit 1
fi

ok "Pre-Ignition Checklist PASSED."

# ---------- Notion writeback ----------
if [[ $NO_NOTION -eq 1 ]]; then
  warn "Notion writeback skipped (--no-notion)"
  ok "Local artifacts ready. Manually flip Registry row to Ignited."
  exit 0
fi

if [[ -z "${NOTION_FORGE_TOKEN:-}" || -z "${REGISTRY_PAGE_ID:-}" ]]; then
  warn "Notion writeback skipped (NOTION_FORGE_TOKEN or REGISTRY_PAGE_ID unset)"
  ok "Local artifacts ready. Manually flip Registry row to Ignited."
  exit 0
fi

inf "Updating Notion Registry row $REGISTRY_PAGE_ID → Ignited"

# Notion API: PATCH /v1/pages/{page_id}
# Sets Build State = Ignited, appends a Notes line.
notes_append="Ignited via forge-ignite.sh on ${ISO_TS} (Spec ${SPEC_ID})"

http_code=$(curl -sS -o /tmp/forge-ignite-notion.json -w "%{http_code}" \
  -X PATCH "https://api.notion.com/v1/pages/${REGISTRY_PAGE_ID}" \
  -H "Authorization: Bearer ${NOTION_FORGE_TOKEN}" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d "$(cat <<JSON
{
  "properties": {
    "Build State": { "select": { "name": "Ignited" } },
    "Repo URL": { "url": "${REPO_URL}" },
    "Notes": { "rich_text": [{ "type": "text", "text": { "content": "${notes_append}" } }] }
  }
}
JSON
)" 2>&1) || true

if [[ "$http_code" == "200" ]]; then
  ok "Notion Registry row updated to Ignited"
else
  err "Notion API returned HTTP $http_code"
  err "Response saved to /tmp/forge-ignite-notion.json"
  exit 3
fi

echo ""
ok "✦ Ignition complete for $PROJECT_NAME ($SPEC_ID)"
ok "RALPH may now consume the artifacts in $TARGET"
