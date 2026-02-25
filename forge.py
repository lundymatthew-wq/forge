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
    python forge.py new <name> [description]
    python forge.py test [project-dir]
    python forge.py check [project-dir]

Architecture:
    FORGE reads a YAML app spec and generates up to 5 layers:

    Layer 1 — DIRECTIVE    : System prompts, configs, .env templates
    Layer 2 — ORCHESTRATION: n8n workflow JSON, wiring, routing
    Layer 3 — EXECUTION    : FastAPI backend, HTML templates, voice scripts
    Layer 4 — SCAFFOLD     : Agent framework (guardrails, confidence, audit, tests)
    Layer 5 — RALPH        : PRD.json, ralph.sh, progress.txt for iterative AI builds

Brave Alpaca · COOP · Life Cockpit
"""

import json
import os
import sys
import shutil
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[FORGE] PyYAML not found. Install: pip install pyyaml")
    sys.exit(1)

# ─────────────────────────────────────────
#  FORGE COLORS
# ─────────────────────────────────────────
GREEN  = "\033[92m"
BLUE   = "\033[94m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


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

        # Layer 4: Scaffold (if enabled)
        if self.spec.get("scaffold"):
            print("  ├─ LAYER 4: SCAFFOLD ──────────────────────────┤")
            scaffold = ScaffoldGenerator(self.spec, self.output_dir)
            scaffold.generate()
            self._log("Scaffold layer complete")

        # Layer 5: RALPH (if enabled)
        if self.spec.get("ralph"):
            print("  ├─ LAYER 5: RALPH ─────────────────────────────┤")
            ralph = RalphGenerator(self.spec, self.output_dir)
            ralph.generate()
            self._log("RALPH layer complete")

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
        if self.spec.get("scaffold"):
            dirs.append(self.output_dir / "scaffold")
        if self.spec.get("ralph"):
            dirs.append(self.output_dir / "ralph")
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        self._log(f"Output directory: {self.output_dir}")

    def _write_manifest(self):
        """Write build manifest with all generated files."""
        layers = {
            "directive": self._list_files("layer1-directive"),
            "orchestration": self._list_files("layer2-orchestration"),
            "execution": self._list_files("layer3-execution"),
        }
        if self.spec.get("scaffold"):
            layers["scaffold"] = self._list_files("scaffold")
        if self.spec.get("ralph"):
            layers["ralph"] = self._list_files("ralph")

        manifest = {
            "forge_version": self.VERSION,
            "app": self.spec["app"],
            "built_at": datetime.now().isoformat(),
            "spec_hash": hashlib.md5(
                self.spec_path.read_bytes()
            ).hexdigest(),
            "layers": layers,
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
        layer_dirs = [
            "layer1-directive",
            "layer2-orchestration",
            "layer3-execution",
        ]
        if self.spec.get("scaffold"):
            layer_dirs.append("scaffold")
        if self.spec.get("ralph"):
            layer_dirs.append("ralph")

        total = sum(len(self._list_files(d)) for d in layer_dirs)
        print(f"\n{'=' * 60}")
        print(f"  BUILD COMPLETE")
        print(f"  App:   {self.spec['app']['name']}")
        print(f"  Files: {total} generated")
        print(f"  Path:  {self.output_dir}")
        if self.spec.get("scaffold"):
            print(f"  Scaffold: {len(self._list_files('scaffold'))} files")
        if self.spec.get("ralph"):
            print(f"  RALPH: {len(self._list_files('ralph'))} files")
        print(f"{'=' * 60}\n")


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
        # Only create HTTP nodes for GET sources. POST sources with a body
        # (like the planner) are called inside the Code node after merge.
        sources = self.spec.get("sources", [])
        fetch_sources = [s for s in sources if s.get("config", {}).get("method", "GET") == "GET"]
        for i, source in enumerate(fetch_sources):
            node = self._build_source_node(source, i)
            nodes.append(node)

        # ── MERGE (Column 2) — Wait for all sources ──
        # Only merge sources that are direct fetches (GET). POST sources
        # with a body (like the planner) are called inside the Code node
        # after merge, so they get access to the other sources' data.
        fetch_sources = [s for s in sources if s.get("config", {}).get("method", "GET") == "GET"]
        post_sources = [s for s in sources if s.get("config", {}).get("method", "GET") != "GET"]

        if len(fetch_sources) > 1:
            merge_node = {
                "parameters": {
                    "mode": "append",
                    "options": {},
                },
                "id": "merge-all",
                "name": "Merge All Data",
                "type": "n8n-nodes-base.merge",
                "typeVersion": 3,
                "position": self._next_pos(2, len(fetch_sources) // 2),
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
            # webhookId is required for n8n to register at the short path
            # (without it, n8n namespaces: /{workflowId}/{nodeName}/{path})
            webhook_id = cfg.get("webhook_id", trigger["id"])
            return {
                "parameters": {
                    "httpMethod": cfg.get("method", "POST"),
                    "path": cfg.get("path", f"/webhook-{idx}").lstrip("/"),
                    "responseMode": "lastNode",
                    "options": {},
                },
                "id": trigger["id"],
                "name": trigger.get("name", f"Webhook Trigger {idx+1}"),
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": self._next_pos(0, idx + 2),
                "webhookId": webhook_id,
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
                    "url": f"http://localhost:{self.spec.get('backend', {}).get('port', 8000)}/api/gmail/send",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": '={{ JSON.stringify({ to: "' + cfg.get("to", "") + '", subject: $json.subject, body: $json.body }) }}',
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

        # Split sources: GET sources get fetched as nodes, POST sources
        # are called inside the Code node (they need upstream data).
        fetch_sources = [s for s in sources if s.get("config", {}).get("method", "GET") == "GET"]

        # Triggers → fetch sources only (fan out)
        for i, trigger in enumerate(triggers):
            # Must match the name generated by _build_trigger_node
            if trigger.get("name"):
                trigger_name = trigger["name"]
            elif trigger["type"] == "schedule":
                trigger_name = f"Schedule Trigger {i+1}"
            elif trigger["type"] == "webhook":
                trigger_name = f"Webhook Trigger {i+1}"
            else:
                trigger_name = trigger["id"]
            fetch_ids = [s["id"] for s in fetch_sources]
            targets = [t for t in trigger.get("outputs_to", []) if t in fetch_ids]
            if targets:
                connections[trigger_name] = {
                    "main": [
                        [
                            {"node": self._find_node_name(tid), "type": "main", "index": 0}
                            for tid in targets
                        ]
                    ]
                }

        # Fetch sources → Merge (each to its own input index)
        for i, source in enumerate(fetch_sources):
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
                    # Must match names generated by _build_delivery_node
                    if dlv.get("name"):
                        dlv_name = dlv["name"]
                    elif dlv["type"] == "email":
                        dlv_name = "Send Email"
                    elif dlv["type"] == "voice":
                        dlv_name = "Voice Output"
                    else:
                        dlv_name = dlv["id"]
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
        """Generate the JS transform code for the code node.

        Reads the spec to determine:
        - Which sources return flat arrays (classified by field sniffing)
        - Which POST sources need to be called inline after merge
        - How to build voice + HTML output
        """
        app_name = self.spec["app"]["name"]
        sources = self.spec.get("sources", [])

        # Find POST sources that need inline calls (they have a body config)
        post_sources = [s for s in sources if s.get("config", {}).get("method", "GET") != "GET"]

        # Build inline API call code for POST sources
        inline_calls = ""
        for ps in post_sources:
            cfg = ps.get("config", {})
            url = cfg.get("url", "")
            timeout = cfg.get("timeout", 60000)
            # Build the body from config, replacing template vars
            body_cfg = cfg.get("body", {})
            if body_cfg:
                inline_calls += f"""
const plan = await this.helpers.httpRequest({{
  method: 'POST',
  url: '{url}',
  body: {{ date: today, calendar_events, triaged_emails }},
  json: true,
  timeout: {timeout},
  headers: {{ 'Content-Type': 'application/json' }}
}});
"""
            else:
                inline_calls += f"""
const plan = await this.helpers.httpRequest({{
  method: 'POST',
  url: '{url}',
  body: {{ date: today }},
  json: true,
  timeout: {timeout},
  headers: {{ 'Content-Type': 'application/json' }}
}});
"""

        # Detect which sources are emails vs calendar from spec field hints
        email_source = next((s for s in sources if "triage" in s["id"] or "email" in s["id"]), None)
        cal_source = next((s for s in sources if "calendar" in s["id"] or "event" in s["id"]), None)

        # Determine field-sniffing logic from spec returns
        email_fields = ""
        cal_fields = ""
        if email_source:
            returns = email_source.get("returns", {})
            if returns.get("_type") == "flat_array":
                # Flat array — sniff by importance + sender
                email_fields = "j.importance && j.sender"
            else:
                email_fields = "j.importance && j.sender"
        if cal_source:
            returns = cal_source.get("returns", {})
            if returns.get("_type") == "flat_array":
                cal_fields = "j.summary && j.start && j.end"
            else:
                cal_fields = "j.summary && j.start && j.end"

        # Build delivery output code (subject, body HTML, voice text)
        deliveries = self.spec.get("delivery", [])
        has_email = any(d["type"] == "email" for d in deliveries)
        has_voice = any(d["type"] == "voice" for d in deliveries)

        delivery_code = ""
        return_fields = "triaged_emails, calendar_events, plan"

        if has_email:
            delivery_code += r"""
