#!/usr/bin/env python3
"""
Ralph Wiggum Autonomous Loop Pattern

Keeps Claude working until a task is FULLY complete.
Intercepts Claude's exit and re-injects the prompt if task is not done yet.

Usage:
    python ralph_wiggum.py \
        --prompt "Process all files in Needs_Action/ and create Plans" \
        --promise "TASK_COMPLETE" \
        --max-iter 10
"""

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

# Base directories
BASE_DIR = Path(__file__).parent
STATE_DIR = BASE_DIR / 'ralph_state'
LOGS_DIR = BASE_DIR / 'Logs'
FAILED_DIR = LOGS_DIR / 'failed_tasks'
DASHBOARD_FILE = BASE_DIR / 'Dashboard.md'

# Ensure directories exist
for directory in [STATE_DIR, LOGS_DIR, FAILED_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# State files
CURRENT_TASK_FILE = STATE_DIR / 'current_task.json'
ITERATION_HISTORY_FILE = STATE_DIR / 'iteration_history.json'
RALPH_LOG_FILE = LOGS_DIR / 'ralph_log.json'


def log_to_file(log_file: Path, entry: dict) -> None:
    """Append entry to a JSON log file"""
    logs = []
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            logs = []
    
    logs.append(entry)
    
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)


def save_current_task(task_data: dict) -> None:
    """Save current task state"""
    with open(CURRENT_TASK_FILE, 'w', encoding='utf-8') as f:
        json.dump(task_data, f, indent=2)


