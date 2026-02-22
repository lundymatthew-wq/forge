#!/usr/bin/env python3
"""
FORGE — Factory for Orchestrated Runtime Generation of Engines
==============================================================
The machine that builds machines.

Usage:
    python forge.py build specs/coop-briefing.yaml
    python forge.py build specs/coop-briefing.yaml --output ./output/coop
    python forge.py validate specs/coop-briefing.yaml
    python forge.py list-layers specs/coop-briefing.yaml

Architecture:
    FORGE reads a YAML app spec and generates all 3 layers:
    
    Layer 1 — DIRECTIVE    : System prompts, configs, .env templates
    Layer 2 — ORCHESTRATION: n8n workflow JSON, wiring, routing
    Layer 3 — EXECUTION    : FastAPI backend, HTML templates, voice scripts

Brave Alpaca · COOP · Life Cockpit
"""

import json
import os
import sys
import shutil
import hashlib
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[FORGE] PyYAML not found. Install: pip install pyyaml")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════
# FORGE CORE
# ═══════════════════════════════════════════════════════════════

class Forge:
    """The machine that builds machines."""

    VERSION = "1.0.0"

    def __init__(self, spec_path: str, output_dir: str = None):
        self.spec_path = Path(spec_path)
        self.build_log = []
        self.cost_tracker = CostTracker()
        self.spec = self._load_spec()
        self.app_id = self.spec["app"]["id"]
        self.output_dir = Path(output_dir or f"./output/{self.app_id}")

    def _load_spec(self) -> dict:
        """Load and validate the YAML app spec."""
        if not self.spec_path.exists():
            raise FileNotFoundError(f"Spec not found: {self.spec_path}")
        with open(self.spec_path) as f:
            spec = yaml.safe_load(f)
        self._validate_spec(spec)
        return spec

    def _validate_spec(self, spec: dict):
        """Validate required spec sections exist."""
        required = ["app", "triggers", "sources", "delivery"]
        missing = [k for k in required if k not in spec]
        if missing:
            raise ValueError(f"Spec missing required sections: {missing}")
        if "id" not in spec["app"]:
            raise ValueError("app.id is required")
        self._log(f"Spec validated: {spec['app']['name']}")

    def _log(self, msg: str):
        """Log a build step."""
        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {msg}"
        self.build_log.append(entry)
        print(f"  ⬡ {msg}")

    # ─── BUILD PIPELINE ────────────────────────────────────────

    def build(self):
        """Run the full build pipeline — generate all 3 layers."""
        print(f"\n{'═' * 60}")
        print(f"  FORGE v{self.VERSION} — Building: {self.spec['app']['name']}")
        print(f"{'═' * 60}\n")

        # Prepare output
        self._prepare_output()

        # Layer 1: Directive
        print("  ┌─ LAYER 1: DIRECTIVE ─────────────────────────┐")
        directive = DirectiveGenerator(self.spec, self.output_dir)
        directive.generate()
        self._log("Directive layer complete")

        # Layer 2: Orchestration
        print("  ├─ LAYER 2: ORCHESTRATION ─────────────────────┤")
        orchestration = OrchestrationGenerator(self.spec, self.output_dir)
        orchestration.generate()
        self._log("Orchestration layer complete")

        # Layer 3: Execution
        print("  ├─ LAYER 3: EXECUTION ─────────────────────────┤")
        execution = ExecutionGenerator(self.spec, self.output_dir)
        execution.generate()
        self._log("Execution layer complete")

        # Build manifest
        print("  └─ MANIFEST ──────────────────────────────────┘")
        self._write_manifest()

        # Summary
        self._print_summary()

    def _prepare_output(self):
        """Create output directory structure."""
        dirs = [
            self.output_dir,
            self.output_dir / "layer1-directive",
            self.output_dir / "layer2-orchestration",
            self.output_dir / "layer3-execution" / "backend",
            self.output_dir / "layer3-execution" / "frontend",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        self._log(f"Output directory: {self.output_dir}")

    def _write_manifest(self):
        """Write build manifest with all generated files."""
        manifest = {
            "forge_version": self.VERSION,
            "app": self.spec["app"],
            "built_at": datetime.now().isoformat(),
            "spec_hash": hashlib.md5(
                self.spec_path.read_bytes()
            ).hexdigest(),
            "layers": {
                "directive": self._list_files("layer1-directive"),
                "orchestration": self._list_files("layer2-orchestration"),
                "execution": self._list_files("layer3-execution"),
            },
            "build_log": self.build_log,
        }
        manifest_path = self.output_dir / "MANIFEST.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        self._log(f"Manifest written: {manifest_path.name}")

    def _list_files(self, subdir: str) -> list:
        """List all files in a layer subdirectory."""
        path = self.output_dir / subdir
        if not path.exists():
            return []
        files = []
        for f in sorted(path.rglob("*")):
            if f.is_file():
                files.append(str(f.relative_to(self.output_dir)))
        return files

    def _print_summary(self):
        """Print build summary."""
        total = sum(
            len(self._list_files(d))
            for d in [
                "layer1-directive",
                "layer2-orchestration",
                "layer3-execution",
            ]
        )
        print(f"\n{'═' * 60}")
        print(f"  BUILD COMPLETE")
        print(f"  App:   {self.spec['app']['name']}")
        print(f"  Files: {total} generated")
        print(f"  Path:  {self.output_dir}")
        print(f"{'═' * 60}\n")


# ═══════════════════════════════════════════════════════════════
# LAYER 1: DIRECTIVE GENERATOR
# ═══════════════════════════════════════════════════════════════

class DirectiveGenerator:
    """
    Layer 1 — The DNA of the app.
    Generates: system config, .env template, app identity, AI prompts.
    """

    def __init__(self, spec: dict, output_dir: Path):
        self.spec = spec
        self.dir = output_dir / "layer1-directive"

    def generate(self):
        self._gen_env_template()
        self._gen_app_config()
        self._gen_system_prompts()

    def _gen_env_template(self):
        """Generate .env.template from integrations."""
        lines = [
            f"# ─── {self.spec['app']['name']} ───",
            f"# Generated by FORGE v{Forge.VERSION}",
            f"# {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "# App Config",
            f"APP_ID={self.spec['app']['id']}",
            f"APP_PORT={self.spec.get('backend', {}).get('port', 8000)}",
            "",
        ]

        integrations = self.spec.get("integrations", {})
        if integrations:
            lines.append("# Integrations")
            for name, cfg in integrations.items():
                env_var = cfg.get("env_var", f"{name.upper()}_KEY")
                int_type = cfg.get("type", "api_key")
                lines.append(f"# {name} ({int_type})")
                lines.append(f"{env_var}=your-{name}-key-here")
                # Add scopes as comment if oauth
                if int_type == "oauth2" and "scopes" in cfg:
                    lines.append(f"# Scopes: {', '.join(cfg['scopes'])}")
                lines.append("")

        path = self.dir / ".env.template"
        path.write_text("\n".join(lines))
        print(f"    ✓ .env.template")

    def _gen_app_config(self):
        """Generate app config JSON."""
        app = self.spec["app"]
        config = {
            "id": app["id"],
            "name": app["name"],
            "version": app.get("version", "1.0.0"),
            "description": app.get("description", ""),
            "brand": app.get("brand", {}),
            "triggers": [
                {"id": t["id"], "type": t["type"]}
                for t in self.spec.get("triggers", [])
            ],
            "services": [
                {"id": s["id"], "path": s["path"], "method": s["method"]}
                for s in self.spec.get("backend", {}).get("services", [])
            ],
        }
        path = self.dir / "app-config.json"
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"    ✓ app-config.json")

    def _gen_system_prompts(self):
        """Generate AI system prompts for any AI-powered services."""
        services = self.spec.get("backend", {}).get("services", [])
        ai_services = [
            s for s in services if "anthropic" in s.get("integrations", [])
        ]

        if not ai_services:
            return

        prompts = {}
        for svc in ai_services:
            prompt = self._build_system_prompt(svc)
            prompts[svc["id"]] = prompt

        path = self.dir / "system-prompts.json"
        with open(path, "w") as f:
            json.dump(prompts, f, indent=2)
        print(f"    ✓ system-prompts.json ({len(prompts)} prompts)")

    def _build_system_prompt(self, service: dict) -> dict:
        """Build a system prompt from service spec."""
        app = self.spec["app"]
        return {
            "service_id": service["id"],
            "model": "claude-sonnet-4-20250514",
            "system": (
                f"You are {app['name']}, an AI assistant by Brave Alpaca. "
                f"Your role: {service['description']}. "
                f"Instructions: {service.get('logic', 'Follow best practices.')}"
            ),
            "max_tokens": 1024,
            "temperature": 0.3,
        }