// Build email subject
const subject = `COOP Briefing \u2014 ${new Date().toLocaleDateString('en-US', {month:'short',day:'numeric'})}`;

// Build email HTML body
const prioritiesHtml = (plan.top_priorities || []).map(p => `<li>${p}</li>`).join('');
const blocksHtml = (plan.blocks || []).map(b =>
  `<tr><td style="padding:4px 8px;border-bottom:1px solid #eee">${b.start}\u2013${b.end}</td><td style="padding:4px 8px;border-bottom:1px solid #eee"><strong>${b.title}</strong><br><small>${b.notes||''}</small></td></tr>`
).join('');
const emailsHtml = triaged_emails.slice(0,10).map(e =>
  `<tr><td style="padding:4px 8px;border-bottom:1px solid #eee;text-transform:uppercase;font-size:11px">${e.importance}</td><td style="padding:4px 8px;border-bottom:1px solid #eee">${e.sender}</td><td style="padding:4px 8px;border-bottom:1px solid #eee">${e.subject}</td></tr>`
).join('');
const actionsHtml = (plan.email_actions || []).map(a => `<li>${a}</li>`).join('');
const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
const dayName = days[new Date().getDay()];

const body = `<h2>COOP MORNING BRIEFING</h2>
<p>${today} &middot; ${dayName.toUpperCase()}</p>
<h3>\u2709 INBOX</h3><p>${triaged_emails.length} messages</p>
<table>${emailsHtml}</table>
${actionsHtml ? `<h4>Actions</h4><ul>${actionsHtml}</ul>` : ''}
<h3>\ud83d\udcc5 SCHEDULE</h3>
<table>${blocksHtml}</table>
<h3>\ud83c\udfaf TOP PRIORITIES</h3>
<ul>${prioritiesHtml}</ul>
<p><em>${plan.summary || ''}</em></p>`;
"""
            return_fields += ", subject, body"

        if has_voice:
            delivery_code += r"""
// Build voice text (under 300 chars)
const topPri = (plan.top_priorities || []).slice(0,3).join('. ');
const numEmails = triaged_emails.length;
const critical = triaged_emails.filter(e => e.importance === 'critical').length;
const numBlocks = (plan.blocks || []).length;
let voice = `Good morning. ${numEmails} emails`;
if (critical > 0) voice += `, ${critical} critical`;
voice += `. ${numBlocks} blocks scheduled. Top priorities: ${topPri}.`;
if (voice.length > 300) voice = voice.substring(0, 297) + '...';
"""
            return_fields += ", voice"

        return f"""// ═══ FORGE-GENERATED TRANSFORM ═══
// App: {app_name}
// Generated: {datetime.now().isoformat()}
// Matched to Life Cockpit API response shapes

const items = $input.all();
const triaged_emails = [];
const calendar_events = [];

for (const item of items) {{
  const j = item.json;
  if ({email_fields}) {{
    triaged_emails.push(j);
  }} else if ({cal_fields}) {{
    calendar_events.push(j);
  }}
}}

const today = new Date().toISOString().split('T')[0];
{inline_calls}{delivery_code}
return [{{ json: {{ {return_fields} }} }}];"""

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

        # Delegate to integration-specific full-file generators
        if "gmail" in integrations:
            code = self._gen_gmail_route_file(service)
        elif "google_calendar" in integrations:
            code = self._gen_calendar_route_file(service)
        elif "anthropic" in integrations:
            code = self._gen_ai_route_file(service)
        elif "elevenlabs" in integrations:
            code = self._gen_voice_route_file(service)
        else:
            code = f'''"""
Route: {service["description"]}
Path: {path}
Generated by FORGE
"""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.{method}("{path}")
async def {module_name}():
    """
    {service["description"]}
    """
    try:
        # {logic}
        return {{"status": "ok"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''

        route_path = routes_dir / f"{module_name}.py"
        route_path.write_text(code)
        print(f"    ✓ backend/routes/{module_name}.py")

    def _gen_gmail_route_file(self, service: dict) -> str:
        path = service.get("path", "/api/triage/inbox")
        module_name = service["id"].replace("-", "_")
        logic = service.get("logic", "")
        return f'''"""
Route: {service["description"]}
Path: {path}
Generated by FORGE — matched to Life Cockpit API
"""

from fastapi import APIRouter, HTTPException
from services.google_auth import get_google_service

router = APIRouter()

IMPORTANCE_KEYWORDS = {{
    "critical": ["declined", "locked", "security alert", "fraud"],
    "high": ["urgent", "asap", "deadline", "action required", "verify", "@atu.edu"],
    "low": ["newsletter", "noreply", "marketing", "promo", "unsubscribe"],
}}


def score_importance(sender: str, subject: str, snippet: str) -> tuple[str, str]:
    text = f"{{sender}} {{subject}} {{snippet}}".lower()
    for level in ("critical", "high", "low"):
        for kw in IMPORTANCE_KEYWORDS[level]:
            if kw in text:
                return level, f"Matched keyword '{{kw}}' in {{level}} rules."
    return "medium", "No priority keywords matched."


def suggest_action(importance: str) -> str:
    return {{"critical": "address immediately", "high": "read and address",
            "low": "read when convenient"}}.get(importance, "read")


@router.get("{path}")
async def {module_name}():
    """
    {service["description"]}
    Returns flat array of TriagedEmail objects.
    """
    try:
        service = get_google_service("gmail", "v1")
        results = service.users().messages().list(
            userId="me", q="is:unread", maxResults=20
        ).execute()

        triaged = []
        for msg_meta in results.get("messages", []):
            msg = service.users().messages().get(
                userId="me", id=msg_meta["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()

            headers = {{h["name"]: h["value"] for h in msg.get("payload", {{}}).get("headers", [])}}
            sender = headers.get("From", "Unknown")
            subject = headers.get("Subject", "No subject")
            snippet = msg.get("snippet", "")
            importance, reason = score_importance(sender, subject, snippet)

            triaged.append({{
                "id": msg["id"],
                "thread_id": msg.get("threadId", msg["id"]),
                "subject": subject,
                "sender": sender,
                "snippet": snippet,
                "date": headers.get("Date", ""),
                "importance": importance,
                "reason": reason,
                "suggested_action": suggest_action(importance),
            }})

        return triaged
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''

    def _gen_calendar_route_file(self, service: dict) -> str:
        path = service.get("path", "/api/calendar/events")
        module_name = service["id"].replace("-", "_")
        return f'''"""
Route: {service["description"]}
Path: {path}
Generated by FORGE — matched to Life Cockpit API
"""

from fastapi import APIRouter, HTTPException
from services.google_auth import get_google_service

router = APIRouter()


@router.get("{path}")
async def {module_name}():
    """
    {service["description"]}
    Returns flat array of CalendarEvent objects.
    """
    try:
        from datetime import datetime

        service = get_google_service("calendar", "v3")

        now = datetime.utcnow()
        start = now.replace(hour=0, minute=0, second=0).isoformat() + "Z"
        end = now.replace(hour=23, minute=59, second=59).isoformat() + "Z"

        cal_list = service.calendarList().list().execute()
        all_events = []

        for cal in cal_list.get("items", []):
            cal_id = cal["id"]
            events_result = service.events().list(
                calendarId=cal_id,
                timeMin=start, timeMax=end,
                singleEvents=True, orderBy="startTime",
            ).execute()

            for event in events_result.get("items", []):
                start_obj = event.get("start", {{}})
                end_obj = event.get("end", {{}})
                is_all_day = "date" in start_obj and "dateTime" not in start_obj

                all_events.append({{
                    "id": event.get("id", ""),
                    "summary": event.get("summary", "Untitled"),
                    "start": start_obj.get("dateTime", start_obj.get("date", "")),
                    "end": end_obj.get("dateTime", end_obj.get("date", "")),
                    "location": event.get("location", ""),
                    "description": event.get("description", ""),
                    "all_day": is_all_day,
                }})

        all_events.sort(key=lambda e: e.get("start", ""))
        return all_events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''

    def _gen_ai_route_file(self, service: dict) -> str:
        path = service.get("path", "/api/planner/generate")
        module_name = service["id"].replace("-", "_")
        return f'''"""
Route: {service["description"]}
Path: {path}
Generated by FORGE — matched to Life Cockpit API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import anthropic
import json
import os
import re

router = APIRouter()


