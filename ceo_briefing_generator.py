#!/usr/bin/env python3
"""
Weekly CEO Briefing Generator

Every Sunday at 9 PM, generates a "Monday Morning CEO Briefing" by auditing
the entire week's data across all business systems.

Usage:
    python ceo_briefing_generator.py [--manual]
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests

# Base directories
BASE_DIR = Path(__file__).parent
BRIEFINGS_DIR = BASE_DIR / 'Briefings'
LOGS_DIR = BASE_DIR / 'Logs'
DONE_DIR = BASE_DIR / 'Done'
ACCOUNTING_DIR = BASE_DIR / 'Accounting'
DASHBOARD_FILE = BASE_DIR / 'Dashboard.md'
BUSINESS_GOALS_FILE = BASE_DIR / 'Business_Goals.md'

# Log file
BRIEFING_LOG_FILE = LOGS_DIR / 'briefing_log.json'

# Ensure directories exist
for directory in [BRIEFINGS_DIR, LOGS_DIR, DONE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Environment variables for Odoo
ODOO_URL = os.environ.get('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.environ.get('ODOO_DB', 'ai_employee_db')
ODOO_USERNAME = os.environ.get('ODOO_USERNAME', 'admin')
ODOO_PASSWORD = os.environ.get('ODOO_PASSWORD', 'changeme123')


def log_briefing(event: str, details: dict) -> None:
    """Log briefing generation events"""
    logs = []
    if BRIEFING_LOG_FILE.exists():
        try:
            with open(BRIEFING_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            logs = []
    
    logs.append({
        'timestamp': datetime.now().isoformat(),
        'event': event,
        'details': details
    })
    
    with open(BRIEFING_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2)


def read_file_safe(filepath: Path) -> Optional[str]:
    """Safely read a file, return None if not exists"""
    if not filepath.exists():
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except (IOError, UnicodeDecodeError):
        return None


def get_done_files_last_7_days() -> List[Dict[str, Any]]:
    """Read all files in Done/ created in last 7 days"""
    completed_tasks = []
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    if not DONE_DIR.exists():
        return completed_tasks
    
    for file in DONE_DIR.iterdir():
        if file.is_file():
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if mtime >= seven_days_ago:
                    content = read_file_safe(file)
                    if content:
                        completed_tasks.append({
                            'filename': file.name,
                            'completed_date': mtime.isoformat(),
                            'content_preview': content[:500] if content else ''
                        })
            except (OSError, IOError):
                continue
    
    return completed_tasks


def read_accounting_data() -> Optional[str]:
    """Read ./Accounting/Current_Month.md"""
    accounting_file = ACCOUNTING_DIR / 'Current_Month.md'
    return read_file_safe(accounting_file)


def call_odoo_revenue_summary() -> Optional[Dict]:
    """
    Call Odoo MCP to get revenue summary for current month
    Uses JSON-RPC directly since MCP servers run separately
    """
    try:
        # Direct Odoo JSON-RPC call for revenue
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # This would typically call the Odoo MCP server
        # For now, we'll make a direct JSON-RPC call to Odoo
        session = requests.Session()
        
        # Authenticate
        auth_url = f"{ODOO_URL}/web/session/authenticate"
        auth_payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'db': ODOO_DB,
                'login': ODOO_USERNAME,
                'password': ODOO_PASSWORD,
                'context': {}
            },
            'id': 1
        }
        
        auth_response = session.post(auth_url, json=auth_payload)
        auth_result = auth_response.json()
        
        if 'result' not in auth_result or not auth_result['result'].get('uid'):
            return None
        
        # Get invoices for current month
        call_url = f"{ODOO_URL}/web/dataset/call_kw"
        
        # Search for invoices
        start_date = f"{current_year}-{current_month:02d}-01"
        search_payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'model': 'account.move',
                'method': 'search_read',
                'args': [
                    [
                        ['move_type', 'in', ['out_invoice', 'out_refund']],
                        ['invoice_date', '>=', start_date],
                        ['state', 'in', ['posted', 'paid']]
                    ],
                    ['id', 'name', 'amount_total', 'amount_residual', 'state', 'invoice_date']
                ],
                'kwargs': {'limit': 100}
            },
            'id': 2
        }
        
        invoice_response = session.post(call_url, json=search_payload)
        invoice_result = invoice_response.json()
        
        if 'result' not in invoice_result:
            return None
        
        invoices = invoice_result['result']
        
        total_invoiced = sum(inv.get('amount_total', 0) for inv in invoices)
        total_paid = sum(inv.get('amount_total', 0) for inv in invoices if inv.get('amount_residual', 0) == 0)
        total_outstanding = sum(inv.get('amount_residual', 0) for inv in invoices)
        
        return {
            'month': current_month,
            'year': current_year,
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'total_outstanding': total_outstanding,
            'invoice_count': len(invoices),
            'invoices': invoices[:10]  # First 10 for reference
        }
        
    except Exception as e:
        log_briefing('odoo_error', {'error': str(e)})
        return None


def read_social_summaries() -> Dict[str, Optional[str]]:
    """Read all social media summary files"""
    return {
        'facebook': read_file_safe(BRIEFINGS_DIR / 'facebook_summary.md'),
        'instagram': read_file_safe(BRIEFINGS_DIR / 'instagram_summary.md'),
        'twitter': read_file_safe(BRIEFINGS_DIR / 'twitter_summary.md')
    }


def read_business_goals() -> Optional[str]:
    """Read Business_Goals.md (targets)"""
    return read_file_safe(BUSINESS_GOALS_FILE)


def get_upcoming_deadlines() -> List[Dict]:
    """Find upcoming deadlines in next 14 days from Pending_Approval/ and other sources"""
    deadlines = []
    pending_dir = BASE_DIR / 'Pending_Approval'
    inbox_dir = BASE_DIR / 'Inbox'
    needs_action_dir = BASE_DIR / 'Needs_Action'
    
    fourteen_days = datetime.now() + timedelta(days=14)
    
    for directory in [pending_dir, inbox_dir, needs_action_dir]:
        if not directory.exists():
            continue
        
        for file in directory.iterdir():
            if file.is_file():
                try:
                    mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    if mtime <= fourteen_days:
                        deadlines.append({
                            'file': file.name,
                            'location': str(directory.relative_to(BASE_DIR)),
                            'created': mtime.strftime('%Y-%m-%d'),
                            'days_old': (datetime.now() - mtime).days
                        })
                except (OSError, IOError):
                    continue
    
    return deadlines


def check_subscriptions_for_optimization() -> List[str]:
    """Check for potentially unused subscriptions"""
    suggestions = []
    
    # Check Logs directory for inactive services
    log_files = list(LOGS_DIR.glob('*.json'))
    
    # Simple heuristic: if a log file hasn't been updated in 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    for log_file in log_files:
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < thirty_days_ago:
                service_name = log_file.stem.replace('_log', '')
                suggestions.append(f"Review {service_name} subscription - no activity in 30+ days")
        except (OSError, IOError):
            continue
    
    # Check for empty pending directories
    pending_dir = BASE_DIR / 'Pending_Approval'
    if pending_dir.exists():
        pending_count = len(list(pending_dir.glob('*.md')))
        if pending_count > 10:
            suggestions.append(f"Clear backlog: {pending_count} items in Pending_Approval/")
    
    return suggestions


def analyze_bottlenecks(completed_tasks: List[Dict]) -> List[str]:
    """Identify tasks that took more than expected"""
    bottlenecks = []
    
    # Look for tasks with multiple iterations or long processing times
    for task in completed_tasks:
        content = task.get('content_preview', '').lower()
        
        # Keywords indicating difficulty
        difficulty_keywords = ['retry', 'failed', 'error', 'blocked', 'stuck', 'issue', 'problem']
        
        if any(kw in content for kw in difficulty_keywords):
            bottlenecks.append(f"{task['filename']}: May have encountered issues")
    
    return bottlenecks[:5]  # Top 5 bottlenecks


def build_briefing_prompt(data: Dict[str, Any]) -> str:
    """Build the Claude CLI prompt with all collected data"""
    
    prompt = """You are a senior business analyst AI. Analyze this week's data and generate a comprehensive Monday Morning CEO Briefing.