# ═══════════════════════════════════════════════════════════════
# LAYER 2: ORCHESTRATION GENERATOR
# ═══════════════════════════════════════════════════════════════

class OrchestrationGenerator:
    """
    Layer 2 — The nervous system.
    Generates: n8n workflow JSON with proper wiring, routing, merge logic.
    """

    def __init__(self, spec: dict, output_dir: Path):
        self.spec = spec
        self.dir = output_dir / "layer2-orchestration"
        self.node_counter = 0

    def generate(self):
        self._gen_n8n_workflow()
        self._gen_routing_map()

    def _next_pos(self, col: int, row: int) -> list:
        """Calculate node position on n8n canvas."""
        return [240 + (col * 260), 200 + (row * 200)]

    def _gen_n8n_workflow(self):
        """Generate a properly-wired n8n workflow from the spec."""
        nodes = []
        connections = {}

        # ── TRIGGERS (Column 0) ──
        for i, trigger in enumerate(self.spec.get("triggers", [])):
            node = self._build_trigger_node(trigger, i)
            nodes.append(node)

        # ── SOURCES (Column 1) ──
        sources = self.spec.get("sources", [])
        for i, source in enumerate(sources):
            node = self._build_source_node(source, i)
            nodes.append(node)

        # ── MERGE (Column 2) — Wait for all sources ──
        if len(sources) > 1:
            merge_node = {
                "parameters": {
                    "mode": "combine",
                    "combinationMode": "mergeByPosition",
                    "numberInputs": len(sources),
                    "options": {},
                },
                "id": "merge-all",
                "name": "Merge All Data",
                "type": "n8n-nodes-base.merge",
                "typeVersion": 3,
                "position": self._next_pos(2, len(sources) // 2),
            }
            nodes.append(merge_node)

        # ── PROCESSORS (Column 3) ──
        processors = self.spec.get("processors", [])
        for i, proc in enumerate(processors):
            if proc["type"] == "transform":
                node = self._build_transform_node(proc, i)
                nodes.append(node)

        # ── DELIVERY (Column 4) ──
        deliveries = self.spec.get("delivery", [])
        for i, dlv in enumerate(deliveries):
            node = self._build_delivery_node(dlv, i)
            nodes.append(node)

        # ── CONNECTIONS ──
        connections = self._build_connections()

        workflow = {
            "name": self.spec["app"]["name"],
            "nodes": nodes,
            "connections": connections,
            "settings": {
                "executionOrder": "v1",
                "timezone": self.spec["triggers"][0]
                .get("config", {})
                .get("timezone", "America/Chicago"),
            },
        }

        path = self.dir / "workflow.json"
        with open(path, "w") as f:
            json.dump(workflow, f, indent=2)
        print(f"    ✓ workflow.json ({len(nodes)} nodes)")

    def _build_trigger_node(self, trigger: dict, idx: int) -> dict:
        """Generate a trigger node."""
        if trigger["type"] == "schedule":
            cron = trigger.get("config", {}).get("cron", "0 8 * * *")
            parts = cron.split()
            return {
                "parameters": {
                    "rule": {
                        "interval": [
                            {
                                "triggerAtMinute": int(parts[0]),
                                "triggerAtHour": int(parts[1]),
                            }
                        ]
                    }
                },
                "id": trigger["id"],
                "name": trigger.get("name", f"Schedule Trigger {idx+1}"),
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": self._next_pos(0, idx),
            }
        elif trigger["type"] == "webhook":
            cfg = trigger.get("config", {})
            return {
                "parameters": {
                    "httpMethod": cfg.get("method", "POST"),
                    "path": cfg.get("path", f"/webhook-{idx}").lstrip("/"),
                    "responseMode": "responseNode",
                    "options": {},
                },
                "id": trigger["id"],
                "name": trigger.get("name", f"Webhook Trigger {idx+1}"),
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": self._next_pos(0, idx + 2),
            }
        return {}

    def _build_source_node(self, source: dict, idx: int) -> dict:
        """Generate a data source node."""
        cfg = source.get("config", {})
        return {
            "parameters": {
                "method": cfg.get("method", "GET"),
                "url": cfg.get("url", ""),
                "options": {"timeout": cfg.get("timeout", 30000)},
            },
            "id": source["id"],
            "name": source.get("name", source["id"]),
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": self._next_pos(1, idx),
        }

    def _build_transform_node(self, proc: dict, idx: int) -> dict:
        """Generate the transform/code node."""
        return {
            "parameters": {
                "jsCode": self._generate_transform_code(proc),
            },
            "id": proc["id"],
            "name": proc.get("name", "Build Output"),
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": self._next_pos(3, 1),
        }

    def _build_delivery_node(self, delivery: dict, idx: int) -> dict:
        """Generate a delivery node."""
        cfg = delivery.get("config", {})
        if delivery["type"] == "email":
            return {
                "parameters": {
                    "method": "POST",
                    "url": f"http://localhost:{self.spec.get('backend', {}).get('port', 8000)}/api/email/send",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": '={{ JSON.stringify({ to: "' + cfg.get("to", "") + '", subject: $json.subject, html: $json.html }) }}',
                    "options": {"timeout": 30000},
                },
                "id": delivery["id"],
                "name": delivery.get("name", "Send Email"),
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": self._next_pos(4, idx),
            }
        elif delivery["type"] == "voice":
            return {
                "parameters": {
                    "method": "POST",
                    "url": f"http://localhost:{self.spec.get('backend', {}).get('port', 8000)}/api/voice/speak",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": "={{ JSON.stringify({ text: $json.voice }) }}",
                    "options": {"timeout": 60000},
                },
                "id": delivery["id"],
                "name": delivery.get("name", "Voice Output"),
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": self._next_pos(4, idx + 2),
            }
        return {}

    def _build_connections(self) -> dict:
        """Build the connections map — the wiring between all nodes."""
        connections = {}
        triggers = self.spec.get("triggers", [])
        sources = self.spec.get("sources", [])
        processors = self.spec.get("processors", [])
        deliveries = self.spec.get("delivery", [])

        # Triggers → Sources (fan out)
        for trigger in triggers:
            trigger_name = trigger.get("name", trigger["id"])
            targets = trigger.get("outputs_to", [])
            if targets:
                connections[trigger_name] = {
                    "main": [
                        [
                            {"node": self._find_node_name(tid), "type": "main", "index": 0}
                            for tid in targets
                        ]
                    ]
                }

        # Sources → Merge (each to its own input index)
        for i, source in enumerate(sources):
            source_name = source.get("name", source["id"])
            connections[source_name] = {
                "main": [
                    [{"node": "Merge All Data", "type": "main", "index": i}]
                ]
            }

        # Merge → Transform
        if processors:
            transform_node = next(
                (p for p in processors if p["type"] == "transform"), None
            )
            if transform_node:
                connections["Merge All Data"] = {
                    "main": [
                        [
                            {
                                "node": transform_node.get("name", "Build Output"),
                                "type": "main",
                                "index": 0,
                            }
                        ]
                    ]
                }

                # Transform → Delivery (with trigger filtering)
                transform_name = transform_node.get("name", "Build Output")
                delivery_connections = []
                for dlv in deliveries:
                    dlv_name = dlv.get("name", dlv["id"])
                    delivery_connections.append(
                        {"node": dlv_name, "type": "main", "index": 0}
                    )
                if delivery_connections:
                    connections[transform_name] = {
                        "main": [delivery_connections]
                    }

        return connections

    def _find_node_name(self, node_id: str) -> str:
        """Find a node's display name by ID across all spec sections."""
        for section in ["sources", "processors", "delivery"]:
            for item in self.spec.get(section, []):
                if item["id"] == node_id:
                    return item.get("name", item["id"])
        return node_id

    def _generate_transform_code(self, proc: dict) -> str:
        """Generate the JS transform code for the code node."""
        brand = self.spec["app"].get("brand", {})
        app_name = self.spec["app"]["name"]

        # This is the code template — FORGE generates this from the spec
        return f'''// ═══ FORGE-GENERATED TRANSFORM ═══
// App: {app_name}
// Generated: {datetime.now().isoformat()}
//
// This node receives merged data from all sources
// and builds both HTML email and voice script outputs.

const items = $input.all();
const now = new Date();
const dateStr = now.toLocaleDateString('en-US', {{ weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }});

// ── Parse incoming merged data ──
let emailData = {{}};
let calendarData = {{}};
let planData = {{}};

for (const item of items) {{
  const j = item.json;
  if (j.urgent || j.normal || j.low) emailData = j;
  else if (j.events) calendarData = j;
  else if (j.tasks) planData = j;
}}

const urgent = Array.isArray(emailData.urgent) ? emailData.urgent : [];
const normal = Array.isArray(emailData.normal) ? emailData.normal : [];
const low = Array.isArray(emailData.low) ? emailData.low : [];
const events = Array.isArray(calendarData.events) ? calendarData.events : [];
const tasks = Array.isArray(planData.tasks) ? planData.tasks : [];
const totalEmails = urgent.length + normal.length + low.length;

// ── Build voice script (concise for ElevenLabs credits) ──
let voice = 'Good morning, Sir. ';
if (totalEmails > 0) {{
  voice += totalEmails + ' emails. ';
  if (urgent.length > 0) {{
    voice += urgent.length + ' urgent. ';
    for (const e of urgent.slice(0, 3)) {{
      voice += (e.from || 'Unknown') + ': ' + (e.subject || 'no subject') + '. ';
    }}
  }}
}} else {{
  voice += 'Inbox clear. ';
}}
if (events.length > 0) {{
  voice += events.length + ' events today. ';
  for (const ev of events.slice(0, 3)) {{
    voice += (ev.summary || ev.title || 'event') + '. ';
  }}
}} else {{
  voice += 'Calendar clear. ';
}}
voice += 'Anything to dig into, Sir?';

// ── Build HTML (uses FORGE template injection) ──
// The HTML is generated from the template at build time.
// See layer3-execution/frontend/briefing.html for the full template.
// Here we return data for the backend to inject into the template.

return [{{
  json: {{
    html_data: {{
      date: dateStr,
      day: now.toLocaleDateString('en-US', {{ weekday: 'long' }}).toUpperCase(),
      emails: {{ urgent, normal, low, total: totalEmails }},
      events,
      tasks,
    }},
    voice,
    subject: 'COOP · Morning Briefing · ' + now.toLocaleDateString('en-US', {{ month: '2-digit', day: '2-digit', year: 'numeric' }}),
    timestamp: now.toISOString(),
  }}
}}];'''

    def _gen_routing_map(self):
        """Generate a visual routing map (Mermaid diagram)."""
        lines = [
            "%%{init: {'theme': 'dark'}}%%",
            "graph LR",
        ]

        # Triggers
        for t in self.spec.get("triggers", []):
            shape = "([" if t["type"] == "schedule" else "{{"
            end = "])" if t["type"] == "schedule" else "}}"
            lines.append(f'    {t["id"]}{shape}"{t["id"]}"{end}')

        # Sources
        for s in self.spec.get("sources", []):
            lines.append(f'    {s["id"]}["{s["id"]}"]')

        # Processors
        for p in self.spec.get("processors", []):
            lines.append(f'    {p["id"]}[/"{p["id"]}"/]')

        # Delivery
        for d in self.spec.get("delivery", []):
            lines.append(f'    {d["id"]}(("{d["id"]}"))')

        lines.append("")

        # Connections
        for t in self.spec.get("triggers", []):
            for target in t.get("outputs_to", []):
                lines.append(f"    {t['id']} --> {target}")

        for s in self.spec.get("sources", []):
            for target in s.get("outputs_to", []):
                lines.append(f"    {s['id']} --> {target}")

        for p in self.spec.get("processors", []):
            for target in p.get("outputs_to", []):
                lines.append(f"    {p['id']} --> {target}")

        # Merge → delivery
        transform = next(
            (p for p in self.spec.get("processors", []) if p["type"] == "transform"),
            None,
        )
        if transform:
            for d in self.spec.get("delivery", []):
                label = "|voice-only|" if d["type"] == "voice" else ""
                lines.append(f"    {transform['id']} -->{label} {d['id']}")

        path = self.dir / "routing-map.mermaid"
        path.write_text("\n".join(lines))
        print(f"    ✓ routing-map.mermaid")


# ═══════════════════════════════════════════════════════════════
# LAYER 3: EXECUTION GENERATOR
# ═══════════════════════════════════════════════════════════════

class ExecutionGenerator:
    """
    Layer 3 — The muscles.
    Generates: FastAPI backend, HTML templates, requirements, Dockerfile.
    """

    def __init__(self, spec: dict, output_dir: Path):
        self.spec = spec
        self.dir = output_dir / "layer3-execution"
        self.backend_dir = self.dir / "backend"
        self.frontend_dir = self.dir / "frontend"

    def generate(self):
        self._gen_backend_main()
        self._gen_backend_routes()
        self._gen_backend_services()
        self._gen_requirements()
        self._gen_dockerfile()
        self._gen_frontend_template()
        self._gen_run_script()

    def _gen_backend_main(self):
        """Generate main FastAPI app entry point."""
        app = self.spec["app"]
        port = self.spec.get("backend", {}).get("port", 8000)
        services = self.spec.get("backend", {}).get("services", [])

        route_imports = []
        route_includes = []
        for svc in services:
            module_name = svc["id"].replace("-", "_")
            route_imports.append(f"from routes.{module_name} import router as {module_name}_router")
            route_includes.append(f'app.include_router({module_name}_router, tags=["{svc["id"]}"])')

        code = f'''"""
{app["name"]} — Backend API
Generated by FORGE v{Forge.VERSION}
Brave Alpaca · COOP · Life Cockpit
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="{app["name"]}",
    description="{app.get("description", "")}",
    version="{app.get("version", "1.0.0")}",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route imports ──
{chr(10).join(route_imports)}

# ── Include routers ──
{chr(10).join(route_includes)}


@app.get("/health")
async def health():
    return {{"status": "operational", "app": "{app["id"]}", "forge": "{Forge.VERSION}"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port={port})
'''
        path = self.backend_dir / "main.py"
        path.write_text(code)
        print(f"    ✓ backend/main.py")

    def _gen_backend_routes(self):
        """Generate route files for each backend service."""
        routes_dir = self.backend_dir / "routes"
        routes_dir.mkdir(exist_ok=True)

        # __init__.py
        (routes_dir / "__init__.py").write_text("")

        services = self.spec.get("backend", {}).get("services", [])
        for svc in services:
            self._gen_single_route(svc, routes_dir)

    def _gen_single_route(self, service: dict, routes_dir: Path):
        """Generate a single route file from a service spec."""
        module_name = service["id"].replace("-", "_")
        method = service.get("method", "GET").lower()
        path = service.get("path", f"/api/{service['id']}")
        integrations = service.get("integrations", [])
        logic = service.get("logic", "# TODO: implement")

        # Build imports based on integrations
        imports = ["from fastapi import APIRouter, HTTPException"]
        if "gmail" in integrations or "google_calendar" in integrations:
            imports.append("from services.google_auth import get_google_service")
        if "anthropic" in integrations:
            imports.append("import anthropic")
            imports.append("import os")
        if "elevenlabs" in integrations:
            imports.append("import httpx")
            imports.append("import os")
            imports.append("from fastapi.responses import StreamingResponse")

        # Build route function
        if "gmail" in integrations:
            body = self._gen_gmail_route_body(service)
        elif "google_calendar" in integrations:
            body = self._gen_calendar_route_body(service)
        elif "anthropic" in integrations:
            body = self._gen_ai_route_body(service)
        elif "elevenlabs" in integrations:
            body = self._gen_voice_route_body(service)
        else:
            body = f'    # {logic}\n    return {{"status": "ok"}}'

        code = f'''"""
Route: {service["description"]}
Path: {path}
Generated by FORGE
"""

{chr(10).join(imports)}

router = APIRouter()


@router.{method}("{path}")
async def {module_name}():
    """
    {service["description"]}
    
    Logic:
{chr(10).join("    " + l for l in logic.strip().splitlines())}
    """
    try:
{body}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''
        route_path = routes_dir / f"{module_name}.py"
        route_path.write_text(code)
        print(f"    ✓ backend/routes/{module_name}.py")

    def _gen_gmail_route_body(self, service: dict) -> str:
        return '''        service = get_google_service("gmail", "v1")
        results = service.users().messages().list(
            userId="me", q="is:unread", maxResults=20
        ).execute()
        
        messages = results.get("messages", [])
        urgent, normal, low = [], [], []
        
        for msg_meta in messages:
            msg = service.users().messages().get(
                userId="me", id=msg_meta["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()
            
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            email = {
                "id": msg["id"],
                "from": headers.get("From", "Unknown"),
                "subject": headers.get("Subject", "No subject"),
                "time": headers.get("Date", ""),
                "snippet": msg.get("snippet", ""),
            }
            
            # Priority scoring — customize these rules
            sender = email["from"].lower()
            subject = email["subject"].lower()
            
            if any(kw in subject for kw in ["urgent", "asap", "deadline", "action required"]):
                urgent.append(email)
            elif any(kw in sender for kw in ["@atu.edu", "asbtdc", "client"]):
                urgent.append(email)
            elif any(kw in sender for kw in ["newsletter", "noreply", "marketing", "promo"]):
                low.append(email)
            else:
                normal.append(email)
        
        return {"urgent": urgent, "normal": normal, "low": low}'''

    def _gen_calendar_route_body(self, service: dict) -> str:
        return '''        from datetime import datetime, timedelta
        
        service = get_google_service("calendar", "v3")
        
        now = datetime.utcnow()
        start = now.replace(hour=0, minute=0, second=0).isoformat() + "Z"
        end = now.replace(hour=23, minute=59, second=59).isoformat() + "Z"
        
        # Fetch from all calendars
        cal_list = service.calendarList().list().execute()
        all_events = []
        
        for cal in cal_list.get("items", []):
            cal_id = cal["id"]
            cal_name = cal.get("summary", "Unknown")
            
            events_result = service.events().list(
                calendarId=cal_id,
                timeMin=start,
                timeMax=end,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            
            for event in events_result.get("items", []):
                all_events.append({
                    "summary": event.get("summary", "Untitled"),
                    "start": event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "")),
                    "end": event.get("end", {}).get("dateTime", ""),
                    "calendar": cal_name,
                    "location": event.get("location", ""),
                })
        
        all_events.sort(key=lambda e: e.get("start", ""))
        return {"events": all_events}'''

    def _gen_ai_route_body(self, service: dict) -> str:
        return '''        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Load system prompt from directive layer
        import json
        prompts_path = os.path.join(os.path.dirname(__file__), "..", "..", "layer1-directive", "system-prompts.json")
        system_prompt = "You are a daily planning assistant. Generate a prioritized task list."
        
        try:
            with open(prompts_path) as f:
                prompts = json.load(f)
                if "planner-generate" in prompts:
                    system_prompt = prompts["planner-generate"]["system"]
        except FileNotFoundError:
            pass
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": "Generate my prioritized daily plan based on current context. Return as JSON array of {task, tag, priority} objects. Tags: do_now, schedule, delegate."
            }],
        )
        
        # Parse response
        text = response.content[0].text
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r"\\[.*\\]", text, re.DOTALL)
            if json_match:
                tasks = json.loads(json_match.group())
            else:
                tasks = [{"task": text.strip(), "tag": "do_now", "priority": 1}]
        except (json.JSONDecodeError, AttributeError):
            tasks = [{"task": text.strip(), "tag": "do_now", "priority": 1}]
        
        return {"tasks": tasks}'''

    def _gen_voice_route_body(self, service: dict) -> str:
        return '''        from pydantic import BaseModel
        
        class VoiceRequest(BaseModel):
            text: str
        
        # This route needs the request body — refactored for POST
        # For now, return the endpoint info
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not set")
        
        # Default voice — customize in .env
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # Adam
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
                headers={"xi-api-key": api_key},
                json={
                    "text": "Briefing ready.",  # Will be replaced with actual text
                    "model_id": "eleven_turbo_v2",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
                timeout=60.0,
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="ElevenLabs API error")
            
            return StreamingResponse(
                iter([response.content]),
                media_type="audio/mpeg",
                headers={"Content-Disposition": "inline; filename=briefing.mp3"},
            )'''

    def _gen_backend_services(self):
        """Generate shared service modules (Google auth, etc.)."""
        services_dir = self.backend_dir / "services"
        services_dir.mkdir(exist_ok=True)
        (services_dir / "__init__.py").write_text("")

        integrations = self.spec.get("integrations", {})

        if "gmail" in integrations or "google_calendar" in integrations:
            self._gen_google_auth_service(services_dir)

    def _gen_google_auth_service(self, services_dir: Path):
        """Generate Google OAuth service helper."""
        code = '''"""
Google OAuth2 Service Helper
Generated by FORGE
"""