class CalendarEvent(BaseModel):
    id: str
    summary: str
    start: str
    end: str
    location: str = ""
    description: str = ""
    all_day: bool = False


class TriagedEmail(BaseModel):
    id: str
    thread_id: str
    subject: str
    sender: str
    snippet: str
    date: str
    importance: str
    reason: str
    suggested_action: str


class DayPlanRequest(BaseModel):
    date: str
    calendar_events: list[CalendarEvent] = []
    triaged_emails: list[TriagedEmail] = []
    preferences: str = ""


class TimeBlock(BaseModel):
    start: str
    end: str
    title: str
    category: str
    notes: str = ""


class DayPlan(BaseModel):
    date: str
    blocks: list[TimeBlock]
    top_priorities: list[str]
    email_actions: list[str]
    summary: str


@router.post("{path}", response_model=DayPlan)
async def {module_name}(request: DayPlanRequest):
    """
    {service["description"]}
    Accepts DayPlanRequest, returns DayPlan.
    """
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        prompts_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "layer1-directive", "system-prompts.json"
        )
        system_prompt = "You are a daily planning assistant. Generate a structured day plan."
        try:
            with open(prompts_path) as f:
                prompts = json.load(f)
                if "{service["id"]}" in prompts:
                    system_prompt = prompts["{service["id"]}"]["system"]
        except FileNotFoundError:
            pass

        email_summary = "\\n".join(
            f"- [{{e.importance.upper()}}] {{e.sender}}: {{e.subject}}"
            for e in request.triaged_emails[:10]
        ) or "No emails."

        cal_summary = "\\n".join(
            f"- {{e.start}} — {{e.summary}}"
            for e in request.calendar_events[:10]
        ) or "No events."

        user_message = f"""Date: {{request.date}}

Emails:
{{email_summary}}

Calendar:
{{cal_summary}}

{{f"Preferences: {{request.preferences}}" if request.preferences else ""}}

Generate a structured daily plan as JSON with this exact schema:
{{{{"date": "{{request.date}}", "blocks": [{{{{"start": "HH:MM", "end": "HH:MM", "title": "...", "category": "...", "notes": "..."}}}}], "top_priorities": ["..."], "email_actions": ["..."], "summary": "..."}}}}
Categories: deep_work, email, admin, habit, break. Return ONLY valid JSON."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=[{{"role": "user", "content": user_message}}],
        )

        text = response.content[0].text
        json_match = re.search(r"\\{{.*\\}}", text, re.DOTALL)
        if json_match:
            plan_data = json.loads(json_match.group())
        else:
            plan_data = {{
                "date": request.date, "blocks": [],
                "top_priorities": [text.strip()[:200]],
                "email_actions": [], "summary": "Could not parse structured plan.",
            }}

        plan_data["date"] = request.date
        return DayPlan(**plan_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''

    def _gen_voice_route_file(self, service: dict) -> str:
        path = service.get("path", "/api/voice/speak")
        module_name = service["id"].replace("-", "_")
        return f'''"""
Route: {service["description"]}
Path: {path}
Generated by FORGE — matched to Life Cockpit API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import httpx
import os

router = APIRouter()


class SpeakRequest(BaseModel):
    text: str


@router.post("{path}")
async def {module_name}(request: SpeakRequest):
    """
    {service["description"]}
    Accepts {{ text: string }}, returns mp3 audio stream.
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY not set")

    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{{voice_id}}/stream",
                headers={{"xi-api-key": api_key}},
                json={{
                    "text": request.text,
                    "model_id": "eleven_turbo_v2",
                    "voice_settings": {{"stability": 0.5, "similarity_boost": 0.75}},
                }},
                timeout=60.0,
            )

            if response.status_code != 200:
                raise HTTPException(status_code=502, detail="ElevenLabs API error")

            return StreamingResponse(
                iter([response.content]),
                media_type="audio/mpeg",
                headers={{"Content-Disposition": "inline; filename=briefing.mp3"}},
            )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=str(e))
'''

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
# LAYER 4: SCAFFOLD GENERATOR
# ═══════════════════════════════════════════════════════════════

class ScaffoldGenerator:
    """
    Layer 4 — Agent framework scaffold.
    Generates: guardrails, confidence scoring, audit logging, cost tracking,
    health checks, ROI tracking, feature flags, tests, project docs.
    Opt-in: only runs when spec contains a 'scaffold:' section or --scaffold flag.
    """

    def __init__(self, spec: dict, output_dir: Path):
        self.spec = spec
        self.dir = output_dir / "scaffold"
        self.app_name = spec["app"].get("name", "FORGE Project")
        self.app_id = spec["app"].get("id", "forge-project")
        self.description = spec["app"].get("description", "A Brave Alpaca AI agent built with FORGE.")

    def generate(self):
        # Create directory structure
        dirs = [
            "agent/directive", "agent/orchestration", "agent/execution",
            "business/client_configs", "monitoring", "tests",
        ]
        for d in dirs:
            (self.dir / d).mkdir(parents=True, exist_ok=True)

        # Generate all scaffold files
        files = {
            "agent/directive/guardrails.py":     self._gen_guardrails(),
            "agent/directive/system_prompt.md":  self._gen_system_prompt(),
            "agent/directive/__init__.py":       "",
            "agent/orchestration/confidence.py": self._gen_confidence(),
            "agent/orchestration/__init__.py":   "",
            "agent/execution/audit_log.py":      self._gen_audit_log(),
            "agent/execution/__init__.py":       "",
            "agent/__init__.py":                 "",
            "monitoring/cost_tracker.py":        self._gen_cost_tracker(),
            "monitoring/health_check.py":        self._gen_health_check(),
            "monitoring/__init__.py":            "",
            "business/roi_tracker.py":           self._gen_roi_tracker(),
            "business/feature_flags.py":         self._gen_feature_flags(),
            "business/__init__.py":              "",
            "tests/conftest.py":                 self._gen_conftest(),
            "tests/test_guardrails.py":          self._gen_test_guardrails(),
            "tests/test_connections.py":         self._gen_test_connections(),
            "tests/test_data_flow.py":           self._gen_test_data_flow(),
            "tests/__init__.py":                 "",
            "CLAUDE.md":                         self._gen_claude_md(),
            "ARCHITECTURE.md":                   self._gen_architecture_md(),
            "Makefile":                          self._gen_makefile(),
            "config.yaml":                       self._gen_config_yaml(),
        }

        for filepath, content in files.items():
            full_path = self.dir / filepath
            full_path.write_text(content)

        print(f"    + {len(files)} scaffold files")

    # ── Template Methods ──────────────────────────────────────

    def _gen_guardrails(self) -> str:
        return '''"""
Guardrails — Hard safety rules enforced in code.
These are NOT just suggestions in a prompt.
The code itself refuses unsafe actions.
"""

# ── Constants ─────────────────────────────────────────────
MAX_EMAILS_PER_SESSION = 50
MAX_TOOL_CALLS_PER_TURN = 10
MAX_REPLY_LENGTH = 2000

SENSITIVE_KEYWORDS = [
    "ssn", "social security", "bank account", "routing number",
    "password", "credit card", "cvv", "diagnosis",
    "prescription", "medical record"
]

ACTIONS_REQUIRING_CONFIRMATION = {
    "send_email", "update_calendar", "delete_record",
    "send_notification", "modify_database"
}


# ── Rule Functions ────────────────────────────────────────

def check_email_count(count: int) -> tuple[bool, str]:
    """Is this within the safe email limit?"""
    if count > MAX_EMAILS_PER_SESSION:
        return False, f"Too many emails ({count}). Max is {MAX_EMAILS_PER_SESSION}."
    return True, "ok"


def check_reply_length(text: str) -> tuple[bool, str]:
    """Is this reply a reasonable length?"""
    if len(text) > MAX_REPLY_LENGTH:
        return False, f"Reply too long ({len(text)} chars). Max is {MAX_REPLY_LENGTH}."
    return True, "ok"


def check_sensitive_content(text: str) -> tuple[bool, list]:
    """Does this text contain sensitive information?"""
    text_lower = text.lower()
    found = [kw for kw in SENSITIVE_KEYWORDS if kw in text_lower]
    if found:
        return True, found
    return False, []


def require_confirmation(action: str, confirmation_token: str = None) -> tuple[bool, str]:
    """
    Does this action need user confirmation?
    Returns (is_allowed, reason).
    """
    if action not in ACTIONS_REQUIRING_CONFIRMATION:
        return True, "ok"

    if not confirmation_token:
        return False, f"Action '{action}' requires explicit user confirmation. Get a confirmation_token first."

    # In production, validate the token here
    return True, "ok"


def dry_run_check(dry_run_mode: bool, action: str) -> tuple[bool, str]:
    """If dry_run_mode is on, block all write actions."""
    write_actions = {"send_email", "update_calendar", "delete_record", "modify_database"}
    if dry_run_mode and action in write_actions:
        return False, f"DRY RUN: Would have executed '{action}' but dry_run_mode is ON."
    return True, "ok"


def check_tool_call_count(count: int) -> tuple[bool, str]:
    """Prevent runaway agent loops."""
    if count >= MAX_TOOL_CALLS_PER_TURN:
        return False, f"Too many tool calls ({count}). Max per turn is {MAX_TOOL_CALLS_PER_TURN}."
    return True, "ok"
'''

    def _gen_system_prompt(self) -> str:
        return f"""# Identity
