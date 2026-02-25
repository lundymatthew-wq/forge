#!/usr/bin/env python3
"""
Load and validate CSV data with automatic encoding detection.

Usage:
    python load_csv_data.py <csv_file> [--output <path>] [--sample <n>]

Example:
    python load_csv_data.py inputs/sales_data.csv --sample 10
"""

import sys
import json
import argparse
import pandas as pd
import chardet
from pathlib import Path


def detect_encoding(file_path):
    """
    Detect the encoding of a file.
    
    Args:
        file_path (str): Path to the file
    
    Returns:
        str: Detected encoding
    """
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read(100000))  # Read first 100KB
    return result['encoding']


def load_csv_data(csv_path, sample_rows=None):
    """
    Load CSV data with encoding detection and validation.
    
    Args:
        csv_path (str): Path to CSV file
        sample_rows (int, optional): Number of sample rows to return
    
    Returns:
        dict: Loaded data info and validation results
    """
    csv_path = Path(csv_path)
    
    if not csv_path.exists():
        return {'error': f'File not found: {csv_path}'}
    
    # Try to detect encoding
    encodings_to_try = []
    try:
        detected = detect_encoding(csv_path)
        encodings_to_try.append(detected)
    except Exception:
        pass
    
    # Add common encodings
    encodings_to_try.extend(['utf-8', 'latin-1', 'cp1252', 'iso-8859-1'])
    
    df = None
    used_encoding = None
    
    # Try different encodings
    for encoding in encodings_to_try:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            used_encoding = encoding
            break
        except (UnicodeDecodeError, Exception):
            continue
    
    if df is None:
        return {'error': 'Could not read CSV with any common encoding'}
    
    # Analyze the data
    analysis = {
        'file_path': str(csv_path),
        'encoding': used_encoding,
        'shape': {
            'rows': len(df),
            'columns': len(df.columns)
        },
        'columns': list(df.columns),
        'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'missing_values': {
            col: int(df[col].isna().sum()) 
            for col in df.columns 
            if df[col].isna().sum() > 0
        },
        'numeric_columns': list(df.select_dtypes(include=['number']).columns),
        'categorical_columns': list(df.select_dtypes(include=['object']).columns),
        'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
    }
    
    # Add sample data
    if sample_rows:
        sample_rows = min(sample_rows, len(df))
        analysis['sample_data'] = df.head(sample_rows).to_dict(orient='records')
    
    # Add summary statistics for numeric columns
    if len(analysis['numeric_columns']) > 0:
        desc = df[analysis['numeric_columns']].describe()
        analysis['statistics'] = desc.to_dict()
    
    # Detect potential date columns
    potential_date_columns = []
    for col in df.columns:
        if df[col].dtype == 'object':
            # Try to parse as date
            try:
                pd.to_datetime(df[col].dropna().head(100), errors='coerce')
                # If more than 50% are valid dates, it's likely a date column
                if pd.to_datetime(df[col].dropna().head(100), errors='coerce').notna().sum() > 50:
                    potential_date_columns.append(col)
            except Exception:
                pass
    
    if potential_date_columns:
        analysis['potential_date_columns'] = potential_date_columns
    
    # Warnings
    warnings = []
    if analysis['memory_usage_mb'] > 100:
        warnings.append(f"Large file: {analysis['memory_usage_mb']:.1f} MB in memory")
    
    if len(analysis['missing_values']) > 0:
        total_missing = sum(analysis['missing_values'].values())
        total_cells = len(df) * len(df.columns)
        missing_pct = (total_missing / total_cells) * 100
        warnings.append(f"Missing data: {missing_pct:.1f}% of cells")
    
    if warnings:
        analysis['warnings'] = warnings
    
    return analysis


def main():
    parser = argparse.ArgumentParser(description='Load and analyze CSV data')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('--output', help='Output JSON file path', default=None)
    parser.add_argument('--sample', help='Number of sample rows', type=int, default=5)
    
    args = parser.parse_args()
    
    # Load and analyze the CSV
    result = load_csv_data(args.csv_file, args.sample)
    
    # Save to file if output path provided
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Analysis saved to: {args.output}")
    else:
        # Print to stdout
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Exit with error code if loading failed
    if 'error' in result:
        sys.exit(1)
    else:
        print(f"\n✓ Successfully loaded {result['shape']['rows']:,} rows × {result['shape']['columns']} columns", 
              file=sys.stderr)


if __name__ == '__main__':
    main()
