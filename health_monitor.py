#!/usr/bin/env python3
"""
Health Monitor - Process Monitoring and Auto-Recovery

Checks every 60 seconds that critical processes are running.
Auto-restarts failed processes (max 3 attempts) and alerts on persistent failures.

Monitored Processes:
- orchestrator.py
- gmail_watcher.py
- whatsapp_watcher.py
- linkedin_watcher.py
- twitter_watcher.py
- social_media_watcher.py
- hitl_watcher.py
- email_mcp_server.js
- odoo_mcp_server.js
"""

import os
import sys
import json
import time
import subprocess
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Base directories
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / 'Logs'
NEEDS_ACTION_DIR = BASE_DIR / 'Needs_Action'
PIDS_DIR = BASE_DIR / 'pids'
DASHBOARD_FILE = BASE_DIR / 'Dashboard.md'

# Ensure directories exist
for directory in [LOGS_DIR, NEEDS_ACTION_DIR, PIDS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Health log file
HEALTH_LOG_FILE = LOGS_DIR / 'health_log.json'

# Process definitions
MONITORED_PROCESSES = [
    {'name': 'orchestrator.py', 'type': 'python', 'restart_delay': 2},
    {'name': 'gmail_watcher.py', 'type': 'python', 'restart_delay': 2},
    {'name': 'whatsapp_watcher.py', 'type': 'python', 'restart_delay': 2},
    {'name': 'linkedin_watcher.py', 'type': 'python', 'restart_delay': 2},
    {'name': 'twitter_watcher.py', 'type': 'python', 'restart_delay': 2},
    {'name': 'social_media_watcher.py', 'type': 'python', 'restart_delay': 2},
    {'name': 'hitl_watcher.py', 'type': 'python', 'restart_delay': 2},
    {'name': 'email_mcp_server.js', 'type': 'node', 'restart_delay': 3},
    {'name': 'odoo_mcp_server.js', 'type': 'node', 'restart_delay': 3},
]

# Maximum restart attempts before alerting
MAX_RESTART_ATTEMPTS = 3

# Check interval in seconds
CHECK_INTERVAL = 60


def log_health_event(event_type: str, details: dict) -> None:
    """Log health check events to ./Logs/health_log.json"""
    logs = []
    if HEALTH_LOG_FILE.exists():
        try:
            with open(HEALTH_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            logs = []
    
    logs.append({
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'details': details
    })
    
    # Keep last 500 events
    if len(logs) > 500:
        logs = logs[-500:]
    
    with open(HEALTH_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)


def get_pid_file(process_name: str) -> Path:
    """Get PID file path for a process"""
    base_name = process_name.replace('.py', '').replace('.js', '')
    return PIDS_DIR / f"{base_name}.pid"


def read_pid(process_name: str) -> Optional[int]:
    """Read PID from file"""
    pid_file = get_pid_file(process_name)
    if not pid_file.exists():
        return None
    
    try:
        with open(pid_file, 'r') as f:
            return int(f.read().strip())
    except (ValueError, IOError):
        return None


def write_pid(process_name: str, pid: int) -> None:
    """Write PID to file"""
    pid_file = get_pid_file(process_name)
    with open(pid_file, 'w') as f:
        f.write(str(pid))


def is_process_running(pid: int) -> bool:
    """Check if a process is running by PID"""
    try:
        # Windows
        if os.name == 'nt':
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}', '/NH'],
                capture_output=True,
                text=True
            )
            return str(pid) in result.stdout
        else:
            # Unix/Linux/Mac
            os.kill(pid, 0)
            return True
    except (OSError, subprocess.SubprocessError):
        return False


def get_process_command(process_name: str) -> List[str]:
    """Get command to start a process"""
    if process_name.endswith('.py'):
        return ['python', process_name]
    elif process_name.endswith('.js'):
        return ['node', process_name]
    else:
        return [process_name]