You are {self.app_name}, an AI assistant built by Brave Alpaca.
{self.description}

# Personality
You are efficient, clear, and warm. You never waste words.
You are calm confidence. Never a hype man. Never cheesy.

# Core Rules
- Always confirm before taking irreversible actions
- If confidence is below 60%, ask for clarification
- Flag sensitive content for human review
- Never fabricate facts or invent data

# Output Format
- Always return structured JSON for data operations
- Use plain English for user-facing responses
- Keep summaries under 20 words unless asked for more
"""

    def _gen_confidence(self) -> str:
        return '''"""
Confidence Scoring — The agent rates its own certainty before acting.

How it works:
  >= 0.85  -> Execute automatically. The agent is sure.
  0.60-0.84 -> Flag for review. Suggest but ask.
  < 0.60  -> Stop. Ask the user. Don't guess.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ConfidenceResult:
    score: float          # 0.0 to 1.0
    action: str           # "execute", "review", "stop"
    reason: str           # Plain English explanation
    suggestion: Optional[str] = None  # What to do if action is "stop"


AUTO_EXECUTE_THRESHOLD = 0.85
FLAG_FOR_REVIEW_THRESHOLD = 0.60


def score_action(
    intent_clarity: float,      # How clear was the user's request? (0-1)
    data_completeness: float,   # Do we have all needed data? (0-1)
    risk_level: float,          # How bad if wrong? (0=low, 1=high)
    past_accuracy: float = 0.9  # Historical accuracy for this action type
) -> ConfidenceResult:
    """
    Calculate confidence score for an agent action.

    Example:
        result = score_action(
            intent_clarity=0.95,    # User was very clear
            data_completeness=0.80, # Missing one field
            risk_level=0.30,        # Medium stakes
        )
        # result.score = ~0.78 -> "review"
    """
    # Weighted formula -- risk is most important
    raw_score = (
        intent_clarity * 0.30 +
        data_completeness * 0.30 +
        (1.0 - risk_level) * 0.25 +
        past_accuracy * 0.15
    )

    score = round(min(max(raw_score, 0.0), 1.0), 3)

    if score >= AUTO_EXECUTE_THRESHOLD:
        return ConfidenceResult(
            score=score,
            action="execute",
            reason=f"High confidence ({score:.0%}). Proceeding automatically."
        )
    elif score >= FLAG_FOR_REVIEW_THRESHOLD:
        return ConfidenceResult(
            score=score,
            action="review",
            reason=f"Medium confidence ({score:.0%}). Please review before I proceed.",
            suggestion="Confirm this is what you want, or give me more detail."
        )
    else:
        return ConfidenceResult(
            score=score,
            action="stop",
            reason=f"Low confidence ({score:.0%}). I'm not sure enough to act.",
            suggestion="I need more information. Can you clarify your intent?"
        )


def is_high_risk(action: str) -> float:
    """Returns a risk level (0-1) for common actions."""
    HIGH_RISK   = {"send_email", "delete_record", "modify_database"}
    MEDIUM_RISK = {"update_calendar", "send_notification", "create_record"}
    LOW_RISK    = {"fetch_emails", "read_calendar", "search_data", "generate_report"}

    if action in HIGH_RISK:   return 0.80
    if action in MEDIUM_RISK: return 0.50
    if action in LOW_RISK:    return 0.10
    return 0.50  # Unknown action = medium risk
'''

    def _gen_audit_log(self) -> str:
        return '''"""
Audit Log — Every agent decision in plain English.

When something goes wrong (and eventually something will),
this log tells you exactly what happened and why.
"""

import json
import os
from datetime import datetime
from pathlib import Path


LOG_FILE = "monitoring/audit_log.jsonl"


def log_decision(
    action: str,
    inputs: dict,
    output: dict,
    confidence_score: float,
    agent_name: str = "coordinator",
    user_confirmed: bool = False,
    dry_run: bool = False,
    notes: str = ""
):
    """
    Write one decision to the audit log.
    Each line is a complete JSON record (JSONL format).
    """
    Path("monitoring").mkdir(exist_ok=True)

    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent_name,
        "action": action,
        "confidence": confidence_score,
        "user_confirmed": user_confirmed,
        "dry_run": dry_run,
        "inputs_summary": _summarize(inputs),
        "output_summary": _summarize(output),
        "notes": notes,
        "plain_english": _to_plain_english(
            agent_name, action, confidence_score,
            user_confirmed, dry_run, output
        )
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\\n")


def _to_plain_english(agent, action, confidence, confirmed, dry_run, output):
    """Convert a decision to a sentence a human can read."""
    status = "DRY RUN --" if dry_run else ""
    confirmed_str = "after user confirmed" if confirmed else "automatically"
    success = "succeeded" if output.get("success", True) else "failed"
    return (
        f"{status} {agent.title()} {action.replace('_', ' ')} "
        f"{confirmed_str} with {confidence:.0%} confidence. "
        f"Result: {success}."
    ).strip()


def _summarize(data: dict) -> dict:
    """Keep only safe, short summary fields for the log."""
    SKIP_KEYS = {"password", "token", "secret", "api_key", "authorization"}
    return {
        k: (str(v)[:100] if isinstance(v, str) else v)
        for k, v in data.items()
        if k.lower() not in SKIP_KEYS
    }


def get_recent_decisions(limit: int = 50) -> list:
    """Read the last N decisions from the log."""
    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()
        recent = lines[-limit:]
        return [json.loads(line) for line in recent]
    except FileNotFoundError:
        return []


def get_plain_english_summary(limit: int = 10) -> str:
    """Returns a readable summary of recent decisions."""
    decisions = get_recent_decisions(limit)
    if not decisions:
        return "No decisions logged yet."
    lines = [d["plain_english"] for d in decisions]
    return "\\n".join(f"  {i+1}. {line}" for i, line in enumerate(lines))
'''

    def _gen_cost_tracker(self) -> str:
        return '''"""
Cost Tracker — Logs every Claude API call and its cost.
Runs in the background. Zero impact on performance.

Pricing (update these if Anthropic changes rates):
  Haiku 4.5:   $0.80 input / $4.00 output per million tokens
  Sonnet 4:    $3.00 input / $15.00 output per million tokens
  Opus 4.6:   $15.00 input / $75.00 output per million tokens
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

LOG_FILE = "monitoring/costs.json"

# ── Model pricing (USD per million tokens) ────────────────
PRICING = {
    "claude-haiku-4-5-20251001": {
        "input_per_mtok":  0.80,
        "output_per_mtok": 4.00,
        "label": "Haiku 4.5 (Fast)"
    },
    "claude-sonnet-4-20250514": {
        "input_per_mtok":  3.00,
        "output_per_mtok": 15.00,
        "label": "Sonnet 4 (Balanced)"
    },
    "claude-opus-4-6": {
        "input_per_mtok":  15.00,
        "output_per_mtok": 75.00,
        "label": "Opus 4.6 (Powerful)"
    },
}

DAILY_LIMIT = float(os.getenv("COST_DAILY_LIMIT", "5.00"))


def _load() -> dict:
    Path("monitoring").mkdir(exist_ok=True)
    try:
        with open(LOG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"total_usd": 0.0, "calls": [], "daily": {}}


def _save(data: dict):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def log_call(
    model: str,
    input_tokens: int,
    output_tokens: int,
    purpose: str = "",
    agent: str = ""
) -> float:
    """
    Log one API call and return its cost in USD.
    Call this after every successful Claude API response.
    """
    pricing = PRICING.get(model, PRICING["claude-sonnet-4-20250514"])
    cost = (
        (input_tokens  / 1_000_000) * pricing["input_per_mtok"] +
        (output_tokens / 1_000_000) * pricing["output_per_mtok"]
    )
    cost = round(cost, 6)

    data = _load()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    data["total_usd"] = round(data.get("total_usd", 0) + cost, 6)
    data["last_updated"] = datetime.utcnow().isoformat()

    # Daily rollup
    if today not in data["daily"]:
        data["daily"][today] = {"total_usd": 0.0, "calls": 0}
    data["daily"][today]["total_usd"] = round(
        data["daily"][today]["total_usd"] + cost, 6
    )
    data["daily"][today]["calls"] += 1

    # Call log (keep last 1000)
    data["calls"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "model": model,
        "model_label": pricing["label"],
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost,
        "purpose": purpose,
        "agent": agent
    })
    data["calls"] = data["calls"][-1000:]

    _save(data)

    # Alert if over daily limit
    daily_spend = data["daily"][today]["total_usd"]
    if daily_spend >= DAILY_LIMIT:
        print(f"\\n  COST ALERT: Daily spend ${daily_spend:.4f} exceeds limit ${DAILY_LIMIT:.2f}\\n")
    elif daily_spend >= DAILY_LIMIT * 0.80:
        print(f"\\n  COST WARNING: At {daily_spend/DAILY_LIMIT:.0%} of daily limit (${daily_spend:.4f})\\n")

    return cost


def get_report() -> dict:
    """Returns a full cost analysis."""
    data = _load()
    calls = data.get("calls", [])
    today = datetime.utcnow().strftime("%Y-%m-%d")

    model_spend = {}
    for call in calls:
        m = call.get("model_label", "unknown")
        if m not in model_spend:
            model_spend[m] = {"cost": 0, "calls": 0}
        model_spend[m]["cost"]  += call["cost_usd"]
        model_spend[m]["calls"] += 1

    return {
        "total_usd":       round(data.get("total_usd", 0), 4),
        "today_usd":       round(data.get("daily", {}).get(today, {}).get("total_usd", 0), 4),
        "daily_limit":     DAILY_LIMIT,
        "total_calls":     len(calls),
        "model_breakdown": model_spend,
    }


# ── CLI report ────────────────────────────────────────────
if __name__ == "__main__":
    if "--report" in sys.argv:
        report = get_report()
        print("\\n" + "=" * 50)
        print("  COST REPORT")
        print("=" * 50)
        print(f"  Total spend:   ${report[\'total_usd\']:.4f}")
        print(f"  Today:         ${report[\'today_usd\']:.4f} / ${report[\'daily_limit\']:.2f} limit")
        print(f"  Total API calls: {report[\'total_calls\']}")
        print("\\n  By Model:")
        for model, stats in report["model_breakdown"].items():
            print(f"    {model}: ${stats[\'cost\']:.4f} ({stats[\'calls\']} calls)")
        print()
'''

    def _gen_health_check(self) -> str:
        project_name = self.app_name
        return f'''"""
