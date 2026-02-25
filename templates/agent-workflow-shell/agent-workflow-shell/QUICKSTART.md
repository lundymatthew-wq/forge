# Quick Start Guide

## Test the System (5 minutes)

### 1. Test the CSV Analysis Workflow

```bash
# Load and analyze the sample data
python execution/load_csv_data.py inputs/sample_sales.csv

# Calculate statistics
python execution/calculate_statistics.py inputs/sample_sales.csv --output outputs/sales_stats.json
```

### 2. Test the Web Scraping Workflow

```bash
# Scrape a simple website
python execution/scrape_single_site.py https://example.com --output outputs/example_scrape.json
```

### 3. Work with the AI Agent

Share the `CLAUDE.MD` file with your AI assistant and say:

> "I've set up this 3-layer agent architecture. Can you analyze the sample sales data in inputs/sample_sales.csv?"

The AI will:
1. Read `directives/analyze_csv_data.md`
2. Call `execution/load_csv_data.py`
3. Call `execution/calculate_statistics.py`
4. Present results to you

## Creating Your First Custom Workflow

### 1. Define the Task

Think about a repetitive task you do. For example: "Send a daily summary email"

### 2. Create a Directive

Create `directives/send_daily_summary.md`:

```markdown
# Directive: Send Daily Summary Email

## Goal
Compile key metrics and send via email

## Inputs
- Date range (default: yesterday)
- Recipient email

## Execution Scripts to Use
1. execution/fetch_daily_metrics.py
2. execution/format_email.py
3. execution/send_email.py

## Workflow
1. Fetch metrics for date range
2. Format into email template
3. Send to recipient
4. Log success

## Edge Cases
- No data for date range: Send empty report
- Email fails: Retry 3 times, then alert user

## Success Criteria
- Email sent successfully
- Metrics include: revenue, orders, customers
```

### 3. Create the Scripts

Create `execution/fetch_daily_metrics.py`, etc.

### 4. Test

Test each script independently, then let AI orchestrate them.

## Tips

- **Start simple**: Pick an easy task first
- **Test scripts manually**: Don't rely on AI for debugging
- **Use JSON**: Makes data exchange easy
- **Handle errors**: Always return error information
- **Update directives**: Learn from each run

## Next Steps

1. Browse `directives/` to see example SOPs
2. Browse `execution/` to see example scripts
3. Try the sample workflows above
4. Create your first custom workflow
5. Let the AI orchestrate it!