================================================================================
WEEKLY DATA SUMMARY
================================================================================

## COMPLETED TASKS (Last 7 Days)
"""
    
    # Add completed tasks
    if data['completed_tasks']:
        for task in data['completed_tasks']:
            prompt += f"\n### {task['filename']}\n"
            prompt += f"Completed: {task['completed_date']}\n"
            prompt += f"Preview: {task['content_preview']}\n"
    else:
        prompt += "\n*No completed tasks found in the last 7 days.*\n"
    
    # Add accounting data
    prompt += "\n\n## ACCOUNTING DATA\n"
    if data['accounting']:
        prompt += f"\n{data['accounting']}\n"
    else:
        prompt += "\n*No accounting data available.*\n"
    
    # Add Odoo revenue
    prompt += "\n\n## ODOO REVENUE SUMMARY\n"
    if data['odoo_revenue']:
        rev = data['odoo_revenue']
        prompt += f"\n- Month: {rev['month']}/{rev['year']}\n"
        prompt += f"- Total Invoiced: ${rev['total_invoiced']:,.2f}\n"
        prompt += f"- Total Paid: ${rev['total_paid']:,.2f}\n"
        prompt += f"- Outstanding: ${rev['total_outstanding']:,.2f}\n"
        prompt += f"- Invoice Count: {rev['invoice_count']}\n"
    else:
        prompt += "\n*Could not retrieve Odoo revenue data.*\n"
    
    # Add social media summaries
    prompt += "\n\n## SOCIAL MEDIA PERFORMANCE\n"
    if data['social']['facebook']:
        prompt += f"\n### Facebook\n{data['social']['facebook']}\n"
    if data['social']['instagram']:
        prompt += f"\n### Instagram\n{data['social']['instagram']}\n"
    if data['social']['twitter']:
        prompt += f"\n### Twitter\n{data['social']['twitter']}\n"
    if not any(data['social'].values()):
        prompt += "\n*No social media summaries available.*\n"
    
    # Add business goals
    prompt += "\n\n## BUSINESS GOALS & TARGETS\n"
    if data['business_goals']:
        prompt += f"\n{data['business_goals']}\n"
    else:
        prompt += "\n*No business goals file found.*\n"
    
    # Add upcoming deadlines
    prompt += "\n\n## UPCOMING DEADLINES (Next 14 Days)\n"
    if data['deadlines']:
        for deadline in data['deadlines'][:10]:
            prompt += f"\n- **{deadline['file']}** (in {deadline['location']}, {deadline['days_old']} days old)"
    else:
        prompt += "\n*No upcoming deadlines identified.*\n"
    
    # Add cost optimization suggestions
    prompt += "\n\n## COST OPTIMIZATION OPPORTUNITIES\n"
    if data['cost_suggestions']:
        for suggestion in data['cost_suggestions']:
            prompt += f"\n- {suggestion}"
    else:
        prompt += "\n*No obvious cost optimization opportunities identified.*\n"
    
    # Add bottlenecks
    prompt += "\n\n## POTENTIAL BOTTLENECKS\n"
    if data['bottlenecks']:
        for bottleneck in data['bottlenecks']:
            prompt += f"\n- {bottleneck}"
    else:
        prompt += "\n*No significant bottlenecks identified.*\n"
    
    # Add the actual instruction
    prompt += """

