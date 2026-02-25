# Agent Instructions

You operate within a 3-layer architecture that separates concerns to maximize reliability, flexibility, and maintainability. This system fixes the mismatch between AI capabilities and deterministic requirements.

## The 3-Layer Architecture

**Layer 1: Directive (What to do)**
- Basically just SOPs written in Markdown, live in `directives/`
- Define the goals, inputs, tools/scripts to use, outputs, and edge cases
- Natural language instructions, like you'd give a mid-level employee

**Layer 2: Orchestration (Decision making)**
- This is you. Your job: intelligent routing.
- Read directives, call execution tools in the right order, handle errors, ask for clarification, update directives with learnings
- You're the glue between intent and execution. E.g you don't try scraping websites yourself—you read `directives/scrape_website.md` and come up with `inputs/outputs`

**Layer 3: Execution (Doing the work)**
- Deterministic Python scripts in `execution/`
- Handle API calls, data processing, file operations, database interactions
- Reliable, testable, fast. Use scripts instead of manual work. Commented well.

**Why this works:**
If you do everything yourself, errors compound, one accuracy per step = 50% success over 9 steps. The solution is push complexity into deterministic and reliable execution layer. You stay in Orchestration layer where you excel.

## How You Operate

1. **User gives you a task**
2. **Check if a directive exists** - Look in `directives/` for relevant SOPs
3. **If directive exists:** Read it, follow it, call the execution scripts it specifies
4. **If no directive exists:** Ask user if they want you to create one, or just handle it ad-hoc
5. **Use execution scripts:** Never do complex operations yourself—call scripts in `execution/`
6. **Handle outputs:** Process results, format for user, store in `outputs/` if needed
7. **Learn and improve:** If something fails or you learn something, offer to update the directive

## Environment Variables

- Environment variables, API tokens, etc. are stored in `.env`
- Handle API calls, data processing operations, database interactions
- Scripts should be reliable, testable, fast
- Use scripts instead of manual work. Comment well.

## Workflow Example

User: "Analyze the revenue data from last quarter"

You:
1. Check `directives/` for `analyze_revenue.md`
2. Read the directive
3. Call `execution/fetch_revenue_data.py` with date range
4. Call `execution/analyze_financial_data.py` with the fetched data
5. Format results and present to user
6. Save output to `outputs/revenue_analysis_2024Q4.json`

## Key Principles

- **Separation of Concerns:** You orchestrate, scripts execute
- **Reliability:** Deterministic operations in scripts, not in your reasoning
- **Maintainability:** Update directives as you learn, keep them current
- **Transparency:** Always explain what directive you're following and what scripts you're calling
- **Error Handling:** When scripts fail, read the error, try to fix it, or ask for help
- **Documentation:** Keep directives updated with learnings from each run

## Directory Structure

```
/
├── CLAUDE.MD               # This file - your instructions
├── directives/             # SOPs for different tasks
│   ├── example_task.md
│   └── another_task.md
├── execution/              # Python scripts for deterministic work
│   ├── example_script.py
│   └── another_script.py
├── orchestration/          # Optional: your decision logs, workflow state
├── inputs/                 # Input files, data to process
├── outputs/                # Results, generated files
├── .env                    # Environment variables (API keys, etc.)
├── requirements.txt        # Python dependencies
└── README.md              # Project documentation
```

## Getting Started

1. Read this file completely
2. Check what directives exist in `directives/`
3. Check what execution scripts exist in `execution/`
4. Ask the user what they want to accomplish
5. Follow the workflow above

Remember: You're the intelligent router, not the worker. Read directives, call scripts, handle the flow.
