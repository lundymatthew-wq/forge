# ⬡ FORGE

**Factory for Orchestrated Runtime Generation of Engines**

The machine that builds machines.

```
forge.py build specs/your-app.yaml
```

One YAML spec in → complete deployable app out.

---

## What It Does

FORGE reads a declarative app spec and generates all three layers:

| Layer | Purpose | Output |
|-------|---------|--------|
| **1 — Directive** | DNA of the app | `.env` template, app config, AI system prompts |
| **2 — Orchestration** | Nervous system | n8n workflow JSON, routing maps |
| **3 — Execution** | Muscles | FastAPI backend, routes, services, Dockerfile, frontend |

## Quick Start

```bash
# Clone
git clone git@github.com:brave-alpaca/forge.git
cd forge

# Build an app
python forge.py build specs/coop-briefing.yaml

# See what was generated
tree output/coop-briefing/

# Deploy it
cd output/coop-briefing
cp layer1-directive/.env.template .env
# Edit .env with your keys
bash run.sh
```

## Writing a Spec

Every app is defined in a single YAML file under `specs/`. The spec declares:

- **app** — identity, brand, version
- **triggers** — what starts it (schedule, webhook, event)
- **sources** — where data comes from (API calls, databases)
- **processors** — how data is transformed (merge, AI, code)
- **delivery** — where output goes (email, voice, webhook, UI)
- **backend** — API services to generate (FastAPI routes)
- **integrations** — external services (Gmail, Calendar, Anthropic, ElevenLabs)

See `specs/coop-briefing.yaml` for a complete example.

## Commands

```bash
# Build — generate all layers from a spec
python forge.py build specs/app.yaml

# Build to specific directory
python forge.py build specs/app.yaml --output ./my-app

# Validate — check spec without building
python forge.py validate specs/app.yaml

# List layers — preview what will be generated
python forge.py list-layers specs/app.yaml
```

## Directory Structure

```
forge/
├── forge.py              # The YAML-spec engine
├── forge-ignite.sh       # FORGE-RALPH ignition (markdown handoff path)
├── specs/                # App specifications (YAML)
│   └── coop-briefing.yaml
├── templates/
│   ├── tron-briefing.html
│   ├── ralph/            # Legacy JSON-PRD scaffold
│   └── forge-ralph/      # Markdown handoff templates (PRD, CLAUDE, verifier, stop-conditions)
├── output/               # Generated apps (gitignored)
│   └── coop-briefing/
│       ├── layer1-directive/
│       ├── layer2-orchestration/
│       └── layer3-execution/
└── docs/                 # Architecture notes, manual, integration spec
```

## FORGE-RALPH Ignition (v1.0)

A second handoff path lives alongside the YAML build pipeline: **FORGE-RALPH Ignition**. Where `forge.py build` generates whole apps from a YAML spec, `forge-ignite.sh` does the opposite — it produces the **handoff contract** that lets a human-driven RALPH loop run start-to-finish without a strategist in the middle.

Spec: [`docs/forge-ralph-integration-spec.md`](docs/forge-ralph-integration-spec.md).

### What it produces

Four artifacts, written into a target repo:

| File | Purpose |
|---|---|
| `PRD.md` | What to build and why. 8 required sections; no open questions. |
| `CLAUDE.md` | RALPH's standing instructions for this project. |
| `verifier.md` | When a build iteration is "done." Machine-readable checks + prose. |
| `stop-conditions.md` | The six off-switches: success, iteration cap, cost cap, drift, hard error, `.ralph-stop`. |

Templates live in `templates/forge-ralph/`.

### Usage

```bash
# 1. Render templates into a target repo
./forge-ignite.sh \
  --name "Rhed" \
  --spec-id "FORGE-2026-002" \
  --target ~/projects/rhed \
  --repo-url "https://github.com/matt/rhed" \
  --registry-row "https://www.notion.so/..."

# 2. Fill in the {{PLACEHOLDERS}} (Acceptance Criteria, Tech Stack, etc.)
#    Edit PRD.md, CLAUDE.md, verifier.md in the target repo.

# 3. Validate. Pre-Ignition Checklist gates the transition to Ignited.
./forge-ignite.sh \
  --name "Rhed" \
  --spec-id "FORGE-2026-002" \
  --target ~/projects/rhed \
  --check-only

# 4. Pass --no-notion to skip Registry writeback, or set both env vars below
#    to flip the Registry row to Ignited automatically.
```

### Pre-Ignition Acceptance Checklist

`--check-only` runs these checks and refuses to proceed if any fail:

- PRD has all 8 required sections (Problem, Goal, Non-goals, Users, Acceptance Criteria, Tech Stack, Out of Scope, Open Questions)
- PRD `Open Questions` section is empty
- `CLAUDE.md` exists in target
- `verifier.md` has ≥3 machine-readable checks (`- id:` entries)
- `stop-conditions.md` defines all 6 minimum conditions
- Repo URL provided (or detected from `git remote`)
- Spec ID matches `FORGE-YYYY-NNN`
- `.ralph-stop` is absent
- Notion credentials available (unless `--no-notion`)

### Environment variables (for Notion writeback)

| Variable | Purpose |
|---|---|
| `NOTION_FORGE_TOKEN` | Notion integration token, scoped to the FORGE Registry database. Integration name: "FORGE-RALPH". |
| `REGISTRY_PAGE_ID` | Notion page ID of the Registry row to update. |

When both are set and the checklist passes, `forge-ignite.sh` PATCHes the Registry row: `Build State → Ignited`, sets `Repo URL`, appends a Notes line. Without them, you flip the row by hand.

### Defaults override

`iteration_cap` and `cost_cap_usd` default to `5` and `25`. To override per project, drop a `forge-defaults.yaml` next to `forge-ignite.sh`:

```yaml
iteration_cap: 8
cost_cap_usd: 50
```

CLI flags `--iteration-cap` and `--cost-cap` override the file.

### What this does NOT do

`forge-ignite.sh` does not run the RALPH loop. That's Huntley's `ralph-wiggum` plugin, which consumes the artifacts this script produces. The boundary is intentional — FORGE manufactures the spec, RALPH manufactures the code.

---

## Roadmap

- [ ] AI-powered code generation (Claude writes transform logic from spec descriptions)
- [ ] Template injection (wire existing HTML templates into generated apps)
- [ ] `forge watch` — rebuild on spec changes
- [ ] Trigger-aware delivery routing
- [ ] Multi-app orchestration (apps that talk to each other)
- [ ] Cost estimation before build
- [ ] Plugin system for custom generators

---

**Brave Alpaca** · COOP · Life Cockpit
