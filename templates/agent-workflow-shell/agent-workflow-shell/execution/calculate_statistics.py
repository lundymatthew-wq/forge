#!/usr/bin/env python3
"""
Calculate statistical summaries for numeric data.

Usage:
    python calculate_statistics.py <csv_file> [--columns <col1,col2>] [--output <path>]

Example:
    python calculate_statistics.py inputs/sales_data.csv --columns "revenue,profit"
"""

import sys
import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path


def calculate_statistics(csv_path, target_columns=None):
    """
    Calculate comprehensive statistics for numeric columns.
    
    Args:
        csv_path (str): Path to CSV file
        target_columns (list, optional): Specific columns to analyze
    
    Returns:
        dict: Statistical analysis results
    """
    try:
        # Load the data
        df = pd.read_csv(csv_path)
        
        # Select numeric columns
        numeric_df = df.select_dtypes(include=['number'])
        
        if target_columns:
            # Filter to requested columns
            available_cols = [col for col in target_columns if col in numeric_df.columns]
            if not available_cols:
                return {'error': f'None of the specified columns are numeric: {target_columns}'}
            numeric_df = numeric_df[available_cols]
        
        if numeric_df.empty:
            return {'error': 'No numeric columns found in the data'}
        
        results = {
            'file': str(csv_path),
            'columns_analyzed': list(numeric_df.columns),
            'statistics': {}
        }
        
        # Calculate statistics for each column
        for col in numeric_df.columns:
            series = numeric_df[col].dropna()
            
            if len(series) == 0:
                results['statistics'][col] = {'error': 'No valid data'}
                continue
            
            stats = {
                'count': int(len(series)),
                'missing': int(df[col].isna().sum()),
                'mean': float(series.mean()),
                'median': float(series.median()),
                'std': float(series.std()),
                'min': float(series.min()),
                'max': float(series.max()),
                'range': float(series.max() - series.min()),
                'q1': float(series.quantile(0.25)),
                'q3': float(series.quantile(0.75)),
                'iqr': float(series.quantile(0.75) - series.quantile(0.25)),
                'skewness': float(series.skew()),
                'kurtosis': float(series.kurtosis())
            }
            
            # Calculate mode (most common value)
            mode_result = series.mode()
            if len(mode_result) > 0:
                stats['mode'] = float(mode_result.iloc[0])
            
            # Identify outliers using IQR method
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = series[(series < lower_bound) | (series > upper_bound)]
            stats['outliers'] = {
                'count': int(len(outliers)),
                'percentage': float(len(outliers) / len(series) * 100)
            }
            
            # Coefficient of variation (relative variability)
            if stats['mean'] != 0:
                stats['coefficient_of_variation'] = float(stats['std'] / abs(stats['mean']) * 100)
            
            results['statistics'][col] = stats
        
        # Correlation matrix if multiple columns
        if len(numeric_df.columns) > 1:
            corr_matrix = numeric_df.corr()
            results['correlation_matrix'] = corr_matrix.to_dict()
            
            # Find strong correlations (|r| > 0.7)
            strong_correlations = []
            for i, col1 in enumerate(corr_matrix.columns):
                for j, col2 in enumerate(corr_matrix.columns):
                    if i < j:  # Only upper triangle
                        corr_value = corr_matrix.iloc[i, j]
                        if abs(corr_value) > 0.7:
                            strong_correlations.append({
                                'column1': col1,
                                'column2': col2,
                                'correlation': float(corr_value)
                            })
            
            if strong_correlations:
                results['strong_correlations'] = strong_correlations
        
        # Overall summary
        results['summary'] = {
            'total_rows': int(len(df)),
            'columns_analyzed': len(numeric_df.columns),
            'total_data_points': int(len(df) * len(numeric_df.columns)),
            'total_missing': int(numeric_df.isna().sum().sum()),
            'missing_percentage': float(numeric_df.isna().sum().sum() / (len(df) * len(numeric_df.columns)) * 100)
        }
        
        return results
        
    except FileNotFoundError:
        return {'error': f'File not found: {csv_path}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}


def main():
    parser = argparse.ArgumentParser(description='Calculate statistics for CSV data')
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('--columns', help='Comma-separated column names', default=None)
    parser.add_argument('--output', help='Output JSON file path', default=None)
    
    args = parser.parse_args()
    
    # Parse columns if provided
    target_cols = None
    if args.columns:
        target_cols = [col.strip() for col in args.columns.split(',')]
    
    # Calculate statistics
    result = calculate_statistics(args.csv_file, target_cols)
    
    # Save to file if output path provided
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Statistics saved to: {args.output}")
    else:
        # Print to stdout
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Exit with error code if calculation failed
    if 'error' in result:
        sys.exit(1)
    else:
        print(f"\n✓ Statistics calculated for {len(result['columns_analyzed'])} columns", 
              file=sys.stderr)


if __name__ == '__main__':
    main()