import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_JSON", "credentials.json")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def get_google_service(service_name: str, version: str):
    """Get an authenticated Google API service."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Google credentials not found at {CREDENTIALS_PATH}. "
                    "Download from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    return build(service_name, version, credentials=creds)
'''
        path = services_dir / "google_auth.py"
        path.write_text(code)
        print(f"    ✓ backend/services/google_auth.py")

    def _gen_requirements(self):
        """Generate requirements.txt from integrations."""
        reqs = [
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "python-dotenv>=1.0.0",
            "pydantic>=2.0.0",
        ]

        integrations = self.spec.get("integrations", {})
        if "gmail" in integrations or "google_calendar" in integrations:
            reqs.extend([
                "google-auth>=2.23.0",
                "google-auth-oauthlib>=1.1.0",
                "google-api-python-client>=2.100.0",
            ])
        if "anthropic" in integrations:
            reqs.append("anthropic>=0.40.0")
        if "elevenlabs" in integrations:
            reqs.append("httpx>=0.25.0")

        path = self.backend_dir / "requirements.txt"
        path.write_text("\n".join(sorted(set(reqs))) + "\n")
        print(f"    ✓ backend/requirements.txt")

    def _gen_dockerfile(self):
        """Generate Dockerfile for the backend."""
        port = self.spec.get("backend", {}).get("port", 8000)
        code = f'''FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {port}

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{port}"]
'''
        path = self.backend_dir / "Dockerfile"
        path.write_text(code)
        print(f"    ✓ backend/Dockerfile")

    def _gen_frontend_template(self):
        """Generate the HTML template with FORGE template tags."""
        brand = self.spec["app"].get("brand", {})
        app_name = self.spec["app"]["name"]

        # Copy the existing template if provided, otherwise generate
        code = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{app_name}</title>
<link href="https://fonts.googleapis.com/css2?family={brand.get("font_display", "Orbitron")}:wght@400;700;900&family={brand.get("font_body", "Rajdhani")}:wght@300;400;500;600;700&family={brand.get("font_mono", "Share+Tech+Mono").replace(" ", "+")}&display=swap" rel="stylesheet">
<style>
  :root {{
    --primary: {brand.get("primary_color", "#00a6cf")};
    --accent: {brand.get("accent_color", "#ff3b5c")};
    --warn: {brand.get("warn_color", "#f0a030")};
    --bg: {brand.get("bg_color", "#050510")};
    --text: {brand.get("text_color", "#c0dfe8")};
    --font-display: '{brand.get("font_display", "Orbitron")}', sans-serif;
    --font-body: '{brand.get("font_body", "Rajdhani")}', sans-serif;
    --font-mono: '{brand.get("font_mono", "Share Tech Mono")}', monospace;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: var(--bg); color: var(--text); font-family: var(--font-body); }}
  .container {{ max-width: 680px; margin: 0 auto; padding: 20px; }}
</style>
</head>
<body>
<div class="container">
  <!-- FORGE TEMPLATE: Populated by backend template engine -->
  <!-- Variables: {{{{date}}}}, {{{{emails}}}}, {{{{events}}}}, {{{{tasks}}}} -->
  <div id="app">Loading...</div>
</div>
<script>
  // FORGE: Frontend hydration from API data
  // This template is populated server-side by Jinja2 or client-side via fetch
</script>
</body>
</html>'''
        path = self.frontend_dir / "template.html"
        path.write_text(code)
        print(f"    ✓ frontend/template.html")

    def _gen_run_script(self):
        """Generate a run.sh convenience script."""
        port = self.spec.get("backend", {}).get("port", 8000)
        code = f'''#!/bin/bash
# ═══ FORGE Run Script ═══
# App: {self.spec["app"]["name"]}
# Generated by FORGE v{Forge.VERSION}

set -e

echo "⬡ Starting {self.spec["app"]["name"]}..."

# Check .env
if [ ! -f .env ]; then
    echo "⚠ No .env found. Copy from layer1-directive/.env.template"
    exit 1
fi

# Install deps
cd layer3-execution/backend
pip install -r requirements.txt -q

# Run
echo "⬡ Backend starting on port {port}..."
uvicorn main:app --host 0.0.0.0 --port {port} --reload
'''
        path = self.dir.parent / "run.sh"  # Goes in app root
        path.write_text(code)
        path.chmod(0o755)
        print(f"    ✓ run.sh")


# ═══════════════════════════════════════════════════════════════
# COST TRACKER
# ═══════════════════════════════════════════════════════════════

class CostTracker:
    """Track API costs during build and runtime."""

    def __init__(self):
        self.calls = []

    def log_call(self, provider: str, model: str, tokens_in: int, tokens_out: int):
        cost = self._calculate_cost(provider, model, tokens_in, tokens_out)
        self.calls.append({
            "provider": provider,
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": cost,
            "timestamp": datetime.now().isoformat(),
        })
        return cost

    def _calculate_cost(self, provider, model, tokens_in, tokens_out) -> float:
        rates = {
            "anthropic": {
                "claude-sonnet-4-20250514": (3.0, 15.0),  # per 1M tokens
                "claude-haiku-4-5-20251001": (0.80, 4.00),
            },
            "elevenlabs": {
                "eleven_turbo_v2": (0.30, 0),  # per 1K chars
            },
        }
        provider_rates = rates.get(provider, {})
        model_rates = provider_rates.get(model, (0, 0))
        return (tokens_in * model_rates[0] / 1_000_000) + (
            tokens_out * model_rates[1] / 1_000_000
        )

    def total_cost(self) -> float:
        return sum(c["cost"] for c in self.calls)


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 3:
        print(f"""
