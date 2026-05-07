# 🔗 FORGE–RALPH Integration Spec v1.0

**Status:** v1.0 — Ratified
**Date:** 2026-05-07
**Owner:** Matt Lundy
**Parent:** AgentC4 Mission Control
**Companions:** FORGE Project Registry — Spec v1.1, Ignition Template

---

## TL;DR

FORGE manufactures the spec. RALPH manufactures the code. This document defines the **handoff contract** between them — what FORGE must produce at ignition so a Claude Code RALPH loop can run start-to-finish without a human in the middle.

If FORGE leaves any of the required artifacts blank, RALPH stalls. If RALPH can't write back to the Registry, FORGE loses visibility. This spec closes both gaps.

---

## Purpose & Scope

**In scope:**
- The artifacts FORGE must produce before a project moves from `Spec Drafting` → `Ignited`
- The structure of those artifacts (PRD, `CLAUDE.md`, verifier contract, stop conditions)
- How RALPH writes state back to the Registry
- Failure modes and recovery paths
- Acceptance checklist FORGE runs before ignition

**Out of scope:**
- The internals of the RALPH loop itself (that's Huntley's pattern, owned by `ralph-wiggum`)
- The Persona Engine logic that drives PRD content
- Multi-project orchestration (one project per RALPH loop, period)
- The `forge-defaults.yaml` circuit breakers (separate spec, blocked on local machine access)

---

## The Two Sides

```
┌─────────────────────────┐         ┌─────────────────────────┐
│      FORGE (you)        │         │      RALPH (Code)       │
│   Claude.ai + Notion    │ ──────▶ │   Claude Code + Git     │
│                         │  spec   │                         │
│  Produces ignition pkg  │         │  Consumes pkg, builds   │
│  Updates Registry rows  │ ◀────── │  Writes state to files  │
│                         │  state  │  Writes back to Registry│
└─────────────────────────┘         └─────────────────────────┘
       Strategy side                       Execution side
       Memory: Notion                      Memory: files + git
```

Same RALPH principle on both sides: **state lives outside the chat**. Different storage layers, identical discipline.

---

## Required Ignition Artifacts

A Registry row cannot move to `Ignited` until **all five** of these exist and are linked from the row.

### 1. PRD (Product Requirements Document)

**Location:** Google Drive, linked from `PRD Link` field.
**Format:** Markdown.
**Purpose:** The "what" and "why." RALPH reads this once at the start of every loop iteration.

**Required sections (in this order):**

| Section | Length | Notes |
|---|---|---|
| Problem | 1 paragraph | What's broken or missing |
| Goal | 1–3 sentences | What "done" looks like |
| Non-goals | Bullet list | What we're explicitly not building |
| Users | 1 paragraph | Who this is for (link Persona Engine output if used) |
| Acceptance Criteria | Numbered list | Testable conditions; RALPH treats this as the verifier input |
| Tech Stack | Bullet list | Languages, frameworks, services (Supabase, Vercel, etc.) |
| Out of Scope | Bullet list | Explicit deferrals — anti-scope-creep |
| Open Questions | Bullet list | Must be empty before ignition |

**Hard rule:** If `Open Questions` has any entries, FORGE stays in `Spec Drafting`. No exceptions.

### 2. CLAUDE.md

**Location:** Repo root, committed as `CLAUDE.md`.
**Purpose:** The standing instructions Claude Code reads at the start of every session — RALPH's operating manual for this specific project.

**Required sections:**

| Section | Purpose |
|---|---|
| Project identity | Name, Spec ID, Registry row URL |
| Pointers | Links to PRD, Verifier Contract, Stop Conditions, Registry row |
| Tech stack | Mirrors PRD; canonical reference for choices |
| Commands | Exact commands to run dev server, test, build, deploy |
| Conventions | Naming, file layout, commit message format |
| What NOT to do | Things RALPH should refuse (e.g., "never bypass auth," "never edit X without spec update") |
| Update protocol | How and when to update Status/Directives/Context (if Shared Brain pattern applies) |

**Length target:** 200–400 lines. If it's longer, it's doing too much; split into linked sub-docs.

### 3. Verifier Contract

**Location:** Repo, committed as `verifier.md` (or `.spec/verifier.md`).
**Purpose:** Defines exactly when a build iteration is "done." RALPH runs this check at the end of every loop pass.