def load_current_task() -> Optional[dict]:
    """Load current task state"""
    if not CURRENT_TASK_FILE.exists():
        return None
    try:
        with open(CURRENT_TASK_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_iteration_history(history: List[dict]) -> None:
    """Save iteration history"""
    with open(ITERATION_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)


def load_iteration_history() -> List[dict]:
    """Load iteration history"""
    if not ITERATION_HISTORY_FILE.exists():
        return []
    try:
        with open(ITERATION_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def update_dashboard_failure(task_id: str, reason: str, iterations: int) -> None:
    """Update Dashboard.md with failure alert"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    alert = f"""
## ⚠️ Ralph Wiggum Loop Failure Alert

**Task ID:** {task_id}
**Failed At:** {timestamp}
**Reason:** {reason}
**Iterations Completed:** {iterations}

---
"""
    
    if DASHBOARD_FILE.exists():
        with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Insert alert after the first line (or at the beginning)
        lines = content.split('\n')
        if len(lines) > 1:
            content = lines[0] + '\n' + alert + '\n'.join(lines[1:])
        else:
            content = alert + content
    else:
        content = f"# AI Employee Dashboard\n{alert}"
    
    with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
        f.write(content)


def move_task_to_failed(task_data: dict, history: List[dict]) -> str:
    """Move failed task to failed_tasks folder"""
    task_id = task_data.get('id', datetime.now().strftime('%Y%m%d_%H%M%S'))
    failed_file = FAILED_DIR / f"failed_task_{task_id}.json"
    
    failed_data = {
        'task': task_data,
        'iteration_history': history,
        'failed_at': datetime.now().isoformat(),
        'status': 'FAILED'
    }
    
    with open(failed_file, 'w', encoding='utf-8') as f:
        json.dump(failed_data, f, indent=2)
    
    return str(failed_file)


def run_claude_cli(prompt: str, timeout: int = 600) -> tuple[str, str, int]:
    """
    Run Claude CLI with the given prompt
    
    Returns:
        tuple: (stdout, stderr, return_code)
    """
    try:
        # Run claude CLI with the prompt
        # Note: This assumes 'claude' is available in PATH
        result = subprocess.run(
            ['claude', prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return '', 'Claude CLI timed out', -1
    except FileNotFoundError:
        return '', 'Claude CLI not found. Please install: npm install -g @anthropic-ai/claude-code', -1
    except Exception as e:
        return '', str(e), -1


def check_completion(output: str, promise: str) -> bool:
    """Check if output contains the completion promise string"""
    return promise in output


def build_next_prompt(original_prompt: str, previous_outputs: List[str], iteration: int) -> str:
    """
    Build the next prompt by appending previous output as context
    
    Args:
        original_prompt: The original task prompt
        previous_outputs: List of previous iteration outputs
        iteration: Current iteration number
    
    Returns:
        str: The enhanced prompt for next iteration
    """
    if not previous_outputs:
        return original_prompt
    
    # Build context from previous iterations
    context_parts = []
    for i, output in enumerate(previous_outputs, 1):
        # Truncate very long outputs to avoid token limits
        truncated = output[:5000] if len(output) > 5000 else output
        context_parts.append(f"--- Iteration {i} Output ---\n{truncated}\n")
    
    context = '\n'.join(context_parts)
    
    next_prompt = f"""{original_prompt}

---
PREVIOUS ATTEMPTS CONTEXT (for reference only):
{context}

Continue working on the task above. Review what was done in previous iterations and proceed from there.
If the task is now complete, include the completion marker.
"""
    
    return next_prompt


def ralph_loop(
    prompt: str,
    promise: str,
    max_iterations: int = 10,
    task_id: Optional[str] = None
) -> dict:
    """
    Ralph Wiggum autonomous loop
    
    Args:
        prompt: The task prompt to give to Claude
        promise: The completion promise string to look for
        max_iterations: Maximum number of iterations (default: 10)
        task_id: Optional task ID for tracking
    
    Returns:
        dict: Result with status, iterations, and output
    """
    # Generate task ID if not provided
    if not task_id:
        task_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Initialize task state
    task_data = {
        'id': task_id,
        'prompt': prompt,
        'promise': promise,
        'max_iterations': max_iterations,
        'started_at': datetime.now().isoformat(),
        'status': 'RUNNING',
        'current_iteration': 0
    }
    
    # Initialize iteration history
    iteration_history = []
    
    # Save initial state
    save_current_task(task_data)
    save_iteration_history(iteration_history)
    
    # Log start
    log_to_file(RALPH_LOG_FILE, {
        'timestamp': datetime.now().isoformat(),
        'event': 'loop_started',
        'task_id': task_id,
        'prompt_preview': prompt[:200],
        'promise': promise,
        'max_iterations': max_iterations
    })
    
    print(f"\n{'='*60}")
    print(f"🔁 RALPH WIGGUM LOOP STARTED")
    print(f"{'='*60}")
    print(f"Task ID: {task_id}")
    print(f"Prompt: {prompt[:100]}...")
    print(f"Completion Promise: {promise}")
    print(f"Max Iterations: {max_iterations}")
    print(f"{'='*60}\n")
    
    previous_outputs = []
    final_output = ''
    
    for iteration in range(1, max_iterations + 1):
        print(f"\n{'='*40}")
        print(f"📍 ITERATION {iteration}/{max_iterations}")
        print(f"{'='*40}")
        
        # Update task state
        task_data['current_iteration'] = iteration
        save_current_task(task_data)
        
        # Build prompt for this iteration
        if iteration == 1:
            current_prompt = prompt
        else:
            current_prompt = build_next_prompt(prompt, previous_outputs, iteration)
        
        # Run Claude CLI
        print(f"⏳ Running Claude CLI...")
        start_time = time.time()
        stdout, stderr, return_code = run_claude_cli(current_prompt)
        elapsed = time.time() - start_time
        
        # Combine output
        output = stdout + ('\n[STDERR]\n' + stderr if stderr else '')
        previous_outputs.append(output)
        
        # Log iteration
        iteration_entry = {
            'iteration': iteration,
            'timestamp': datetime.now().isoformat(),
            'elapsed_seconds': round(elapsed, 2),
            'return_code': return_code,
            'output_length': len(output),
            'output_preview': output[:500] if output else 'No output',
            'promise_found': False
        }
        
        # Check for completion promise
        if check_completion(output, promise):
            print(f"✅ COMPLETION PROMISE FOUND!")
            iteration_entry['promise_found'] = True
            iteration_entry['status'] = 'SUCCESS'
            iteration_history.append(iteration_entry)
            
            # Update task state
            task_data['status'] = 'COMPLETED'
            task_data['completed_at'] = datetime.now().isoformat()
            task_data['total_iterations'] = iteration
            save_current_task(task_data)
            save_iteration_history(iteration_history)
            
            # Log success
            log_to_file(RALPH_LOG_FILE, {
                'timestamp': datetime.now().isoformat(),
                'event': 'loop_completed',
                'task_id': task_id,
                'iterations': iteration,
                'status': 'SUCCESS'
            })
            
            print(f"\n{'='*60}")
            print(f"✅ TASK COMPLETED in {iteration} iteration(s)")
            print(f"{'='*60}")
            
            return {
                'status': 'SUCCESS',
                'task_id': task_id,
                'iterations': iteration,
                'output': output,
                'history': iteration_history
            }
        else:
            print(f"⏸️  Completion promise not found. Continuing...")
            iteration_entry['status'] = 'CONTINUING'
            iteration_history.append(iteration_entry)
            save_iteration_history(iteration_history)
        
        # Small delay between iterations
        if iteration < max_iterations:
            time.sleep(2)
    
    # Max iterations reached without completion
    print(f"\n{'='*60}")
    print(f"❌ MAX ITERATIONS REACHED WITHOUT COMPLETION")
    print(f"{'='*60}")
    
    # Mark task as failed
    task_data['status'] = 'FAILED'
    task_data['failed_at'] = datetime.now().isoformat()
    task_data['failure_reason'] = 'Max iterations reached without completion promise'
    task_data['total_iterations'] = max_iterations
    save_current_task(task_data)
    
    # Move to failed tasks
    failed_file = move_task_to_failed(task_data, iteration_history)
    
    # Update dashboard
    update_dashboard_failure(
        task_id,
        'Max iterations reached without completion promise',
        max_iterations
    )
    
    # Log failure
    log_to_file(RALPH_LOG_FILE, {
        'timestamp': datetime.now().isoformat(),
        'event': 'loop_failed',
        'task_id': task_id,
        'iterations': max_iterations,
        'reason': 'Max iterations reached',
        'failed_file': failed_file
    })
    
    return {
        'status': 'FAILED',
        'task_id': task_id,
        'iterations': max_iterations,
        'output': previous_outputs[-1] if previous_outputs else '',
        'history': iteration_history,
        'failed_file': failed_file
    }


def main():
    parser = argparse.ArgumentParser(
        description='Ralph Wiggum Autonomous Loop - Keep Claude working until task is complete',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ralph_wiggum.py --prompt "Process all files" --promise "TASK_COMPLETE"
  python ralph_wiggum.py --prompt "Analyze data" --promise "DONE" --max-iter 5
  python ralph_wiggum.py --prompt "Fix bugs" --promise "ALL_FIXED" --max-iter 15 --task-id "bug-fix-001"
        """
    )
    
    parser.add_argument(
        '--prompt', '-p',
        required=True,
        help='The task prompt to give to Claude'
    )
    
    parser.add_argument(
        '--promise', '-P',
        required=True,
        help='The completion promise string to look for in output'
    )
    
    parser.add_argument(
        '--max-iter', '-m',
        type=int,
        default=10,
        help='Maximum number of iterations (default: 10)'
    )
    
    parser.add_argument(
        '--task-id', '-t',
        default=None,
        help='Optional task ID for tracking'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=600,
        help='Timeout for each Claude CLI call in seconds (default: 600)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually running'
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE")
        print(f"Prompt: {args.prompt}")
        print(f"Promise: {args.promise}")
        print(f"Max Iterations: {args.max_iter}")
        print(f"Task ID: {args.task_id or 'auto-generated'}")
        return
    
    # Run the Ralph Wiggum loop
    result = ralph_loop(
        prompt=args.prompt,
        promise=args.promise,
        max_iterations=args.max_iter,
        task_id=args.task_id
    )
    
    # Print summary
    print(f"\n📊 FINAL SUMMARY")
    print(f"{'-'*40}")
    print(f"Status: {result['status']}")
    print(f"Task ID: {result['task_id']}")
    print(f"Iterations: {result['iterations']}")
    
    if result['status'] == 'FAILED':
        print(f"Failed File: {result.get('failed_file', 'N/A')}")
    
    print(f"{'-'*40}")
    
    # Exit with appropriate code
    sys.exit(0 if result['status'] == 'SUCCESS' else 1)


if __name__ == '__main__':
    main()
