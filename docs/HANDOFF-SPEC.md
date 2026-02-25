# FORGE-to-RALPH Handoff Specification
## Version 1.0 — Brave Alpaca

---

## Overview

This spec defines how FORGE generates output that RALPH can immediately consume. 
The goal: **describe a project idea → FORGE produces scaffold + PRD → you refine → RALPH builds it out.**

---

## The Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   YOU (Product Owner)                                               │
│   "I want a tool that breaks down employee processes                │
│    into AI automation opportunities with time savings"              │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   FORGE (Inception — first 10-15%)                                  │
│                                                                     │
│   Generates:                                                        │
│   ├── Project scaffold (src/, tests, config, package.json)          │
│   ├── PRD.json         ← stories with acceptance criteria           │
│   ├── progress.txt     ← initialized empty log                     │
│   └── ralph.sh         ← pre-configured bash loop                  │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   YOU (Review Gate)                                                 │
│                                                                     │
│   - Review PRD stories: right scope? right priority?                │
│   - Adjust acceptance criteria                                      │
│   - Add/remove/reorder stories                                      │
│   - Set config values (hourly rate, tech preferences, etc.)         │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   RALPH (Maturation — next 20-40%)                                  │
│                                                                     │
│   Loop:                                                             │
│   1. Read PRD.json + progress.txt                                   │
│   2. Pick highest-priority non-passing story                        │
│   3. Implement it (code + tests)                                    │
│   4. Run CI guardrails                                              │
│   5. Commit, update PRD, append to progress.txt                     │
│   6. Exit iteration → fresh context → repeat                        │
│                                                                     │
│   Until: all stories pass OR max iterations reached                 │
│                                                                     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   YOU (Polish & Ship — final 40-60%)                                │
│                                                                     │
│   - Review RALPH's output                                           │
│   - Add new PRD stories for next phase                              │
│   - UX polish, edge cases, deployment                               │
│   - Run another RALPH loop if needed                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## FORGE Output Requirements

When FORGE generates a project, it MUST produce these files in addition to 
the normal project scaffold:

### 1. PRD.json

Location: `{project_root}/PRD.json`

Schema: See 01-PRD-TEMPLATE.json

**Story Decomposition Rules:**

| Rule | Rationale |
|------|-----------|
| One story = one context window | RALPH gets a fresh context each iteration. If a story needs more than ~200 lines of changes, it's too big. |
| Every story has a test_command | RALPH must verify its own work. No test = no verification = drift. |
| Acceptance criteria are machine-checkable | "It looks nice" is not verifiable. "Test X passes" is. |
| Dependencies are explicit | RALPH checks depends_on before starting. No implicit ordering. |
| Priority numbers are unique and sequential | RALPH picks the lowest non-passing priority. Ties cause ambiguity. |
| First 2-3 stories are always scaffold/config | The project must build and test before any features are added. |
| Last story is always README/docs | Documentation happens after code is stable. |

**Story Sizing Guide:**

| Story Size | Lines of Change | Good For |
|-----------|----------------|----------|
| XS | < 50 lines | Config, schema definitions, types |
| S | 50-100 lines | Single function + tests |
| M | 100-200 lines | Module with 2-3 functions + tests |
| TOO BIG | > 200 lines | Split into multiple stories |

### 2. progress.txt

Location: `{project_root}/progress.txt`

- Initialized with a header block (project name, date, format guide)
- Body is empty — RALPH appends entries
- Format per entry: `[ISO_TIMESTAMP] S-XXX | PASS|FAIL | Summary`
- MUST be append-only (RALPH prompt uses verb "append")

### 3. ralph.sh

Location: `{project_root}/ralph.sh`

- Pre-configured with project name, PRD file path, progress file path
- Default max iterations: 20
- Accepts iteration count as $1 argument
- Uses `claude --permission-mode acceptEdits -p` for non-interactive execution
- Checks for `<promise>COMPLETE</promise>` sigil to exit early
- Prints iteration status to stdout

### 4. .ralph-config (optional, future)

For projects that need custom RALPH behavior:

```json
{
  "agent": "claude",
  "permission_mode": "acceptEdits",
  "docker_sandbox": false,
  "pre_iteration_hook": "",
  "post_iteration_hook": "npm run lint:fix",
  "completion_hook": "say 'Ralph is done!'"
}
```

---

## PRD Design Patterns

### Pattern: Foundation First
Stories 1-3 should always establish the project skeleton before any business logic.
```
S-001: Scaffold and config
S-002: Core data models / schemas  
S-003: Input parsing / validation
S-004+: Business logic features
```

### Pattern: Inside Out
Build the core engine first, then wrap it in interfaces.
```
S-001-006: Core logic (models, classifier, calculator)
S-007: Pipeline/orchestrator that wires core together
S-008+: CLI, API, or web interface on top
```

### Pattern: Test Fixtures as Stories
Sample data and demo fixtures get their own story near the end.
This ensures the tool works end-to-end before adding examples.
```
S-N-1: Sample data / demo fixtures
S-N:   README and documentation
```

---

## Human Review Checklist (between FORGE and RALPH)

Before running `./ralph.sh`, review:

- [ ] Are story sizes realistic for one context window each?
- [ ] Do all acceptance criteria have matching test_commands?
- [ ] Are dependencies correct? (no circular deps, no missing deps)
- [ ] Is the priority order sensible? (foundation → logic → interface → docs)
- [ ] Are guardrail CI commands correct for this tech stack?
- [ ] Is the commit convention what you want?
- [ ] Are forbidden_patterns appropriate?
- [ ] Have you initialized git and made an initial commit?

---

## Integration with COOP

COOP's role in this pipeline is strategic:

- **Pre-FORGE:** Help articulate the project idea, identify requirements
- **Post-FORGE / Pre-RALPH:** Review the PRD, suggest story adjustments
- **During RALPH:** Monitor progress.txt, flag issues
- **Post-RALPH:** Plan next phase, generate new PRD stories for the next 20%

This keeps COOP as the orchestration/strategy layer while FORGE and RALPH 
handle the generative and iterative execution.
