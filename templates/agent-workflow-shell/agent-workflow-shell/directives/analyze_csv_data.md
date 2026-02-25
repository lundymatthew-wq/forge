# Directive: Analyze CSV Data

## Goal
Load, analyze, and visualize data from CSV files, providing statistical insights and charts.

## Inputs
- **CSV File Path** (required): Path to the CSV file in `inputs/`
- **Analysis Type** (optional): 'summary', 'correlation', 'timeseries', 'all' (default: 'all')
- **Target Columns** (optional): Specific columns to analyze (default: all numeric columns)

## Execution Scripts to Use
1. `execution/load_csv_data.py` - Load and validate CSV
2. `execution/calculate_statistics.py` - Calculate descriptive statistics
3. `execution/generate_visualizations.py` - Create charts
4. `execution/export_analysis.py` - Save results

## Workflow
1. Validate CSV file exists in `inputs/`
2. Load CSV using `load_csv_data.py` - checks for encoding issues, missing values
3. If loading fails, try different encodings (utf-8, latin-1, cp1252)
4. Calculate statistics with `calculate_statistics.py`:
   - Mean, median, mode, std dev for numeric columns
   - Value counts for categorical columns
   - Missing value analysis
5. Generate visualizations based on analysis type:
   - Summary: histograms and box plots
   - Correlation: correlation matrix heatmap
   - Timeseries: line charts with trends
6. Export results to `outputs/analysis_[filename]_[timestamp]/`
7. Present findings to user with key insights

## Outputs
- **stats.json**: Statistical summary
- **report.html**: Visual report with charts
- **visualizations/**: PNG files of charts
- **cleaned_data.csv**: Cleaned version of input data (optional)

Structure:
```
outputs/analysis_sales_data_20240127/
├── stats.json
├── report.html
├── visualizations/
│   ├── distribution_revenue.png
│   ├── correlation_matrix.png
│   └── timeseries_trend.png
└── cleaned_data.csv
```

## Edge Cases
- **Large files (>100MB)**: Process in chunks, warn user about processing time
- **Missing values**: Report percentage, offer to fill with mean/median/mode
- **Non-numeric data**: Identify and handle appropriately (categorical analysis)
- **Date columns**: Auto-detect and convert to datetime
- **Mixed encodings**: Try multiple encodings, ask user if all fail

## Error Handling
- File not found: Check `inputs/` directory, list available files
- Encoding errors: Try utf-8, latin-1, cp1252 in sequence
- Memory errors: Switch to chunked processing
- Invalid column names: Sanitize names, warn user

## Success Criteria
- CSV successfully loaded and validated
- Statistical analysis completed for all appropriate columns
- At least 3 visualizations generated
- Results exported to outputs directory
- User receives actionable insights

## Notes
- Always show sample of data (first 5 rows) to user for confirmation
- Ask user about column meanings if unclear
- Suggest additional analyses based on data patterns discovered
- Keep visualizations simple and clear