╔══════════════════════════════════════════════════════════╗
║  FORGE v{Forge.VERSION} — Factory for Orchestrated Runtime       ║
║  Generation of Engines                                   ║
║                                                          ║
║  Usage:                                                  ║
║    forge.py build <spec.yaml> [--output <dir>]           ║
║    forge.py validate <spec.yaml>                         ║
║    forge.py list-layers <spec.yaml>                      ║
║                                                          ║
║  Brave Alpaca · COOP · Life Cockpit                      ║
╚══════════════════════════════════════════════════════════╝
""")
        sys.exit(1)

    command = sys.argv[1]
    spec_path = sys.argv[2]
    output_dir = None

    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        output_dir = sys.argv[idx + 1]

    if command == "build":
        forge = Forge(spec_path, output_dir)
        forge.build()

    elif command == "validate":
        try:
            forge = Forge(spec_path)
            print("  ✓ Spec is valid")
        except Exception as e:
            print(f"  ✗ Validation failed: {e}")
            sys.exit(1)

    elif command == "list-layers":
        forge = Forge(spec_path)
        print(f"\n  App: {forge.spec['app']['name']}")
        print(f"  Triggers: {len(forge.spec.get('triggers', []))}")
        print(f"  Sources: {len(forge.spec.get('sources', []))}")
        print(f"  Services: {len(forge.spec.get('backend', {}).get('services', []))}")
        print(f"  Deliveries: {len(forge.spec.get('delivery', []))}")
        print(f"  Integrations: {list(forge.spec.get('integrations', {}).keys())}")
        print()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
