#!/usr/bin/env python3
"""
Orchestration logger - tracks workflow execution for debugging and learning.

Usage:
    python orchestration_logger.py <workflow_name> <status> [--message <msg>] [--data <json>]

Example:
    python orchestration_logger.py "analyze_sales" "started" --message "Beginning analysis"
    python orchestration_logger.py "analyze_sales" "completed" --data '{"rows": 100}'
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path


def log_workflow(workflow_name, status, message=None, data=None):
    """
    Log workflow execution for tracking and debugging.
    
    Args:
        workflow_name (str): Name of the workflow
        status (str): Status (started, completed, failed, etc.)
        message (str, optional): Additional message
        data (dict, optional): Additional data to log
    
    Returns:
        dict: Log entry
    """
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        'timestamp': timestamp,
        'workflow': workflow_name,
        'status': status
    }
    
    if message:
        log_entry['message'] = message
    
    if data:
        log_entry['data'] = data
    
    # Create orchestration directory if it doesn't exist
    log_dir = Path('orchestration')
    log_dir.mkdir(exist_ok=True)
    
    # Append to log file
    log_file = log_dir / f'{workflow_name}.jsonl'
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    return log_entry


def view_logs(workflow_name=None, limit=None):
    """
    View workflow logs.
    
    Args:
        workflow_name (str, optional): Filter by workflow name
        limit (int, optional): Limit number of entries
    
    Returns:
        list: Log entries
    """
    log_dir = Path('orchestration')
    
    if not log_dir.exists():
        return []
    
    logs = []
    
    if workflow_name:
        # Read specific workflow log
        log_file = log_dir / f'{workflow_name}.jsonl'
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    logs.append(json.loads(line.strip()))
    else:
        # Read all workflow logs
        for log_file in log_dir.glob('*.jsonl'):
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    logs.append(json.loads(line.strip()))
    
    # Sort by timestamp
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    
    if limit:
        logs = logs[:limit]
    
    return logs


def main():
    parser = argparse.ArgumentParser(description='Log and view workflow orchestration')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Log command
    log_parser = subparsers.add_parser('log', help='Log a workflow event')
    log_parser.add_argument('workflow', help='Workflow name')
    log_parser.add_argument('status', help='Status (started, completed, failed, etc.)')
    log_parser.add_argument('--message', help='Additional message', default=None)
    log_parser.add_argument('--data', help='Additional data as JSON string', default=None)
    
    # View command
    view_parser = subparsers.add_parser('view', help='View workflow logs')
    view_parser.add_argument('--workflow', help='Filter by workflow name', default=None)
    view_parser.add_argument('--limit', help='Limit number of entries', type=int, default=None)
    
    args = parser.parse_args()
    
    if args.command == 'log':
        # Parse data if provided
        data = None
        if args.data:
            try:
                data = json.loads(args.data)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON data: {args.data}", file=sys.stderr)
                sys.exit(1)
        
        # Log the workflow event
        log_entry = log_workflow(args.workflow, args.status, args.message, data)
        print(json.dumps(log_entry, indent=2))
        
    elif args.command == 'view':
        # View logs
        logs = view_logs(args.workflow, args.limit)
        
        if not logs:
            print("No logs found")
        else:
            for log in logs:
                print(json.dumps(log, indent=2))
                print('-' * 50)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