================================================================================
YOUR TASK: Generate Monday Morning CEO Briefing
================================================================================

Based on the data above, generate a clean, executive-level briefing with these exact sections:

1. **Executive Summary** (3 sentences max - the most important takeaway)

2. **Revenue Performance**
   - Actual vs Target (compare to goals)
   - Week-over-week trend
   - Key drivers

3. **Completed Tasks This Week**
   - Summary of what was accomplished
   - Highlight major wins

4. **Bottlenecks & Blockers**
   - Tasks that took more than expected
   - What slowed us down

5. **Social Media Performance**
   - Combined reach and engagement
   - Best performing platform
   - Recommendations

6. **Cost Optimization Suggestions**
   - Unused subscriptions to review
   - Efficiency opportunities

7. **Upcoming Deadlines** (Next 14 Days)
   - Critical dates
   - What needs attention

8. **Top 3 Recommended Actions**
   - The 3 most important things to focus on this week
   - Prioritized by impact

Format as clean, professional markdown suitable for a CEO.
Be concise but insightful. Use bullet points and tables where appropriate.

End your briefing with: **BRIEFING_COMPLETE**
"""
    
    return prompt


def run_claude_cli(prompt: str, timeout: int = 300) -> Optional[str]:
    """Run Claude CLI with the given prompt"""
    try:
        result = subprocess.run(
            ['claude', prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            log_briefing('claude_error', {'stderr': result.stderr})
            return None
            
    except subprocess.TimeoutExpired:
        log_briefing('claude_timeout', {'timeout': timeout})
        return None
    except FileNotFoundError:
        log_briefing('claude_not_found', {})
        return None
    except Exception as e:
        log_briefing('claude_error', {'error': str(e)})
        return None


def update_dashboard(briefing_file: Path) -> None:
    """Update Dashboard.md with link to new briefing"""
    briefing_link = f"[{briefing_file.name}]({briefing_file})"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    update_text = f"""
## 📊 Latest CEO Briefing
- **Generated:** {timestamp}
- **File:** {briefing_link}