Health Check — Verifies everything is working in ~30 seconds.
Run this: python monitoring/health_check.py
Or:       make check
"""

import os
import sys
from pathlib import Path
from datetime import datetime

GREEN  = "\\033[92m"
RED    = "\\033[91m"
YELLOW = "\\033[93m"
RESET  = "\\033[0m"

REQUIRED_FILES = [
    "CLAUDE.md", "ARCHITECTURE.md", "config.yaml",
    "Makefile",
    "agent/directive/system_prompt.md",
    "agent/directive/guardrails.py",
    "agent/orchestration/confidence.py",
    "agent/execution/audit_log.py",
    "monitoring/cost_tracker.py",
]

REQUIRED_ENV_VARS = [
    "ANTHROPIC_API_KEY",
]


def check(name, passed, detail=""):
    icon = f"{{GREEN}}+{{RESET}}" if passed else f"{{RED}}x{{RESET}}"
    suffix = f" -- {{YELLOW}}{{detail}}{{RESET}}" if detail else ""
    print(f"  {{icon}} {{name}}{{suffix}}")
    return passed


def run_health_check():
    print(f"\\n{project_name.upper()} -- Health Check")
    print(f"{{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
    print("-" * 40)

    passed = 0
    total = 0

    # 1. File structure
    print("\\n  File Structure")
    for filepath in REQUIRED_FILES:
        ok = Path(filepath).exists()
        check(filepath, ok, "MISSING" if not ok else "")
        total += 1
        if ok: passed += 1

    # 2. Environment variables
    print("\\n  Environment Variables")
    for var in REQUIRED_ENV_VARS:
        val = os.getenv(var, "")
        ok = bool(val) and val != "your-key-here"
        check(var, ok, "not set" if not ok else "set")
        total += 1
        if ok: passed += 1

    # 3. Config
    print("\\n  Configuration")
    try:
        import yaml
        with open("config.yaml") as f:
            cfg = yaml.safe_load(f)
        check("config.yaml is valid YAML", True)
        check("models defined", "models" in cfg)
        total += 2
        passed += 2
    except Exception as e:
        check("config.yaml", False, str(e))
        total += 1

    # Summary
    pct = (passed / total * 100) if total else 0
    color = GREEN if pct == 100 else YELLOW if pct >= 75 else RED
    print(f"\\n{{color}}Results: {{passed}}/{{total}} checks passed ({{pct:.0f}}%){{RESET}}")

    if passed < total:
        print(f"\\n{{YELLOW}}Fix the red items above, then run: make check{{RESET}}")
    else:
        print(f"\\n{{GREEN}}Everything looks good. Ready to build!{{RESET}}")

    print()
    return passed == total


if __name__ == "__main__":
    success = run_health_check()
    sys.exit(0 if success else 1)
'''

    def _gen_roi_tracker(self) -> str:
        return '''"""
ROI Tracker — Logs every task the agent completes.
At month-end, your client sees exactly what the agent did for them.
"""

import json
from datetime import datetime
from pathlib import Path

LOG_FILE = "monitoring/roi_log.json"
HOURS_SAVED = {
    "send_email":        0.08,   # ~5 min
    "draft_email":       0.17,   # ~10 min
    "summarize_emails":  0.25,   # ~15 min
    "reschedule_meeting":0.33,   # ~20 min
    "triage_inbox":      0.50,   # ~30 min
    "build_day_plan":    0.50,   # ~30 min
    "meeting_brief":     0.25,   # ~15 min
    "add_task":          0.03,   # ~2 min
    "log_habit":         0.02,   # ~1 min
    "generate_report":   1.00,   # ~60 min
}
HOURLY_RATE = float(60)  # Assumed value of user time, USD/hr


def _load():
    Path("monitoring").mkdir(exist_ok=True)
    try:
        with open(LOG_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"tasks": [], "totals": {"count": 0, "hours_saved": 0.0, "value_usd": 0.0}}


def _save(data):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def log_task(task_type: str, detail: str = ""):
    """Log one completed task."""
    data = _load()
    hours = HOURS_SAVED.get(task_type, 0.10)
    value = round(hours * HOURLY_RATE, 2)

    data["tasks"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "type": task_type,
        "detail": detail,
        "hours_saved": hours,
        "value_usd": value
    })
    data["totals"]["count"]       += 1
    data["totals"]["hours_saved"] = round(data["totals"]["hours_saved"] + hours, 2)
    data["totals"]["value_usd"]   = round(data["totals"]["value_usd"]   + value, 2)

    _save(data)
    return {"hours_saved": hours, "value_usd": value}


def get_monthly_summary() -> dict:
    """Returns a client-ready ROI summary for the current month."""
    data = _load()
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)

    monthly_tasks = [
        t for t in data["tasks"]
        if datetime.fromisoformat(t["timestamp"]) >= month_start
    ]

    by_type = {}
    for task in monthly_tasks:
        t = task["type"]
        if t not in by_type:
            by_type[t] = {"count": 0, "hours": 0.0, "value": 0.0}
        by_type[t]["count"]  += 1
        by_type[t]["hours"]  += task["hours_saved"]
        by_type[t]["value"]  += task["value_usd"]

    total_hours = sum(t["hours_saved"] for t in monthly_tasks)
    total_value = sum(t["value_usd"]   for t in monthly_tasks)

    return {
        "period": month_start.strftime("%B %Y"),
        "total_tasks": len(monthly_tasks),
        "total_hours_saved": round(total_hours, 1),
        "total_value_usd": round(total_value, 2),
        "breakdown": by_type
    }
'''

    def _gen_feature_flags(self) -> str:
        return '''"""
Feature Flags — Turn features on and off per client.
Ship one codebase. Customize for every customer.

Usage:
    from business.feature_flags import flags
    if flags.is_enabled("voice_mode"):
        # do voice stuff
"""

import os
import yaml
from pathlib import Path


# Default flags -- all clients get these unless overridden
DEFAULT_FLAGS = {
    "voice_mode":         False,
    "email_send":         True,
    "calendar_write":     True,
    "habit_tracking":     True,
    "roi_dashboard":      True,
    "cost_dashboard":     True,
    "dry_run_mode":       False,
    "white_label":        False,
    "multi_user":         False,
    "advanced_analytics": False,
}

# Tier overrides
TIER_FLAGS = {
    "free": {
        "voice_mode": False,
        "email_send": False,
        "roi_dashboard": False,
        "cost_dashboard": False,
    },
    "pro": {
        "voice_mode": True,
        "email_send": True,
        "roi_dashboard": True,
        "cost_dashboard": True,
    },
    "business": {
        **{k: True for k in DEFAULT_FLAGS},
        "dry_run_mode": False,
    }
}


class FeatureFlags:
    def __init__(self):
        self._flags = {**DEFAULT_FLAGS}
        self._load_client_overrides()

    def _load_client_overrides(self):
        """Apply tier and client-specific overrides."""
        tier = os.getenv("CLIENT_TIER", "pro")
        if tier in TIER_FLAGS:
            self._flags.update(TIER_FLAGS[tier])

        client_config = Path("business/client_configs") / f"{os.getenv(\'CLIENT_ID\', \'default\')}.yaml"
        if client_config.exists():
            with open(client_config) as f:
                overrides = yaml.safe_load(f).get("feature_flags", {})
                self._flags.update(overrides)

    def is_enabled(self, flag: str) -> bool:
        return self._flags.get(flag, False)

    def get_all(self) -> dict:
        return {**self._flags}

    def override(self, flag: str, value: bool):
        """Override a flag at runtime (useful for testing)."""
        self._flags[flag] = value


# Singleton instance
flags = FeatureFlags()
'''

    def _gen_conftest(self) -> str:
        return '''"""