def start_process(process_name: str) -> Optional[int]:
    """Start a process and return its PID"""
    try:
        command = get_process_command(process_name)
        
        # Start process in background
        process = subprocess.Popen(
            command,
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        pid = process.pid
        
        # Give it a moment to start
        time.sleep(1)
        
        if is_process_running(pid):
            write_pid(process_name, pid)
            return pid
        else:
            return None
            
    except Exception as e:
        print(f"Error starting {process_name}: {e}")
        return None


def stop_process(process_name: str) -> bool:
    """Stop a process by PID"""
    pid = read_pid(process_name)
    if pid is None:
        return False
    
    try:
        if os.name == 'nt':
            # Windows
            subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                          capture_output=True)
        else:
            # Unix/Linux/Mac
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        
        # Wait for process to stop
        time.sleep(2)
        
        # Force kill if still running
        if is_process_running(pid):
            if os.name == 'nt':
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                              capture_output=True)
            else:
                os.killpg(os.getpgid(pid), signal.SIGKILL)
        
        # Remove PID file
        pid_file = get_pid_file(process_name)
        if pid_file.exists():
            pid_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"Error stopping {process_name}: {e}")
        return False


def create_system_alert(process_name: str, restart_attempts: int, error_details: str) -> str:
    """Create alert file in Needs_Action/"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    alert_file = NEEDS_ACTION_DIR / f"SYSTEM_ALERT_{process_name.replace('.', '_')}_{timestamp}.md"
    
    alert_content = f"""# SYSTEM ALERT - Process Down

## Process Information
- **Process:** {process_name}
- **Detected At:** {datetime.now().isoformat()}
- **Restart Attempts:** {restart_attempts}
- **Max Attempts:** {MAX_RESTART_ATTEMPTS}

## Status
⚠️ **CRITICAL:** Process is DOWN and could not be auto-restarted.

## Error Details
{error_details}

## Required Actions
- [ ] Check process logs in `logs/` directory
- [ ] Verify configuration and dependencies
- [ ] Manually restart the process:
  ```bash
  python {process_name}  # For Python scripts
  node {process_name}    # For Node.js scripts
  ```
- [ ] Update Dashboard.md after resolution
- [ ] Delete this alert file after resolving

## Auto-Recovery History
The system attempted to restart this process {restart_attempts} times automatically.
All attempts failed. Manual intervention required.

---
*Generated by Health Monitor System*
"""
    
    with open(alert_file, 'w', encoding='utf-8') as f:
        f.write(alert_content)
    
    return str(alert_file)


def update_dashboard_alert(process_name: str, restart_attempts: int, alert_file: str) -> None:
    """Write alert to Dashboard.md under Alerts section"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    alert = f"""
## 🚨 SYSTEM ALERT - {timestamp}

**Process:** `{process_name}`
**Status:** DOWN (Auto-restart failed after {restart_attempts} attempts)
**Alert File:** [{alert_file.split('/')[-1]}]({alert_file})

**Action Required:** Manual intervention needed. Check Needs_Action/ folder.