---
"""
    
    if DASHBOARD_FILE.exists():
        with open(DASHBOARD_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Insert after first line (title)
        lines = content.split('\n')
        if len(lines) > 1:
            content = lines[0] + '\n' + update_text + '\n'.join(lines[1:])
        else:
            content = update_text + content
    else:
        content = f"# AI Employee Dashboard\n{update_text}"
    
    with open(DASHBOARD_FILE, 'w', encoding='utf-8') as f:
        f.write(content)


def generate_briefing() -> Dict[str, Any]:
    """Main briefing generation function"""
    print("\n" + "="*60)
    print("📊 WEEKLY CEO BRIEFING GENERATOR")
    print("="*60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    log_briefing('briefing_started', {'timestamp': datetime.now().isoformat()})
    
    # STEP A: Collect Data
    print("📥 STEP A: Collecting Data...")
    
    print("  - Reading completed tasks from Done/...")
    completed_tasks = get_done_files_last_7_days()
    print(f"    Found {len(completed_tasks)} completed tasks")
    
    print("  - Reading accounting data...")
    accounting_data = read_accounting_data()
    
    print("  - Fetching Odoo revenue summary...")
    odoo_revenue = call_odoo_revenue_summary()
    if odoo_revenue:
        print(f"    Retrieved {odoo_revenue['invoice_count']} invoices")
    
    print("  - Reading social media summaries...")
    social_summaries = read_social_summaries()
    
    print("  - Reading business goals...")
    business_goals = read_business_goals()
    
    print("  - Checking upcoming deadlines...")
    deadlines = get_upcoming_deadlines()
    print(f"    Found {len(deadlines)} items")
    
    print("  - Analyzing cost optimization opportunities...")
    cost_suggestions = check_subscriptions_for_optimization()
    
    print("  - Identifying bottlenecks...")
    bottlenecks = analyze_bottlenecks(completed_tasks)
    
    # Compile all data
    data = {
        'completed_tasks': completed_tasks,
        'accounting': accounting_data,
        'odoo_revenue': odoo_revenue,
        'social': social_summaries,
        'business_goals': business_goals,
        'deadlines': deadlines,
        'cost_suggestions': cost_suggestions,
        'bottlenecks': bottlenecks
    }
    
    log_briefing('data_collected', {
        'completed_tasks': len(completed_tasks),
        'has_accounting': bool(accounting_data),
        'has_odoo': bool(odoo_revenue),
        'deadlines': len(deadlines)
    })
    
    # STEP B: Analyze with Claude
    print("\n🤖 STEP B: Analyzing with Claude...")
    
    prompt = build_briefing_prompt(data)
    print("  - Running Claude CLI (this may take a few minutes)...")
    
    briefing_content = run_claude_cli(prompt, timeout=600)
    
    if not briefing_content:
        print("  ❌ Claude analysis failed")
        log_briefing('briefing_failed', {'reason': 'Claude CLI failed'})
        return {
            'success': False,
            'error': 'Claude CLI failed to generate briefing'
        }
    
    # Check if briefing is complete
    if 'BRIEFING_COMPLETE' not in briefing_content:
        print("  ⚠️ Warning: Briefing may be incomplete (no BRIEFING_COMPLETE marker)")
    
    # STEP C: Save Output
    print("\n💾 STEP C: Saving Output...")
    
    # Generate filename
    today = datetime.now().strftime('%Y-%m-%d')
    briefing_filename = f"{today}_Monday_Briefing.md"
    briefing_file = BRIEFINGS_DIR / briefing_filename
    
    # Extract just the briefing (remove any trailing notes)
    if 'BRIEFING_COMPLETE' in briefing_content:
        briefing_content = briefing_content.split('BRIEFING_COMPLETE')[0] + '\n\n---\n*Briefing generated automatically by AI Employee System*\n'
    
    with open(briefing_file, 'w', encoding='utf-8') as f:
        f.write(briefing_content)
    
    print(f"  - Saved to: {briefing_file}")
    
    # Update Dashboard
    print("  - Updating Dashboard.md...")
    update_dashboard(briefing_file)
    
    # Log success
    log_briefing('briefing_completed', {
        'file': str(briefing_file),
        'timestamp': datetime.now().isoformat(),
        'data_sources': {
            'completed_tasks': len(completed_tasks),
            'social_platforms': sum(1 for v in social_summaries.values() if v),
            'deadlines': len(deadlines)
        }
    })
    
    print("\n" + "="*60)
    print("✅ BRIEFING GENERATED SUCCESSFULLY")
    print("="*60)
    print(f"File: {briefing_file}")
    print("="*60 + "\n")
    
    return {
        'success': True,
        'file': str(briefing_file),
        'timestamp': datetime.now().isoformat()
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Weekly CEO Briefing Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage:
  python ceo_briefing_generator.py          # Generate briefing
  python ceo_briefing_generator.py --manual # Manual mode with prompts
        """
    )
    
    parser.add_argument(
        '--manual',
        action='store_true',
        help='Manual mode with interactive prompts'
    )
    
    args = parser.parse_args()
    
    if args.manual:
        print("Manual mode: Generating briefing now...")
    
    result = generate_briefing()
    
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
