# FORGE Architecture

## Philosophy

Build the machine → Improve the machine → Run apps through the machine.

FORGE is a meta-system. It doesn't run apps — it generates them.

## Three Layers

Every app FORGE produces has exactly three layers:

### Layer 1 — Directive (DNA)
The identity and configuration of the app. What it is, what it connects to, how its AI components behave.

**Generates:** `.env` templates, `app-config.json`, `system-prompts.json`

### Layer 2 — Orchestration (Nervous System)
The wiring between components. What triggers what, how data flows, where outputs go.

**Generates:** n8n workflow JSON, routing maps (Mermaid), connection logic

### Layer 3 — Execution (Muscles)
The actual code that runs. API routes, services, templates, containers.

**Generates:** FastAPI app, route files, service helpers, Dockerfile, HTML templates, run scripts

## Spec Format

A single YAML file defines everything FORGE needs to generate all three layers. See `specs/coop-briefing.yaml` for the canonical example.

## Build Pipeline

```
spec.yaml → Forge.build()
              ├── DirectiveGenerator.generate()    → Layer 1
              ├── OrchestrationGenerator.generate() → Layer 2
              ├── ExecutionGenerator.generate()     → Layer 3
              └── write_manifest()                  → MANIFEST.json
```

---

Brave Alpaca · COOP · Life Cockpit
