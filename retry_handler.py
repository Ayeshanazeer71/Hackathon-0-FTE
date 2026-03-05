#!/usr/bin/env python3
"""
Retry Handler - Comprehensive Error Recovery System

Provides a reusable decorator with exponential backoff for any function.
Logs all failures and alerts Dashboard on final failure.

Usage:
    @with_retry(max_attempts=3, base_delay=2, max_delay=60)
    def my_function():
        ...
"""

import os
import sys
import json
import time
import traceback
import functools
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any, Tuple

# Base directories
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / 'Logs'
DASHBOARD_FILE = BASE_DIR / 'Dashboard.md'
DRAFTS_DIR = BASE_DIR / 'Drafts' / 'queued'

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

# Error log file
ERRORS_LOG_FILE = LOGS_DIR / 'errors.json'


def log_error(error_data: dict) -> None:
    """Log error to ./Logs/errors.json"""
    errors = []
    if ERRORS_LOG_FILE.exists():
        try:
            with open(ERRORS_LOG_FILE, 'r', encoding='utf-8') as f:
                errors = json.load(f)
        except (json.JSONDecodeError, IOError):
            errors = []
    
    errors.append(error_data)
    
    # Keep last 1000 errors
    if len(errors) > 1000:
        errors = errors[-1000:]
    
    with open(ERRORS_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(errors, f, indent=2)


def update_dashboard_alert(error_data: dict) -> None:
    """Write alert to Dashboard.md under Alerts section"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    alert = f"""
## ⚠️ Error Alert - {timestamp}

**Function:** `{error_data.get('function', 'unknown')}`
**Error Type:** {error_data.get('error_type', 'unknown')}
**Attempts:** {error_data.get('attempts', 'N/A')}
**Message:** {error_data.get('message', 'No details')}

---
"""
    
    if DASHBOARD_FILE.exists():
        with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if Alerts section exists
        if '## Alerts' in content or '## ⚠️' in content:
            # Insert after existing alerts
            lines = content.split('\n')
            insert_index = 0
            for i, line in enumerate(lines):
                if line.startswith('## Alerts') or '⚠️' in line:
                    insert_index = i + 1
                    # Find end of this section
                    while insert_index < len(lines) and not lines[insert_index].startswith('## '):
                        insert_index += 1
                    break
            
            content = '\n'.join(lines[:insert_index]) + alert + '\n'.join(lines[insert_index:])
        else:
            # Add new Alerts section after title
            lines = content.split('\n')
            if len(lines) > 1:
                content = lines[0] + '\n\n## Alerts\n' + alert + '\n'.join(lines[1:])
            else:
                content = '# AI Employee Dashboard\n\n## Alerts\n' + alert
    else:
        content = f"# AI Employee Dashboard\n\n## Alerts\n{alert}"
    
    with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
        f.write(content)


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple = (Exception,),
    log_errors: bool = True,
    alert_on_final: bool = True,
    retry_callback: Optional[Callable] = None
) -> Callable:
    """
    Decorator that adds retry logic with exponential backoff to any function.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds between retries (default: 2)
        max_delay: Maximum delay cap in seconds (default: 60)
        exceptions: Tuple of exception types to catch (default: all Exceptions)
        log_errors: Whether to log errors to ./Logs/errors.json (default: True)
        alert_on_final: Whether to alert Dashboard on final failure (default: True)
        retry_callback: Optional callback function called before each retry
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @with_retry(max_attempts=3, base_delay=2, max_delay=60)
        def send_email(to, subject, body):
            ...
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    
                    # Log attempt
                    error_info = {
                        'function': func.__name__,
                        'module': func.__module__,
                        'attempt': attempt,
                        'max_attempts': max_attempts,
                        'error_type': type(e).__name__,
                        'message': str(e),
                        'timestamp': datetime.now().isoformat(),
                        'args_preview': str(args)[:200] if args else None,
                        'kwargs_preview': str(kwargs)[:200] if kwargs else None
                    }
                    
                    print(f"⚠️  [{func.__name__}] Attempt {attempt}/{max_attempts} failed: {type(e).__name__}")
                    print(f"   Delay: {delay:.1f}s | Message: {str(e)[:100]}")
                    
                    # Call retry callback if provided
                    if retry_callback and attempt < max_attempts:
                        try:
                            retry_callback(error_info, attempt)
                        except Exception as cb_error:
                            print(f"   Retry callback error: {cb_error}")
                    
                    # If not final attempt, wait and retry
                    if attempt < max_attempts:
                        time.sleep(delay)
                    else:
                        # Final failure
                        print(f"❌ [{func.__name__}] All {max_attempts} attempts failed")
                        
                        final_error = {
                            **error_info,
                            'status': 'FINAL_FAILURE',
                            'traceback': traceback.format_exc(),
                            'total_duration': 'N/A'
                        }
                        
                        if log_errors:
                            log_error(final_error)
                            print(f"   Error logged to {ERRORS_LOG_FILE}")
                        
                        if alert_on_final:
                            update_dashboard_alert(final_error)
                            print(f"   Alert written to Dashboard.md")
                        
                        # Re-raise the exception
                        raise last_exception
            
            # Should not reach here, but just in case
            raise last_exception
        
        return wrapper
    
    return decorator


# Convenience retry configurations for common scenarios

def api_retry(func: Callable) -> Callable:
    """Retry decorator for API calls (3 attempts, 2s base delay, 30s max)"""
    return with_retry(
        max_attempts=3,
        base_delay=2,
        max_delay=30,
        exceptions=(Exception,),
        alert_on_final=True
    )(func)


def database_retry(func: Callable) -> Callable:
    """Retry decorator for database operations (5 attempts, 1s base delay, 10s max)"""
    return with_retry(
        max_attempts=5,
        base_delay=1,
        max_delay=10,
        exceptions=(Exception,),
        alert_on_final=True
    )(func)


def file_operation_retry(func: Callable) -> Callable:
    """Retry decorator for file operations (3 attempts, 0.5s base delay, 5s max)"""
    return with_retry(
        max_attempts=3,
        base_delay=0.5,
        max_delay=5,
        exceptions=(IOError, OSError, PermissionError),
        alert_on_final=False
    )(func)


def critical_operation_retry(func: Callable) -> Callable:
    """Retry decorator for critical operations (5 attempts, 5s base delay, 120s max)"""
    return with_retry(
        max_attempts=5,
        base_delay=5,
        max_delay=120,
        exceptions=(Exception,),
        alert_on_final=True
    )(func)


# Example usage and tests
if __name__ == '__main__':
    print("Testing retry_handler.py...")
    
    # Test 1: Function that succeeds on first try
    @with_retry(max_attempts=3)
    def always_succeeds():
        return "Success!"
    
    result = always_succeeds()
    print(f"Test 1 - Always succeeds: {result}")
    
    # Test 2: Function that fails all attempts
    @with_retry(max_attempts=3, base_delay=0.1, alert_on_final=False)
    def always_fails():
        raise ValueError("Intentional failure")
    
    try:
        always_fails()
    except ValueError as e:
        print(f"Test 2 - Always fails (expected): {e}")
    
    # Test 3: Function that succeeds on third attempt
    attempt_count = [0]
    
    @with_retry(max_attempts=5, base_delay=0.1, alert_on_final=False)
    def succeeds_on_third():
        attempt_count[0] += 1
        if attempt_count[0] < 3:
            raise RuntimeError(f"Not yet (attempt {attempt_count[0]})")
        return f"Success on attempt {attempt_count[0]}"
    
    result = succeeds_on_third()
    print(f"Test 3 - Succeeds on third: {result}")
    
    # Test 4: API retry decorator
    @api_retry
    def mock_api_call():
        raise ConnectionError("API unavailable")
    
    try:
        mock_api_call()
    except ConnectionError:
        print("Test 4 - API retry exhausted (expected)")
    
    print("\n✅ All tests completed!")
    print(f"Check {ERRORS_LOG_FILE} for logged errors.")
