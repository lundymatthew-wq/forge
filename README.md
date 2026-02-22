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
├── forge.py              # The engine
├── specs/                # App specifications (YAML)
│   └── coop-briefing.yaml
├── templates/            # Reusable HTML/email templates
│   └── tron-briefing.html
├── output/               # Generated apps (gitignored)
│   └── coop-briefing/
│       ├── layer1-directive/
│       ├── layer2-orchestration/
│       └── layer3-execution/
└── docs/                 # Architecture notes, manual
```

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
