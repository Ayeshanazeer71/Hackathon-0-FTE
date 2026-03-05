#!/usr/bin/env python3
"""
Audit Logger - Central Logging Module for AI Employee System

Every single action taken by the AI Employee is logged in a structured format.
Logs are stored in ./Logs/YYYY-MM-DD.json format (one file per day).

Usage:
    from audit_logger import log_action, log_error, log_system_event
    
    log_action('email_send', 'gmail_watcher', 'user@example.com', {...}, 'success', 'auto_approved')
    log_error('gmail_watcher', 'SMTPError', 'Connection failed', traceback.format_exc())
    log_system_event('system_start', {'version': '1.0.0'})
"""

import os
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict
from functools import wraps
import threading

# Base directories
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / 'Logs'

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Thread lock for file writes
_lock = threading.Lock()


def get_log_file() -> Path:
    """Get today's log file path"""
    today = datetime.now().strftime('%Y-%m-%d')
    return LOGS_DIR / f"{today}.json"


def load_logs() -> list:
    """Load today's logs"""
    log_file = get_log_file()
    if not log_file.exists():
        return []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_logs(logs: list) -> None:
    """Save logs to today's file"""
    log_file = get_log_file()
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


def log_action(
    action_type: str,
    actor: str,
    target: str,
    parameters: Optional[Dict[str, Any]] = None,
    result: str = 'pending',
    approval_status: str = 'pending',
    approved_by: str = 'N/A',
    error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log an action taken by the AI Employee.
    
    Args:
        action_type: Type of action (email_send, payment, social_post, file_move, etc.)
        actor: Who performed the action (gmail_watcher, claude, hitl_watcher, etc.)
        target: Who or what was affected
        parameters: Action parameters/details
        result: 'success', 'failed', or 'pending'
        approval_status: 'auto_approved', 'human_approved', 'pending', 'rejected'
        approved_by: 'human', 'system', or 'N/A'
        error: Error message if result is 'failed'
    
    Returns:
        The log entry that was created
    
    Example:
        log_action(
            action_type='email_send',
            actor='gmail_watcher',
            target='user@example.com',
            parameters={'subject': 'Hello', 'body': '...'},
            result='success',
            approval_status='auto_approved',
            approved_by='system'
        )
    """
    entry = {
        'timestamp': datetime.now().isoformat(),
        'log_type': 'action',
        'action_type': action_type,
        'actor': actor,
        'target': target,
        'parameters': parameters or {},
        'approval_status': approval_status,
        'approved_by': approved_by,
        'result': result,
        'error': error
    }
    
    with _lock:
        logs = load_logs()
        logs.append(entry)
        save_logs(logs)
    
    return entry


def log_error(
    component: str,
    error_type: str,
    error_message: str,
    stack_trace: Optional[str] = None,
    actor: str = 'system',
    target: str = 'N/A',
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Log an error that occurred.
    
    Args:
        component: Component where error occurred (gmail_watcher, odoo, etc.)
        error_type: Type of error (SMTPError, ConnectionError, etc.)
        error_message: Human-readable error message
        stack_trace: Full stack trace (use traceback.format_exc())
        actor: Actor that encountered the error
        target: What was being operated on
        parameters: Context parameters
    
    Returns:
        The log entry that was created
    
    Example:
        try:
            send_email(...)
        except Exception as e:
            log_error(
                component='gmail_watcher',
                error_type=type(e).__name__,
                error_message=str(e),
                stack_trace=traceback.format_exc()
            )
    """
    entry = {
        'timestamp': datetime.now().isoformat(),
        'log_type': 'error',
        'action_type': 'error',
        'actor': actor,
        'target': target,
        'parameters': {
            'component': component,
            'error_type': error_type,
            'error_message': error_message,
            'stack_trace': stack_trace,
            **(parameters or {})
        },
        'approval_status': 'N/A',
        'approved_by': 'N/A',
        'result': 'failed',
        'error': error_message
    }
    
    with _lock:
        logs = load_logs()
        logs.append(entry)
        save_logs(logs)
    
    return entry


def log_system_event(
    event_type: str,
    details: Optional[Dict[str, Any]] = None,
    actor: str = 'system'
) -> Dict[str, Any]:
    """
    Log a system event (startup, shutdown, config change, etc.).
    
    Args:
        event_type: Type of event (system_start, system_stop, config_change, etc.)
        details: Event details
        actor: Who triggered the event
    
    Returns:
        The log entry that was created
    
    Example:
        log_system_event('system_start', {'version': '1.0.0', 'pid': os.getpid()})
    """
    entry = {
        'timestamp': datetime.now().isoformat(),
        'log_type': 'system',
        'action_type': event_type,
        'actor': actor,
        'target': 'system',
        'parameters': details or {},
        'approval_status': 'N/A',
        'approved_by': 'N/A',
        'result': 'success',
        'error': None
    }
    
    with _lock:
        logs = load_logs()
        logs.append(entry)
        save_logs(logs)
    
    return entry


# ============================================================================
# Decorator for Automatic Action Logging
# ============================================================================

def audit_log(action_type: str, actor: str = 'unknown'):
    """
    Decorator that automatically logs function calls as actions.
    
    Args:
        action_type: Type of action to log
        actor: Actor performing the action
    
    Example:
        @audit_log('email_send', actor='gmail_watcher')
        def send_email(to, subject, body):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Log start (pending)
            log_action(
                action_type=action_type,
                actor=actor,
                target=str(args[0]) if args else 'unknown',
                parameters={
                    'args': str(args)[:500],
                    'kwargs': str(kwargs)[:500]
                },
                result='pending'
            )
            
            try:
                result = func(*args, **kwargs)
                
                # Log success
                log_action(
                    action_type=action_type,
                    actor=actor,
                    target=str(args[0]) if args else 'unknown',
                    parameters={'result_preview': str(result)[:200]},
                    result='success',
                    approval_status='auto_approved',
                    approved_by='system'
                )
                
                return result
                
            except Exception as e:
                # Log failure
                log_action(
                    action_type=action_type,
                    actor=actor,
                    target=str(args[0]) if args else 'unknown',
                    parameters={},
                    result='failed',
                    error=str(e)
                )
                raise
        
        return wrapper
    return decorator


# ============================================================================
# Query Functions
# ============================================================================

def get_logs_for_date(date_str: str) -> list:
    """Get all logs for a specific date"""
    log_file = LOGS_DIR / f"{date_str}.json"
    if not log_file.exists():
        return []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def get_logs_by_type(log_type: str, date_str: Optional[str] = None) -> list:
    """Get logs filtered by type (action, error, system)"""
    if date_str:
        logs = get_logs_for_date(date_str)
    else:
        logs = load_logs()
    
    return [log for log in logs if log.get('log_type') == log_type]


def get_logs_by_action_type(action_type: str, date_str: Optional[str] = None) -> list:
    """Get logs filtered by action type"""
    if date_str:
        logs = get_logs_for_date(date_str)
    else:
        logs = load_logs()
    
    return [log for log in logs if log.get('action_type') == action_type]


def get_errors(date_str: Optional[str] = None) -> list:
    """Get all error logs"""
    return get_logs_by_type('error', date_str)


def get_logs_by_actor(actor: str, date_str: Optional[str] = None) -> list:
    """Get logs filtered by actor"""
    if date_str:
        logs = get_logs_for_date(date_str)
    else:
        logs = load_logs()
    
    return [log for log in logs if log.get('actor') == actor]


def get_summary(date_str: Optional[str] = None) -> Dict[str, Any]:
    """Get summary statistics for logs"""
    if date_str:
        logs = get_logs_for_date(date_str)
    else:
        logs = load_logs()
    
    summary = {
        'total_logs': len(logs),
        'by_type': {},
        'by_action': {},
        'by_actor': {},
        'by_result': {},
        'by_approval': {},
        'errors': 0
    }
    
    for log in logs:
        # Count by type
        log_type = log.get('log_type', 'unknown')
        summary['by_type'][log_type] = summary['by_type'].get(log_type, 0) + 1
        
        # Count by action type
        action_type = log.get('action_type', 'unknown')
        summary['by_action'][action_type] = summary['by_action'].get(action_type, 0) + 1
        
        # Count by actor
        actor = log.get('actor', 'unknown')
        summary['by_actor'][actor] = summary['by_actor'].get(actor, 0) + 1
        
        # Count by result
        result = log.get('result', 'unknown')
        summary['by_result'][result] = summary['by_result'].get(result, 0) + 1
        
        # Count by approval status
        approval = log.get('approval_status', 'unknown')
        summary['by_approval'][approval] = summary['by_approval'].get(approval, 0) + 1
        
        # Count errors
        if log.get('log_type') == 'error' or log.get('error'):
            summary['errors'] += 1
    
    return summary


# ============================================================================
# Main - CLI for quick log inspection
# ============================================================================

def main():
    """Show today's log summary"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Audit Logger - Quick Log Inspection')
    parser.add_argument('--date', type=str, help='Date to view (YYYY-MM-DD)')
    parser.add_argument('--type', type=str, choices=['action', 'error', 'system'], help='Filter by log type')
    parser.add_argument('--action', type=str, help='Filter by action type')
    parser.add_argument('--summary', action='store_true', help='Show summary only')
    
    args = parser.parse_args()
    
    date_str = args.date or datetime.now().strftime('%Y-%m-%d')
    
    if args.summary:
        summary = get_summary(date_str)
        print(f"\n📊 AUDIT LOG SUMMARY - {date_str}")
        print("="*50)
        print(f"Total Logs: {summary['total_logs']}")
        print(f"Errors: {summary['errors']}")
        print(f"\nBy Type: {summary['by_type']}")
        print(f"By Action: {summary['by_action']}")
        print(f"By Actor: {summary['by_actor']}")
        print(f"By Result: {summary['by_result']}")
        print("="*50 + "\n")
    else:
        logs = get_logs_for_date(date_str)
        
        if args.type:
            logs = [l for l in logs if l.get('log_type') == args.type]
        
        if args.action:
            logs = [l for l in logs if l.get('action_type') == args.action]
        
        print(f"\n📋 AUDIT LOGS - {date_str}")
        print("="*50)
        print(f"Total entries: {len(logs)}")
        print("="*50 + "\n")
        
        for log in logs[:50]:  # Show first 50
            print(f"[{log.get('timestamp', 'N/A')[:19]}] {log.get('log_type', 'N/A'):6} | "
                  f"{log.get('action_type', 'N/A'):20} | {log.get('actor', 'N/A'):15} | "
                  f"{log.get('result', 'N/A'):8}")
        
        if len(logs) > 50:
            print(f"\n... and {len(logs) - 50} more entries")
        
        print()


if __name__ == '__main__':
    main()