Pytest Configuration + Shared Fixtures
These are available in ALL test files automatically.
"""

import pytest
import os

# ── Test environment setup ────────────────────────────────
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-real")
os.environ.setdefault("ENVIRONMENT", "test")


# ── Shared mock data ──────────────────────────────────────
@pytest.fixture
def mock_email():
    return {
        "id": "test-email-001",
        "thread_id": "thread-001",
        "from": "client@example.com",
        "subject": "Quick question",
        "snippet": "Hey, can you check on this?",
        "date": "2026-02-21T09:00:00Z"
    }

@pytest.fixture
def mock_emails(mock_email):
    return [mock_email, {**mock_email, "id": "test-email-002"}]

@pytest.fixture
def mock_calendar_event():
    return {
        "id": "event-001",
        "summary": "Design Review with Sarah",
        "start": {"dateTime": "2026-02-21T14:00:00Z"},
        "end":   {"dateTime": "2026-02-21T14:30:00Z"},
        "attendees": [{"email": "sarah@example.com"}],
        "location": ""
    }

@pytest.fixture
def mock_config():
    return {
        "agent": {"name": "TestAgent", "environment": "test"},
        "models": {
            "fast":    "claude-haiku-4-5-20251001",
            "default": "claude-sonnet-4-20250514",
        },
        "confidence": {"auto_execute": 0.85, "flag_for_review": 0.60},
        "guardrails": {"max_emails_per_session": 50}
    }
'''

    def _gen_test_guardrails(self) -> str:
        return '''"""
Test: Guardrails
Verifies that hard safety rules actually work.
Run: make test-guardrails
"""

import pytest
import sys
sys.path.insert(0, ".")


def test_send_email_requires_confirmation():
    """send_email must fail without a confirmation token."""
    from agent.directive.guardrails import require_confirmation
    allowed, reason = require_confirmation("send_email", confirmation_token=None)
    assert not allowed, "send_email should be blocked without confirmation_token"
    assert "confirmation" in reason.lower()


def test_send_email_passes_with_token():
    """send_email should work when confirmation is provided."""
    from agent.directive.guardrails import require_confirmation
    allowed, reason = require_confirmation("send_email", confirmation_token="user-said-yes")
    assert allowed, f"send_email with token should be allowed, got: {reason}"


def test_low_risk_action_needs_no_confirmation():
    """Reading data should never require confirmation."""
    from agent.directive.guardrails import require_confirmation
    allowed, reason = require_confirmation("fetch_emails", confirmation_token=None)
    assert allowed, "fetch_emails should not require confirmation"


def test_sensitive_content_flagged():
    """Text with sensitive keywords should be caught."""
    from agent.directive.guardrails import check_sensitive_content
    found, keywords = check_sensitive_content("Here is my social security number: 123-45-6789")
    assert found, "Should have flagged sensitive content"
    assert len(keywords) > 0


def test_clean_content_passes():
    """Normal text should pass the sensitive content check."""
    from agent.directive.guardrails import check_sensitive_content
    found, keywords = check_sensitive_content("Please schedule a meeting for Tuesday at 2pm")
    assert not found, f"Should not flag clean content, but found: {keywords}"


def test_email_count_limit():
    """Processing more than 50 emails at once should be blocked."""
    from agent.directive.guardrails import check_email_count
    ok, msg = check_email_count(51)
    assert not ok, "Should block over 50 emails"


def test_confidence_auto_execute():
    """High confidence actions should auto-execute."""
    from agent.orchestration.confidence import score_action
    result = score_action(
        intent_clarity=0.95,
        data_completeness=0.95,
        risk_level=0.10
    )
    assert result.action == "execute", f"Expected execute, got {result.action} (score: {result.score})"


def test_confidence_low_stops():
    """Low confidence should stop and ask the user."""
    from agent.orchestration.confidence import score_action
    result = score_action(
        intent_clarity=0.30,
        data_completeness=0.40,
        risk_level=0.90
    )
    assert result.action == "stop", f"Expected stop, got {result.action} (score: {result.score})"
'''

    def _gen_test_connections(self) -> str:
        return '''"""
Test: API Connections
Verifies every external service can be reached.
Run: make test-connections
"""

import pytest
import os


def test_anthropic_api_key_is_set():
    """The most important check -- no key = nothing works."""
    key = os.getenv("ANTHROPIC_API_KEY", "")
    assert key, "ANTHROPIC_API_KEY is not set in .env"
    assert key != "sk-ant-your-key-here", "ANTHROPIC_API_KEY is still the placeholder value"


def test_anthropic_client_can_be_created():
    """Can we create an Anthropic client without errors?"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        assert client is not None
    except ImportError:
        pytest.skip("anthropic package not installed")


@pytest.mark.skipif(not os.getenv("GOOGLE_CLIENT_ID"), reason="Google not configured")
def test_google_credentials_present():
    """Are Google OAuth credentials available?"""
    assert os.getenv("GOOGLE_CLIENT_ID"), "GOOGLE_CLIENT_ID not set"
    assert os.getenv("GOOGLE_CLIENT_SECRET"), "GOOGLE_CLIENT_SECRET not set"


def test_config_loads():
    """Can we load the config file without errors?"""
    try:
        import yaml
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
        assert "models" in config, "config.yaml missing 'models' section"
        assert "agent" in config, "config.yaml missing 'agent' section"
    except FileNotFoundError:
        pytest.fail("config.yaml not found")
    except Exception as e:
        pytest.fail(f"config.yaml has an error: {e}")
'''

    def _gen_test_data_flow(self) -> str:
        return '''"""
Test: Data Flow
Verifies data moves correctly through all three layers.
Uses mock data -- no real API calls.
Run: make test-flow
"""

import pytest
import json


MOCK_EMAIL = {
    "id": "test-001",
    "from": "client@example.com",
    "subject": "Quick question about the proposal",
    "snippet": "Hey, just wanted to check on the timeline...",
    "date": "2026-02-21T09:00:00Z"
}

MOCK_EMAILS = [MOCK_EMAIL] * 3


def test_guardrails_accept_valid_email():
    """A clean email passes all guardrail checks."""
    from agent.directive.guardrails import (
        check_email_count, check_sensitive_content, check_reply_length
    )
    ok, _ = check_email_count(len(MOCK_EMAILS))
    assert ok

    sensitive, _ = check_sensitive_content(MOCK_EMAIL["subject"])
    assert not sensitive

    test_reply = "Thanks for reaching out! I'll have an update for you by end of day."
    ok, _ = check_reply_length(test_reply)
    assert ok


def test_confidence_scores_are_bounded():
    """Confidence scores must always be between 0 and 1."""
    from agent.orchestration.confidence import score_action
    for clarity in [0.0, 0.5, 1.0]:
        for completeness in [0.0, 0.5, 1.0]:
            for risk in [0.0, 0.5, 1.0]:
                result = score_action(clarity, completeness, risk)
                assert 0.0 <= result.score <= 1.0
                assert result.action in ["execute", "review", "stop"]


def test_audit_log_writes():
    """Audit log records a decision without errors."""
    import sys, os, tempfile
    sys.path.insert(0, ".")
    try:
        from agent.execution.audit_log import log_decision, get_recent_decisions
        import agent.execution.audit_log as al
        original = al.LOG_FILE
        al.LOG_FILE = f"{tempfile.gettempdir()}/test_audit.jsonl"

        log_decision(
            action="fetch_emails",
            inputs={"max_results": 25},
            output={"count": 3},
            confidence_score=0.92,
            agent_name="inbox_agent"
        )

        decisions = get_recent_decisions(1)
        assert len(decisions) == 1
        assert decisions[0]["action"] == "fetch_emails"
        assert "plain_english" in decisions[0]

        al.LOG_FILE = original
        os.remove(f"{tempfile.gettempdir()}/test_audit.jsonl")
    except ImportError:
        pytest.skip("audit_log not built yet")
