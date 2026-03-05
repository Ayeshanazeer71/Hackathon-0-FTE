#!/usr/bin/env python3
"""
Log Viewer - CLI Tool for Audit Log Inspection

Usage:
    python log_viewer.py --date 2026-01-07    # Show all logs for that date
    python log_viewer.py --week               # Show summary of this week
    python log_viewer.py --errors             # Show only error logs
    python log_viewer.py --actions email_send # Filter by action type
    python log_viewer.py --today              # Show today's logs
    python log_viewer.py --summary            # Show summary statistics
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# Base directories
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / 'Logs'


def get_log_file(date_str: str) -> Path:
    """Get log file path for a date"""
    return LOGS_DIR / f"{date_str}.json"


def load_logs_for_date(date_str: str) -> List[Dict]:
    """Load logs for a specific date"""
    log_file = get_log_file(date_str)
    if not log_file.exists():
        return []

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def load_logs_for_week() -> Dict[str, List[Dict]]:
    """Load logs for the current week (last 7 days)"""
    logs_by_date = {}
    today = datetime.now()

    for i in range(7):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        logs = load_logs_for_date(date_str)
        if logs:
            logs_by_date[date_str] = logs

    return logs_by_date


def format_log_entry(log: Dict, verbose: bool = False) -> str:
    """Format a single log entry for display"""
    timestamp = log.get('timestamp', 'N/A')[:19]
    log_type = log.get('log_type', 'N/A')
    action_type = log.get('action_type', 'N/A')
    actor = log.get('actor', 'N/A')
    target = log.get('target', 'N/A')
    result = log.get('result', 'N/A')

    line = f"[{timestamp}] {log_type:6} | {action_type:20} | {actor:15} | {target:20} | {result:8}"

    if verbose and log.get('error'):
        line += f"\n    Error: {log['error'][:100]}"

    if verbose and log.get('parameters'):
        params = log['parameters']
        if isinstance(params, dict):
            preview = str({k: v for k, v in list(params.items())[:3]})[:100]
            line += f"\n    Params: {preview}"

    return line


def show_date_logs(date_str: str, log_type: Optional[str] = None,
                   action_type: Optional[str] = None,
                   errors_only: bool = False,
                   verbose: bool = False) -> None:
    """Show logs for a specific date"""
    logs = load_logs_for_date(date_str)

    if not logs:
        print(f"\n[INFO] No logs found for {date_str}")
        return

    # Apply filters
    if log_type:
        logs = [l for l in logs if l.get('log_type') == log_type]

    if action_type:
        logs = [l for l in logs if l.get('action_type') == action_type]

    if errors_only:
        logs = [l for l in logs if l.get('log_type') == 'error' or l.get('error')]

    print(f"\n[LOGS] AUDIT LOGS - {date_str}")
    print("="*100)
    print(f"Total entries: {len(logs)}")
    print("="*100 + "\n")

    if not logs:
        print("No logs match the specified filters.")
        return

    for log in logs:
        print(format_log_entry(log, verbose))
        print()

    print("="*100)


def show_week_summary() -> None:
    """Show summary for the current week"""
    logs_by_date = load_logs_for_week()

    if not logs_by_date:
        print("\n[INFO] No logs found for the past week")
        return

    print("\n[WEEKLY] WEEKLY AUDIT LOG SUMMARY")
    print("="*60)
    print(f"Period: Last 7 days")
    print("="*60 + "\n")

    total_logs = 0
    total_errors = 0
    by_action = {}
    by_actor = {}
    by_result = {}

    for date_str, logs in sorted(logs_by_date.items(), reverse=True):
        date_total = len(logs)
        date_errors = len([l for l in logs if l.get('log_type') == 'error' or l.get('error')])

        total_logs += date_total
        total_errors += date_errors

        # Aggregate stats
        for log in logs:
            action = log.get('action_type', 'unknown')
            actor = log.get('actor', 'unknown')
            result = log.get('result', 'unknown')

            by_action[action] = by_action.get(action, 0) + 1
            by_actor[actor] = by_actor.get(actor, 0) + 1
            by_result[result] = by_result.get(result, 0) + 1

        print(f"[DATE] {date_str}: {date_total} logs ({date_errors} errors)")

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total Logs:   {total_logs}")
    print(f"Total Errors: {total_errors}")
    print(f"Success Rate: {(total_logs - total_errors) / total_logs * 100:.1f}%" if total_logs > 0 else "N/A")

    print("\n[TOP] Top Actions:")
    for action, count in sorted(by_action.items(), key=lambda x: -x[1])[:10]:
        print(f"  - {action}: {count}")

    print("\n[TOP] Top Actors:")
    for actor, count in sorted(by_actor.items(), key=lambda x: -x[1])[:10]:
        print(f"  - {actor}: {count}")

    print("\n[RESULT] Results:")
    for result, count in sorted(by_result.items(), key=lambda x: -x[1]):
        print(f"  - {result}: {count}")

    print("\n" + "="*60 + "\n")


def show_errors(date_str: Optional[str] = None) -> None:
    """Show only error logs"""
    if date_str:
        logs = load_logs_for_date(date_str)
    else:
        logs = load_logs_for_date(datetime.now().strftime('%Y-%m-%d'))

    errors = [l for l in logs if l.get('log_type') == 'error' or l.get('error')]

    if not errors:
        print("\n[INFO] No errors found")
        return

    print(f"\n[ERRORS] ERROR LOGS" + (f" - {date_str}" if date_str else " - Today"))
    print("="*100)
    print(f"Total errors: {len(errors)}")
    print("="*100 + "\n")

    for error in errors:
        timestamp = error.get('timestamp', 'N/A')[:19]
        component = error.get('parameters', {}).get('component', 'unknown')
        error_type = error.get('parameters', {}).get('error_type', 'unknown')
        error_msg = error.get('error', 'Unknown error')[:150]
        actor = error.get('actor', 'unknown')

        print(f"[{timestamp}] {component:20} | {error_type:15} | {actor:15}")
        print(f"    {error_msg}")

        if error.get('parameters', {}).get('stack_trace'):
            stack = error['parameters']['stack_trace'][:300]
            print(f"    Stack: {stack}...")

        print()

    print("="*100 + "\n")


def show_summary(date_str: Optional[str] = None) -> None:
    """Show summary statistics"""
    if date_str:
        logs = load_logs_for_date(date_str)
        period = date_str
    else:
        logs = load_logs_for_date(datetime.now().strftime('%Y-%m-%d'))
        period = "Today"

    if not logs:
        print(f"\n[INFO] No logs found for {period}")
        return

    # Calculate statistics
    by_type = {}
    by_action = {}
    by_actor = {}
    by_result = {}
    by_approval = {}
    errors = 0

    for log in logs:
        log_type = log.get('log_type', 'unknown')
        action_type = log.get('action_type', 'unknown')
        actor = log.get('actor', 'unknown')
        result = log.get('result', 'unknown')
        approval = log.get('approval_status', 'unknown')

        by_type[log_type] = by_type.get(log_type, 0) + 1
        by_action[action_type] = by_action.get(action_type, 0) + 1
        by_actor[actor] = by_actor.get(actor, 0) + 1
        by_result[result] = by_result.get(result, 0) + 1
        by_approval[approval] = by_approval.get(approval, 0) + 1

        if log.get('log_type') == 'error' or log.get('error'):
            errors += 1

    print(f"\n[SUMMARY] AUDIT LOG SUMMARY - {period}")
    print("="*60)
    print(f"Total Logs: {len(logs)}")
    print(f"Errors: {errors}")
    print(f"Success Rate: {(len(logs) - errors) / len(logs) * 100:.1f}%" if len(logs) > 0 else "N/A")
    print("="*60)

    print("\n[TYPE] By Type:")
    for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  - {t}: {count}")

    print("\n[ACTION] By Action:")
    for action, count in sorted(by_action.items(), key=lambda x: -x[1])[:15]:
        print(f"  - {action}: {count}")

    print("\n[ACTOR] By Actor:")
    for actor, count in sorted(by_actor.items(), key=lambda x: -x[1])[:10]:
        print(f"  - {actor}: {count}")

    print("\n[RESULT] By Result:")
    for result, count in sorted(by_result.items(), key=lambda x: -x[1]):
        print(f"  - {result}: {count}")

    print("\n[APPROVAL] By Approval Status:")
    for approval, count in sorted(by_approval.items(), key=lambda x: -x[1]):
        print(f"  - {approval}: {count}")

    print("\n" + "="*60 + "\n")


def show_actions(action_type: str, date_str: Optional[str] = None) -> None:
    """Show logs filtered by action type"""
    if date_str:
        logs = load_logs_for_date(date_str)
    else:
        logs = load_logs_for_date(datetime.now().strftime('%Y-%m-%d'))

    filtered = [l for l in logs if l.get('action_type') == action_type]

    if not filtered:
        print(f"\n[INFO] No '{action_type}' actions found")
        return

    print(f"\n[ACTIONS] ACTION LOGS - {action_type}" + (f" - {date_str}" if date_str else ""))
    print("="*100)
    print(f"Total entries: {len(filtered)}")
    print("="*100 + "\n")

    for log in filtered:
        print(format_log_entry(log, verbose=True))
        print()

    print("="*100 + "\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Log Viewer - CLI Tool for Audit Log Inspection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python log_viewer.py --date 2026-01-07       # Show all logs for that date
  python log_viewer.py --week                  # Show summary of this week
  python log_viewer.py --errors                # Show only error logs
  python log_viewer.py --actions email_send    # Filter by action type
  python log_viewer.py --today --verbose       # Show today's logs verbose
  python log_viewer.py --summary               # Show summary statistics
        """
    )

    parser.add_argument('--date', '-d', type=str,
                        help='Show logs for specific date (YYYY-MM-DD)')
    parser.add_argument('--week', '-w', action='store_true',
                        help='Show summary for the last 7 days')
    parser.add_argument('--today', '-t', action='store_true',
                        help='Show today\'s logs')
    parser.add_argument('--errors', '-e', action='store_true',
                        help='Show only error logs')
    parser.add_argument('--actions', '-a', type=str,
                        help='Filter by action type (e.g., email_send)')
    parser.add_argument('--type', type=str, choices=['action', 'error', 'system'],
                        help='Filter by log type')
    parser.add_argument('--summary', '-s', action='store_true',
                        help='Show summary statistics')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show verbose output with details')
    parser.add_argument('--limit', '-l', type=int, default=100,
                        help='Limit number of entries shown (default: 100)')

    args = parser.parse_args()

    # Determine which view to show
    if args.week:
        show_week_summary()
    elif args.errors:
        show_errors(args.date)
    elif args.summary:
        show_summary(args.date)
    elif args.actions:
        show_actions(args.actions, args.date)
    elif args.today:
        date_str = datetime.now().strftime('%Y-%m-%d')
        show_date_logs(date_str, log_type=args.type, verbose=args.verbose)
    elif args.date:
        show_date_logs(args.date, log_type=args.type, verbose=args.verbose)
    else:
        # Default: show today's summary
        show_summary()


if __name__ == '__main__':
    main()
