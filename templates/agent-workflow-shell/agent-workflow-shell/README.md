# Agent Workflow Shell

A 3-layer AI agent architecture that separates concerns to maximize reliability, flexibility, and maintainability.

## Overview

This system solves the problem of AI accuracy compounding over multiple steps by pushing complexity into a deterministic execution layer, while keeping the AI in an orchestration role where it excels.

### The 3 Layers

1. **Directive Layer** (`directives/`) - The "what to do"
   - SOPs written in Markdown
   - Define goals, inputs, tools, outputs, and edge cases
   - Natural language instructions

2. **Orchestration Layer** (Claude/AI) - The "decision making"
   - Intelligent routing and workflow management
   - Reads directives and calls execution scripts
   - Handles errors and asks for clarification

3. **Execution Layer** (`execution/`) - The "doing the work"
   - Deterministic Python scripts
   - Handles API calls, data processing, file operations
   - Reliable, testable, and fast

## Quick Start

### 1. Installation

```bash
# Clone or download this repository
cd agent-workflow-shell

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and settings
```

### 2. Directory Structure

```
agent-workflow-shell/
├── CLAUDE.MD               # Instructions for the AI agent
├── directives/             # Task SOPs in Markdown
│   ├── scrape_website.md
│   └── analyze_csv_data.md
├── execution/              # Python scripts
│   ├── scrape_single_site.py
│   ├── load_csv_data.py
│   └── calculate_statistics.py
├── orchestration/          # Workflow logs (optional)
├── inputs/                 # Input files
├── outputs/                # Generated results
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

### 3. Usage

The system is designed to be used with an AI assistant (like Claude) that reads `CLAUDE.MD` and follows the architecture.

**Typical workflow:**

1. Give the AI a task: "Scrape https://example.com and analyze the content"
2. AI checks `directives/` for relevant SOPs
3. AI calls appropriate scripts from `execution/`
4. AI handles the results and presents them to you

**Manual usage of execution scripts:**

```bash
# Scrape a website
python execution/scrape_single_site.py https://example.com --output outputs/example.json

# Load and analyze CSV
python execution/load_csv_data.py inputs/data.csv --sample 10

# Calculate statistics
python execution/calculate_statistics.py inputs/data.csv --output outputs/stats.json
```

## Creating New Workflows

### 1. Create a Directive

Create a new `.md` file in `directives/`:

```markdown
# Directive: Your Task Name

## Goal
What you want to accomplish

## Inputs
- Required inputs
- Optional parameters

## Execution Scripts to Use
1. script1.py - What it does
2. script2.py - What it does

## Workflow
Step-by-step process

## Outputs
Expected output format

## Edge Cases
- Case 1: How to handle
- Case 2: How to handle

## Success Criteria
How to know it worked
```

### 2. Create Execution Scripts

Create corresponding Python scripts in `execution/`:

```python
#!/usr/bin/env python3
"""
Brief description of what this script does.

Usage:
    python script_name.py <args>
"""

import sys
import json
import argparse

def main():
    parser = argparse.ArgumentParser(description='...')
    # Add arguments
    args = parser.parse_args()
    
    # Do the work
    result = do_work(args)
    
    # Output results
    print(json.dumps(result, indent=2))
    
    if 'error' in result:
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### 3. Test the Workflow

Test your scripts manually first, then let the AI orchestrate them.

## Examples

### Example 1: Web Scraping

```bash
# The AI follows directives/scrape_website.md
# Calls: execution/scrape_single_site.py
# Saves results to: outputs/scraped_*.json
```

### Example 2: Data Analysis

```bash
# The AI follows directives/analyze_csv_data.md
# Calls: execution/load_csv_data.py → execution/calculate_statistics.py
# Saves results to: outputs/analysis_*/
```

## Best Practices

1. **Keep directives simple** - Write them like you're instructing a smart colleague
2. **Make scripts atomic** - Each script should do one thing well
3. **Use JSON for data exchange** - Easy to parse and debug
4. **Handle errors gracefully** - Always return error info in a consistent format
5. **Log everything** - Use stdout for data, stderr for status messages
6. **Test scripts independently** - Don't rely on the AI for testing

## Troubleshooting

**Problem: Script not found**
- Check that scripts are in `execution/` directory
- Verify script has execute permissions: `chmod +x execution/script.py`

**Problem: Import errors**
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**Problem: File not found errors**
- Check file paths are relative to project root
- Verify input files are in `inputs/` directory

## Contributing

When adding new functionality:

1. Create a directive in `directives/`
2. Create corresponding execution scripts
3. Test manually
4. Update this README with examples

## Why This Architecture Works

**Traditional approach:**
- AI does everything → errors compound → 50% success rate over 9 steps

**This approach:**
- AI orchestrates → Scripts execute → 95%+ success rate
- Clear separation of concerns
- Easy to debug and improve
- Scales to complex workflows

## License

MIT License - Use freely for any purpose.