**Required content:**

```yaml
# verifier.md — machine-readable section
checks:
  - id: build_passes
    command: "npm run build"
    expect: "exit_code == 0"
  - id: tests_pass
    command: "npm test"
    expect: "exit_code == 0"
  - id: lint_clean
    command: "npm run lint"
    expect: "exit_code == 0"
  - id: acceptance_criteria
    source: "PRD § Acceptance Criteria"
    expect: "all items checked off"
```

Plus a prose section explaining each check, edge cases, and what "passes" means for ambiguous checks (e.g., visual regression, manual review gates).

**Rule:** RALPH does not declare done until every check passes. A failed check sends RALPH back to the loop.

### 4. Stop Conditions

**Location:** Repo, committed as `stop-conditions.md` (or section inside `verifier.md`).
**Purpose:** The off-switches. When does RALPH stop the loop and surface to a human?

**Required conditions (at minimum):**

1. **Success** — verifier passes all checks
2. **Iteration cap** — N loop iterations without verifier progress. **Default: 5.** Override per project in `forge-defaults.yaml` under `iteration_cap`.
3. **Cost cap** — token spend exceeds threshold. RALPH self-tracks cumulative spend in `.ralph-state.json` from API response usage data. **Default: $25/project.** Override per project in `forge-defaults.yaml` under `cost_cap_usd`. No reliance on Anthropic dashboard.
4. **Schema/contract drift** — RALPH detects PRD acceptance criteria changed mid-loop
5. **Hard error** — uncaught exception, infrastructure failure, auth failure
6. **Human override** — file `.ralph-stop` present in repo root (dotfile, single-file drop, discoverable in any debug session)

Each condition specifies:
- What RALPH does (commit progress, write state, exit)
- What gets written to the Registry (Build State change + Notes)
- Whether human intervention is required to resume

### 5. Registry Writeback Contract

**Location:** This document (canonical). Implemented by RALPH via the Notion API.
**Purpose:** Defines exactly what RALPH writes back to the Registry row, and when.

**State transitions RALPH owns:**

| Trigger | New `Build State` | New `QA Gate Status` | Notes field update |
|---|---|---|---|
| Loop starts | `Manufacturing` | unchanged | "Loop started [timestamp]" |
| Verifier passes | `QA Gate` | `In Review` | "Build complete, ready for review" |
| Stop condition hit (non-success) | `Paused` | unchanged | Reason + iteration count |
| Human marks reviewed (manual) | `Shipped` | `Passed` | (Matt does this, not RALPH) |