---
"""
    
    if DASHBOARD_FILE.exists():
        with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if Alerts section exists
        if '## 🚨 SYSTEM ALERT' in content or '## Alerts' in content:
            # Insert at beginning of alerts
            lines = content.split('\n')
            insert_index = 0
            for i, line in enumerate(lines):
                if '## 🚨 SYSTEM ALERT' in line or line == '## Alerts':
                    insert_index = i + 1
                    break
            
            content = '\n'.join(lines[:insert_index]) + alert + '\n'.join(lines[insert_index:])
        else:
            # Add new Alerts section
            lines = content.split('\n')
            if len(lines) > 1:
                content = lines[0] + '\n\n## Alerts\n' + alert + '\n'.join(lines[1:])
            else:
                content = '# AI Employee Dashboard\n\n## Alerts\n' + alert
    else:
        content = f"# AI Employee Dashboard\n\n## Alerts\n{alert}"
    
    with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
        f.write(content)


def check_and_restart_process(process_info: Dict[str, Any], restart_counts: Dict[str, int]) -> Dict[str, Any]:
    """
    Check if a process is running and attempt restart if needed.
    
    Returns:
        dict with status information
    """
    process_name = process_info['name']
    pid = read_pid(process_name)
    
    result = {
        'name': process_name,
        'was_running': False,
        'restart_attempted': False,
        'restart_success': False,
        'alert_created': False,
        'error': None
    }
    
    # Check if process is running
    if pid and is_process_running(pid):
        result['was_running'] = True
        return result
    
    # Process is not running - attempt restart
    print(f"⚠️  [{process_name}] Process not running (PID: {pid})")
    
    restart_counts[process_name] = restart_counts.get(process_name, 0) + 1
    attempt = restart_counts[process_name]
    
    result['restart_attempted'] = True
    
    # Log restart attempt
    log_health_event('restart_attempt', {
        'process': process_name,
        'attempt': attempt,
        'max_attempts': MAX_RESTART_ATTEMPTS
    })
    
    # Try to start the process
    new_pid = start_process(process_name)
    
    if new_pid and is_process_running(new_pid):
        print(f"✅ [{process_name}] Restarted successfully (PID: {new_pid})")
        result['restart_success'] = True
        
        # Reset restart count on success
        restart_counts[process_name] = 0
        
        log_health_event('restart_success', {
            'process': process_name,
            'new_pid': new_pid
        })
    else:
        print(f"❌ [{process_name}] Restart failed (attempt {attempt}/{MAX_RESTART_ATTEMPTS})")
        result['error'] = f"Failed to start process after {attempt} attempts"
        
        # Check if we've exceeded max attempts
        if attempt >= MAX_RESTART_ATTEMPTS:
            # Create alert file
            alert_file = create_system_alert(
                process_name, 
                attempt, 
                result['error']
            )
            
            # Update Dashboard
            update_dashboard_alert(process_name, attempt, alert_file)
            
            result['alert_created'] = True
            
            log_health_event('alert_created', {
                'process': process_name,
                'alert_file': alert_file
            })
            
            print(f"🚨 [{process_name}] Alert created: {alert_file}")
    
    return result


def run_health_check() -> Dict[str, Any]:
    """
    Run a complete health check on all monitored processes.
    
    Returns:
        dict with overall health status
    """
    print("\n" + "="*60)
    print("🏥 HEALTH CHECK")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    # Load restart counts from state file
    restart_counts_file = PIDS_DIR / 'restart_counts.json'
    restart_counts = {}
    if restart_counts_file.exists():
        try:
            with open(restart_counts_file, 'r') as f:
                restart_counts = json.load(f)
        except (json.JSONDecodeError, IOError):
            restart_counts = {}
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'processes': [],
        'healthy_count': 0,
        'unhealthy_count': 0,
        'restarted_count': 0,
        'alerts_created': 0
    }
    
    for process_info in MONITORED_PROCESSES:
        process_name = process_info['name']
        print(f"Checking: {process_name}...")
        
        result = check_and_restart_process(process_info, restart_counts)
        results['processes'].append(result)
        
        if result['was_running']:
            print(f"  ✅ Running")
            results['healthy_count'] += 1
        elif result['restart_success']:
            print(f"  ✅ Restarted")
            results['restarted_count'] += 1
            results['healthy_count'] += 1
        else:
            print(f"  ❌ Down")
            results['unhealthy_count'] += 1
            if result['alert_created']:
                results['alerts_created'] += 1
    
    # Save restart counts
    with open(restart_counts_file, 'w') as f:
        json.dump(restart_counts, f, indent=2)
    
    # Log summary
    log_health_event('health_check_complete', {
        'healthy': results['healthy_count'],
        'unhealthy': results['unhealthy_count'],
        'restarted': results['restarted_count'],
        'alerts': results['alerts_created']
    })
    
    # Print summary
    print("\n" + "="*60)
    print("HEALTH CHECK SUMMARY")
    print("="*60)
    print(f"Healthy:    {results['healthy_count']}/{len(MONITORED_PROCESSES)}")
    print(f"Unhealthy:  {results['unhealthy_count']}/{len(MONITORED_PROCESSES)}")
    print(f"Restarted:  {results['restarted_count']}")
    print(f"Alerts:     {results['alerts_created']}")
    print("="*60 + "\n")
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Health Monitor - Process Monitoring and Auto-Recovery',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage:
  python health_monitor.py          # Run continuous monitoring
  python health_monitor.py --once   # Run single health check
  python health_monitor.py --check  # Alias for --once
        """
    )
    
    parser.add_argument(
        '--once', '--check',
        action='store_true',
        help='Run single health check and exit'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=CHECK_INTERVAL,
        help=f'Check interval in seconds (default: {CHECK_INTERVAL})'
    )
    
    args = parser.parse_args()
    
    if args.once:
        # Single health check
        results = run_health_check()
        sys.exit(0 if results['unhealthy_count'] == 0 else 1)
    
    # Continuous monitoring
    print("🏥 Health Monitor starting...")
    print(f"Monitoring {len(MONITORED_PROCESSES)} processes")
    print(f"Check interval: {args.interval} seconds")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            run_health_check()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n\nHealth Monitor stopped.")


if __name__ == '__main__':
    main()