'''

    def _gen_claude_md(self) -> str:
        return f"""# {self.app_name.upper()} -- FORGE Project
# Claude Code: Read this entire file before writing a single line of code.

## What This Project Does
{self.description}

---

## Project File Map
```
{self.app_id}/
+-- CLAUDE.md              <-- You are here
+-- ARCHITECTURE.md        <-- Visual system map
+-- config.yaml            <-- All settings in one place
+-- Makefile               <-- Build/test/check commands
|
+-- agent/
|   +-- directive/
|   |   +-- system_prompt.md    <-- Agent personality + rules
|   |   +-- guardrails.py       <-- Hard safety rules (code-enforced)
|   +-- orchestration/
|   |   +-- confidence.py       <-- Rates how sure the agent is
|   +-- execution/
|       +-- audit_log.py        <-- Plain-English decision log
|
+-- business/
|   +-- roi_tracker.py      <-- Logs every task completed
|   +-- feature_flags.py    <-- Turn features on/off per client
|
+-- monitoring/
|   +-- cost_tracker.py     <-- Logs every API call + cost
|   +-- health_check.py     <-- Verifies everything is working
|
+-- tests/
    +-- test_connections.py <-- Can we reach all APIs?
    +-- test_guardrails.py  <-- Do the safety rules actually work?
    +-- test_data_flow.py   <-- Does data move through layers correctly?
```

---

## How To Build
ALWAYS follow this sequence:

1. Read this file (done)
2. Read ARCHITECTURE.md
3. Check .env.example -- create your .env with real keys
4. Build Execution layer first (API clients, DB connections)
5. Run: make test-connections
6. Build Orchestration layer (workflow, state, router)
7. Run: make test-flow
8. Build Directive layer (system prompt, config, guardrails)
9. Run: make test (full suite)
10. Run: make check (health check)

---

## Hard Rules -- Never Break These
1. NEVER auto-send email without confirmation_token from user
2. NEVER modify database records without dry_run check first
3. NEVER skip the audit log on any agent decision
4. NEVER deploy with a failing test
5. NEVER hardcode API keys (use .env)
6. NEVER call an API that isn't in the tool registry

---

## Cost Rules -- Keep It Lean
- Use claude-haiku-4-5-20251001 for: data extraction, formatting, simple classification
- Use claude-sonnet-4-20250514 for: reasoning, drafting, complex decisions
- Use claude-opus-4-6 for: nothing in production (too expensive) -- dev/testing only
- Batch API calls when possible
- Run `make cost-report` weekly to review spend
"""

    def _gen_architecture_md(self) -> str:
        return f"""# {self.app_name.upper()} -- Architecture
{self.description}

## System Flow
```
User Input
    |
[ COORDINATOR ] <-- system_prompt.md (Directive)
    |                config.yaml
    +-->  [ SPECIALIST AGENT 1 ] -> Tool -> External API
    +-->  [ SPECIALIST AGENT 2 ] -> Tool -> Database
    +-->  [ SPECIALIST AGENT 3 ] -> Tool -> File System
    |
[ ORCHESTRATION ] <-- workflow.py, state.py, router.py
    |
[ EXECUTION ] <-- API clients, DB, notifications
    |
Structured JSON Response
    |
User Output (UI / Voice / API)
```

## Confidence Scoring
Every agent action runs through confidence.py before executing:
- Score >= 0.85 -> Execute automatically
- Score 0.60-0.84 -> Flag for review, suggest action
- Score < 0.60 -> Stop. Ask the user.

## Data Persistence
| Data Type         | Storage      | TTL          |
|-------------------|--------------|--------------|
| User preferences  | PostgreSQL   | Permanent    |
| API cache         | Redis        | 24 hours     |
| Session state     | In-memory    | Session only |
| Audit log         | PostgreSQL   | 90 days      |
| Cost log          | JSON file    | Rolling 30d  |
"""

    def _gen_makefile(self) -> str:
        return f"""# {self.app_name.upper()} -- Makefile
# Run these commands from your terminal in the project folder.

.PHONY: help run test test-connections test-flow test-guardrails check cost-report clean

help:
\t@echo ""
\t@echo "  {self.app_name} -- Available Commands"
\t@echo "  make run              Start the server (localhost:8000)"
\t@echo "  make test             Run all tests"
\t@echo "  make test-connections Check all API connections"
\t@echo "  make test-flow        Test data moving through layers"
\t@echo "  make test-guardrails  Verify safety rules work"
\t@echo "  make check            30-second health check"
\t@echo "  make cost-report      Show this week's API costs"
\t@echo "  make clean            Remove cache files"
\t@echo ""

run:
\tuvicorn main:app --reload --port 8000

test:
\tpython -m pytest tests/ -v --tb=short

test-connections:
\tpython -m pytest tests/test_connections.py -v

test-flow:
\tpython -m pytest tests/test_data_flow.py -v

test-guardrails:
\tpython -m pytest tests/test_guardrails.py -v

check:
\tpython monitoring/health_check.py

cost-report:
\tpython monitoring/cost_tracker.py --report

clean:
\tfind . -type d -name __pycache__ -exec rm -rf {{}} + 2>/dev/null; echo "Cleaned."
"""

    def _gen_config_yaml(self) -> str:
        return f"""# {self.app_name} -- Configuration
# Edit this file to change how the app behaves.

agent:
  name: {self.app_id}
  version: 1.0.0
  environment: development

models:
  fast: claude-haiku-4-5-20251001
  default: claude-sonnet-4-20250514
  powerful: claude-opus-4-6
  temperature: 0.2
  max_tokens: 4096

cost_limits:
  daily_limit: 5.00
  warn_at_percent: 80

confidence:
  auto_execute: 0.85
  flag_for_review: 0.60

guardrails:
  require_confirmation_for:
    - send_email
    - update_calendar
    - delete_record
    - send_notification
  max_emails_per_session: 50
  max_tool_calls_per_turn: 10

cache:
  ttl_seconds: 86400
  max_size_mb: 100

business:
  client_id: default
  enable_roi_tracking: true
  enable_audit_log: true
  enable_cost_tracking: true
  dry_run_mode: false
"""


# ═══════════════════════════════════════════════════════════════
# LAYER 5: RALPH GENERATOR
# ═══════════════════════════════════════════════════════════════

class RalphGenerator:
    """
    Layer 5 — RALPH integration.
    Generates: PRD.json, ralph.sh, progress.txt for iterative AI builds.
    Opt-in: only runs when spec contains a 'ralph:' section.
    """

    TEMPLATE_DIR = Path(__file__).parent / "templates" / "ralph"

    def __init__(self, spec: dict, output_dir: Path):
        self.spec = spec
        self.dir = output_dir / "ralph"
        self.app_name = spec["app"].get("name", "FORGE Project")
        self.app_id = spec["app"].get("id", "forge-project")
        self.description = spec["app"].get("description", "")
        self.ralph_cfg = spec.get("ralph", {})
        self.now = datetime.now().isoformat()

    def generate(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        self._gen_prd()
        self._gen_ralph_sh()
        self._gen_progress_txt()

    def _gen_prd(self):
        """Generate PRD.json from template + spec stories."""
        stories = self.ralph_cfg.get("stories", [])

        if not stories:
            # Generate default foundation stories
            stories = [
                {
                    "id": "S-001",
                    "priority": 1,
                    "title": "Project scaffold and config",
                    "description": "Initialize project structure with package files, config, and basic test setup.",
                    "acceptance_criteria": [
                        "Project directory structure exists",
                        "Config file is valid",
                        "make test runs without errors"
                    ],
                    "test_command": "make test",
                    "depends_on": [],
                    "passes": False,
                },
                {
                    "id": "S-002",
                    "priority": 2,
                    "title": "Core configuration and environment",
                    "description": "Set up environment variables, config loading, and validation.",
                    "acceptance_criteria": [
                        "Config loads from config.yaml",
                        ".env.example documents all required vars",
                        "make check passes"
                    ],
                    "test_command": "make check",
                    "depends_on": ["S-001"],
                    "passes": False,
                },
                {
                    "id": "S-003",
                    "priority": 3,
                    "title": "Test suite and CI validation",
                    "description": "Ensure all tests pass and CI commands succeed.",
                    "acceptance_criteria": [
                        "All tests pass",
                        "No skipped tests",
                        "make test exits 0"
                    ],
                    "test_command": "make test",
                    "depends_on": ["S-002"],
                    "passes": False,
                },
            ]

        ci_commands = self.ralph_cfg.get("ci_commands", ["make test"])
        commit_convention = self.ralph_cfg.get(
            "commit_convention", "feat|fix|chore: description (S-XXX)"
        )

        prd = {
            "meta": {
                "project_name": self.app_name,
                "generated_by": "FORGE",
                "generated_at": self.now,
                "forge_version": "1.0",
                "ralph_compatible": True,
                "description": self.description,
                "tech_stack": self.ralph_cfg.get("tech_stack", []),
                "estimated_iterations": len(stories),
            },
            "stories": stories,
            "guardrails": {
                "max_iterations_per_story": 3,
                "ci_commands": ci_commands,
                "commit_convention": commit_convention,
                "forbidden_patterns": self.ralph_cfg.get("forbidden_patterns", [
                    "console.log used for debugging",
                    "TODO left in code",
                    "skipped tests",
                    "hardcoded credentials",
                ]),
            },
        }

        path = self.dir / "PRD.json"
        with open(path, "w") as f:
            json.dump(prd, f, indent=2)
        print(f"    + PRD.json ({len(stories)} stories)")

    def _gen_ralph_sh(self):
        """Generate ralph.sh from template with substitutions."""
        ci_commands = self.ralph_cfg.get("ci_commands", ["make test"])
        ci_str = " && ".join(ci_commands)

        template_path = self.TEMPLATE_DIR / "ralph.sh.template"
        if template_path.exists():
            content = template_path.read_text()
        else:
            # Fallback inline template
            content = self._inline_ralph_sh_template()

        content = content.replace("{{PROJECT_NAME}}", self.app_name)
        content = content.replace("{{CI_COMMANDS}}", ci_str)

        path = self.dir / "ralph.sh"
        path.write_text(content)
        path.chmod(0o755)
        print(f"    + ralph.sh")

    def _gen_progress_txt(self):
        """Generate progress.txt from template."""
        template_path = self.TEMPLATE_DIR / "progress.txt.template"
        if template_path.exists():
            content = template_path.read_text()
        else:
            content = "# {{PROJECT_NAME}} -- RALPH Progress Log\n# Generated by FORGE | {{ISO_TIMESTAMP}}\n#\n# This file is append-only. Each RALPH iteration adds an entry below.\n# Format: [ISO_TIMESTAMP] Story ID | Status | Summary\n# =====================================================\n\n"

        content = content.replace("{{PROJECT_NAME}}", self.app_name)
        content = content.replace("{{ISO_TIMESTAMP}}", self.now)

        path = self.dir / "progress.txt"
        path.write_text(content)
        print(f"    + progress.txt")

    def _inline_ralph_sh_template(self) -> str:
        """Fallback template if file template is missing."""
        return '''#!/bin/bash