**Fields RALPH must update on every state transition:**
- `Build State`
- `Last Updated` (auto via Notion)
- `Notes` (append, don't overwrite)
- `Repo URL` (if not already set)
- `Live URL` (if deployment happened)

**Fields RALPH never touches:**
- `Project Name`
- `Spec ID`
- `Priority`
- `Kicked Off`
- `PRD Link`
- `Persona Engine Used`
- `Linked Tracker Row`

---

## Pre-Ignition Acceptance Checklist

FORGE runs this before flipping `Build State` from `Spec Drafting` to `Ignited`. This replaces the three-checkbox stub in the current Ignition template.

```
[ ] PRD exists, linked, and all 8 required sections present
[ ] PRD Open Questions section is empty
[ ] CLAUDE.md exists in repo, committed to main
[ ] Verifier Contract exists with at least 3 machine-readable checks
[ ] Stop Conditions exist with all 6 minimum conditions defined
[ ] Repo URL set on Registry row
[ ] Spec ID assigned (FORGE-YYYY-NNN format)
[ ] Persona Engine Used field populated (if persona work was done)
[ ] First .ralph-stop file removed (or never created)
[ ] Notion API credentials available to RALPH for writeback
```

If any box is unchecked, the row stays in `Spec Drafting`. No partial ignition.

---

## Failure Modes & Recovery

| Failure | Symptom | Recovery |
|---|---|---|
| **Spec drift mid-loop** | RALPH detects PRD acceptance criteria changed after ignition | Stop loop, set state to `Paused`, write Notes "Spec drift detected — re-ignite required" |
| **Verifier never passes** | Iteration cap hit | `Paused` + Notes with last 3 iteration summaries |
| **Notion write fails** | API error, auth expired | RALPH writes state to local `.ralph-state.json`, retries on next iteration, surfaces after 3 failed retries |
| **Verifier itself broken** | Verifier command not found, parse error | Hard stop, `Paused`, Notes "Verifier broken — fix before resume" |
| **Repo in dirty state at start** | Uncommitted changes when RALPH wakes up | RALPH refuses to start. Human must clean up or explicitly override. |
| **Cost cap exceeded** | Token spend > threshold | `Paused`, Notes with spend summary, requires human re-ignite |

---

## What FORGE Hands Off (Concrete Deliverable List)

When FORGE finishes a project's spec phase, the Registry row should look like this before RALPH picks it up:

```
Project Name:        Rhed
Spec ID:             FORGE-2026-002
Build State:         Ignited           ← was Spec Drafting
Priority:            P1 — Ship
Persona Engine Used: [Solo Operator, Marketing-First SMB]
QA Gate Status:      Not Started
Repo URL:            github.com/matt/rhed
Live URL:            (blank — RALPH fills after deploy)
PRD Link:            drive.google.com/...
Handoff Doc Link:    (blank — RALPH fills as it works)
Kicked Off:          2026-05-07
Notes:               Ignited via FORGE-RALPH spec v1.0
```

And in the repo:
```
rhed/
├── CLAUDE.md
├── verifier.md
├── stop-conditions.md
├── .ralph-state.json   (created by RALPH on first loop)
└── ... (project code)
```

That's the handoff. After that, RALPH runs.

---

## Ratified Decisions

The four open questions from the v1.0 draft are resolved:

1. **Iteration cap** — Default 5. Overridable per project in `forge-defaults.yaml` under `iteration_cap`. ✅
2. **Cost cap** — RALPH self-tracks cumulative spend from API response usage. Default $25/project. Overridable in `forge-defaults.yaml` under `cost_cap_usd`. ✅
3. **`.ralph-stop` location** — Repo root. Single-file drop, dotfile prefix, no directory traversal needed. ✅
4. **Notion writeback auth** — Notion integration token, scoped to FORGE Registry database only. Stored in `.env` as `NOTION_FORGE_TOKEN`, never committed. Integration named "FORGE-RALPH". ✅

---

## Plan for Claude Code

This is the handoff. Claude Code will:

1. Read this spec in full (`forge-ralph-integration-spec.md`)
2. Build a project-template scaffold that produces compliant artifacts:
   - `templates/CLAUDE.md.template`
   - `templates/verifier.md.template`
   - `templates/stop-conditions.md.template`
   - `templates/PRD.md.template`
3. Write a `forge-ignite.sh` script that:
   - Reads a project name + Spec ID
   - Generates the four template files into a target repo
   - Runs the Pre-Ignition Acceptance Checklist as automated checks where possible
   - Updates the Registry row to `Ignited` only if all checks pass
4. Document usage in the FORGE repo README

**Claude Code does not need to implement the RALPH loop itself** — that's Huntley's `ralph-wiggum` plugin. Claude Code only needs to produce the artifacts RALPH consumes.

---

## Implementation Notes (post-handoff)

This spec was implemented by Claude Code on 2026-05-07. Deviations from the "Plan for Claude Code" above:

- **Templates live at `templates/forge-ralph/`** (subdirectory) rather than `templates/` root, to coexist with the legacy `templates/ralph/` scaffold and `templates/agent-workflow-shell/`.
- **Notion writeback is implemented in pure bash** via `curl`. No Python helper. Activated when both `NOTION_FORGE_TOKEN` and `REGISTRY_PAGE_ID` are set; pass `--no-notion` to skip.
- **A `forge-defaults.yaml` is read if present** at the FORGE repo root for `iteration_cap` and `cost_cap_usd` overrides. CLI flags take precedence.
- **`forge.py` integration is deferred.** `forge-ignite.sh` is standalone for now; folding the markdown handoff path into the YAML pipeline is a follow-up.

---

## Changelog

| Version | Date | Change | Author |
|---|---|---|---|
| v1.0 | 2026-05-07 | Initial draft | Claude (strategy) |
| v1.0.1 | 2026-05-07 | Added Implementation Notes section | Claude Code |
