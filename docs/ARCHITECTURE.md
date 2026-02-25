# FORGE Architecture

## Philosophy

Build the machine -> Improve the machine -> Run apps through the machine.

FORGE is a meta-system. It doesn't run apps — it generates them.

## Five Layers

Every app FORGE produces has up to five layers. Layers 1-3 always run; Layers 4-5 are opt-in.

### Layer 1 — Directive (DNA)
The identity and configuration of the app. What it is, what it connects to, how its AI components behave.

**Generates:** `.env` templates, `app-config.json`, `system-prompts.json`

### Layer 2 — Orchestration (Nervous System)
The wiring between components. What triggers what, how data flows, where outputs go.

**Generates:** n8n workflow JSON, routing maps (Mermaid), connection logic

### Layer 3 — Execution (Muscles)
The actual code that runs. API routes, services, templates, containers.

**Generates:** FastAPI app, route files, service helpers, Dockerfile, HTML templates, run scripts

### Layer 4 — Scaffold (Skeleton) [opt-in]
The agent framework. Safety guardrails, confidence scoring, audit trail, cost tracking, health monitoring, business metrics, and tests.

**Generates:**
- `agent/directive/guardrails.py` — Hard safety rules (email limits, sensitive content, confirmation)
- `agent/directive/system_prompt.md` — Agent personality + rules
- `agent/orchestration/confidence.py` — 4-factor confidence scoring (execute/review/stop)
- `agent/execution/audit_log.py` — JSONL audit trail of agent decisions
- `monitoring/cost_tracker.py` — Per-call API cost logging with daily limits
- `monitoring/health_check.py` — 30-second structural verification
- `business/roi_tracker.py` — Task-level hours saved + USD value
- `business/feature_flags.py` — Multi-tier feature toggles (free/pro/business)
- `tests/` — conftest, test_guardrails, test_connections, test_data_flow
- `CLAUDE.md`, `ARCHITECTURE.md`, `Makefile`, `config.yaml`

**Enable:** Add `scaffold: { enabled: true }` to spec, or use `forge.py new`.

### Layer 5 — RALPH (Growth Loop) [opt-in]
The iterative AI build loop. Produces the files RALPH needs to implement stories one context window at a time.

**Generates:**
- `PRD.json` — Story-based product requirements with acceptance criteria and test commands
- `ralph.sh` — Pre-configured bash loop that calls Claude Code CLI per iteration
- `progress.txt` — Append-only log of iteration results

**Enable:** Add `ralph:` section to spec with stories and CI commands.

## Spec Format

A single YAML file defines everything FORGE needs to generate all layers. See `specs/coop-briefing.yaml` for the canonical example.

Optional sections for Layers 4 and 5:
```yaml
scaffold:
  enabled: true

ralph:
  enabled: true
  ci_commands:
    - "make test"
  commit_convention: "feat|fix|chore: description (S-XXX)"
  stories:
    - id: "S-001"
      priority: 1
      title: "Project scaffold"
      ...
```

## Build Pipeline

```
spec.yaml -> Forge.build()
               +-- DirectiveGenerator.generate()      -> Layer 1
               +-- OrchestrationGenerator.generate()   -> Layer 2
               +-- ExecutionGenerator.generate()        -> Layer 3
               +-- ScaffoldGenerator.generate()         -> Layer 4 (if scaffold:)
               +-- RalphGenerator.generate()            -> Layer 5 (if ralph:)
               +-- write_manifest()                     -> MANIFEST.json
```

## RALPH Pipeline (Post-FORGE)

```
FORGE generates -> PRD.json + ralph.sh + progress.txt
Human reviews   -> Adjust stories, acceptance criteria, priorities
Run ralph.sh    -> Loop: pick story -> implement -> test -> commit -> repeat
Complete        -> All stories pass, <promise>COMPLETE</promise> sigil
```

---

Brave Alpaca . COOP . Life Cockpit