set -e

MAX_ITERATIONS=${1:-20}
PRD_FILE="PRD.json"
PROGRESS_FILE="progress.txt"

echo "RALPH loop starting for {{PROJECT_NAME}}"
echo "   Max iterations: $MAX_ITERATIONS"
echo "=============================================="

for ((i=1; i<=$MAX_ITERATIONS; i++)); do
  echo ""
  echo "--- Iteration $i of $MAX_ITERATIONS ---"

  result=$(claude --permission-mode acceptEdits -p "\\
You are working on the '{{PROJECT_NAME}}' project. \\

READ these files first:
- $PRD_FILE (the full product requirements with stories)
- $PROGRESS_FILE (log of what previous iterations accomplished)

YOUR TASK:
1. Find the highest-priority story where 'passes' is still false.
2. Check if its dependencies (depends_on) all pass. If not, work on the blocking dependency instead.
3. Implement ONLY that single story.
4. Write or update tests to cover the acceptance criteria.
5. Run the story's test_command to verify it passes.
6. Run ALL guardrail CI commands: {{CI_COMMANDS}}
7. If everything passes:
   a. Update the story's 'passes' field to true in $PRD_FILE
   b. Append a progress entry to $PROGRESS_FILE with format:
      [TIMESTAMP] S-XXX | PASS | Brief summary of what was implemented
   c. Commit all changes with message format: feat: description (S-XXX)
8. If tests fail, fix the issues before committing.

CRITICAL RULES:
- ONLY work on ONE story per iteration.
- Every commit MUST pass typechecks and tests.
- NEVER skip tests or use test.skip.
- If ALL stories pass, output <promise>COMPLETE</promise>.
")

  echo "$result"

  if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
    echo ""
    echo "=============================================="
    echo "PRD COMPLETE after $i iterations!"
    echo "=============================================="
    exit 0
  fi

  echo "--- Iteration $i finished ---"
done

echo ""
echo "=============================================="
echo "Max iterations ($MAX_ITERATIONS) reached."
echo "    Check $PROGRESS_FILE for status."
echo "=============================================="
'''


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

def _cmd_new(args):
    """Scaffold-only mode: creates project with scaffold + RALPH without a YAML spec."""
    if len(args) < 1:
        print("Usage: forge.py new <name> [description]")
        sys.exit(1)

    name = args[0].lower().replace(" ", "-")
    description = " ".join(args[1:]) if len(args) > 1 else "A Brave Alpaca AI agent built with FORGE."

    print(f"\n{'=' * 60}")
    print(f"  FORGE v{Forge.VERSION} -- New Project: {name}")
    print(f"{'=' * 60}\n")

    # Build minimal spec on-the-fly
    spec = {
        "app": {
            "id": name,
            "name": name,
            "description": description,
            "version": "1.0.0",
        },
        "triggers": [{"id": "manual", "type": "webhook", "name": "Manual Trigger", "outputs_to": []}],
        "sources": [],
        "delivery": [],
        "scaffold": {"enabled": True},
        "ralph": {
            "enabled": True,
            "ci_commands": ["make test"],
        },
    }

    output_dir = Path(f"./output/{name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate scaffold
    print("  +- SCAFFOLD ───────────────────────────────────+")
    scaffold_dir = output_dir / "scaffold"
    scaffold_dir.mkdir(parents=True, exist_ok=True)
    scaffold = ScaffoldGenerator(spec, output_dir)
    scaffold.generate()

    # Generate RALPH
    print("  +- RALPH ──────────────────────────────────────+")
    ralph_dir = output_dir / "ralph"
    ralph_dir.mkdir(parents=True, exist_ok=True)
    ralph = RalphGenerator(spec, output_dir)
    ralph.generate()

    scaffold_count = sum(1 for _ in (output_dir / "scaffold").rglob("*") if _.is_file())
    ralph_count = sum(1 for _ in (output_dir / "ralph").rglob("*") if _.is_file())

    print(f"\n{'=' * 60}")
    print(f"  PROJECT CREATED")
    print(f"  Name:     {name}")
    print(f"  Scaffold: {scaffold_count} files")
    print(f"  RALPH:    {ralph_count} files")
    print(f"  Path:     {output_dir}")
    print(f"{'=' * 60}")
    print(f"\n  Next steps:")
    print(f"    cd {output_dir}/scaffold")
    print(f"    cp ../ralph/* .")
    print(f"    make check")
    print(f"    ./ralph.sh 1    # single iteration\n")


def _cmd_test(args):
    """Run pytest in project directory."""
    project_dir = args[0] if args else "."
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=project_dir,
    )
    sys.exit(result.returncode)


def _cmd_check(args):
    """Run health_check.py in project directory."""
    project_dir = args[0] if args else "."
    hc = Path(project_dir) / "monitoring" / "health_check.py"
    if hc.exists():
        result = subprocess.run(["python", str(hc)], cwd=project_dir)
        sys.exit(result.returncode)
    else:
        print(f"  No health_check.py found in {project_dir}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(f"""
+{'=' * 58}+
|  FORGE v{Forge.VERSION} -- Factory for Orchestrated Runtime        |
|  Generation of Engines                                   |
|                                                          |
|  Commands:                                               |
|    forge.py build <spec.yaml> [--output <dir>]           |
|    forge.py validate <spec.yaml>                         |
|    forge.py list-layers <spec.yaml>                      |
|    forge.py new <name> [description]                     |
|    forge.py test [project-dir]                           |
|    forge.py check [project-dir]                          |
|                                                          |
|  Brave Alpaca . COOP . Life Cockpit                      |
+{'=' * 58}+
""")
        sys.exit(1)

    command = sys.argv[1]

    # Commands that don't need a spec file
    if command == "new":
        _cmd_new(sys.argv[2:])
        sys.exit(0)
    elif command == "test":
        _cmd_test(sys.argv[2:])
    elif command == "check":
        _cmd_check(sys.argv[2:])

    # Commands that need a spec file
    if len(sys.argv) < 3:
        print(f"Usage: forge.py {command} <spec.yaml>")
        sys.exit(1)

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
            print("  + Spec is valid")
        except Exception as e:
            print(f"  x Validation failed: {e}")
            sys.exit(1)

    elif command == "list-layers":
        forge = Forge(spec_path)
        print(f"\n  App: {forge.spec['app']['name']}")
        print(f"  Triggers: {len(forge.spec.get('triggers', []))}")
        print(f"  Sources: {len(forge.spec.get('sources', []))}")
        print(f"  Services: {len(forge.spec.get('backend', {}).get('services', []))}")
        print(f"  Deliveries: {len(forge.spec.get('delivery', []))}")
        print(f"  Integrations: {list(forge.spec.get('integrations', {}).keys())}")
        if forge.spec.get("scaffold"):
            print(f"  Scaffold: enabled")
        if forge.spec.get("ralph"):
            print(f"  RALPH: enabled ({len(forge.spec['ralph'].get('stories', []))} stories)")
        print()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
