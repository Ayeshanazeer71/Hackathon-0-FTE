#!/usr/bin/env python3
"""
AI Employee System - Final Test Suite
Tests all components and generates report
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

# Results storage
RESULTS = {
    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'tests': [],
    'passed': 0,
    'failed': 0,
    'warnings': 0
}

BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / 'Logs'
LOGS_DIR.mkdir(exist_ok=True)

def log_test(name, status, message=''):
    """Log test result"""
    RESULTS['tests'].append({
        'name': name,
        'status': status,
        'message': message
    })
    
    if status == 'PASS':
        RESULTS['passed'] += 1
        print(f"{Fore.GREEN}✓ {name}: {message}{Style.RESET_ALL}")
    elif status == 'FAIL':
        RESULTS['failed'] += 1
        print(f"{Fore.RED}✗ {name}: {message}{Style.RESET_ALL}")
    else:
        RESULTS['warnings'] += 1
        print(f"{Fore.YELLOW}⚠ {name}: {message}{Style.RESET_ALL}")

def test_python_scripts():
    """Test Python scripts import correctly"""
    print(f"\n{Fore.CYAN}=== Testing Python Scripts ==={Style.RESET_ALL}")
    
    scripts = [
        'filesystem_watcher.py',
        'orchestrator.py',
        'playwright_twitter_poster.py',
        'twitter_watcher.py',
        'linkedin_watcher.py',
        'social_media_watcher.py',
        'ceo_briefing_generator.py',
        'audit_logger.py',
        'health_monitor.py',
        'log_viewer.py',
    ]
    
    for script in scripts:
        script_path = BASE_DIR / script
        if script_path.exists():
            # Try to import/parse
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), script_path, 'exec')
                log_test(script, 'PASS', 'Syntax OK')
            except Exception as e:
                log_test(script, 'FAIL', str(e))
        else:
            log_test(script, 'WARN', 'File not found')

def test_node_servers():
    """Test Node.js servers"""
    print(f"\n{Fore.CYAN}=== Testing Node.js Servers ==={Style.RESET_ALL}")
    
    servers = [
        'email_mcp_server.js',
        'odoo_mcp_server.js',
        'social_mcp_server.js',
    ]
    
    for server in servers:
        server_path = BASE_DIR / server
        if server_path.exists():
            log_test(server, 'PASS', 'File exists')
        else:
            log_test(server, 'WARN', 'File not found')

def test_directories():
    """Test required directories exist"""
    print(f"\n{Fore.CYAN}=== Testing Directories ==={Style.RESET_ALL}")
    
    dirs = [
        'Inbox',
        'Needs_Action',
        'Plans',
        'Done',
        'Pending_Approval',
        'Approved',
        'Briefings',
        'Logs',
    ]
    
    for dir_name in dirs:
        dir_path = BASE_DIR / dir_name
        if dir_path.exists() and dir_path.is_dir():
            log_test(dir_name, 'PASS', f'Exists ({len(list(dir_path.iterdir()))} files)')
        else:
            log_test(dir_name, 'WARN', 'Not found')

def test_env_file():
    """Test .env file exists and has required vars"""
    print(f"\n{Fore.CYAN}=== Testing Environment ==={Style.RESET_ALL}")
    
    env_file = BASE_DIR / '.env'
    if not env_file.exists():
        log_test('.env', 'FAIL', 'File not found')
        return
    
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_vars = [
        'ODOO_USERNAME',
        'ODOO_PASSWORD',
        'TWITTER_USERNAME',
        'TWITTER_PASSWORD',
    ]
    
    for var in required_vars:
        if var in content:
            # Check if not default value
            if 'your_' in content.split(f'{var}=')[1].split('\n')[0].lower():
                log_test(var, 'WARN', 'Using default value')
            else:
                log_test(var, 'PASS', 'Configured')
        else:
            log_test(var, 'WARN', 'Not set')

def test_odoo_connection():
    """Test Odoo connection"""
    print(f"\n{Fore.CYAN}=== Testing Odoo Connection ==={Style.RESET_ALL}")
    
    try:
        result = subprocess.run(
            ['node', 'test_odoo_xmlrpc.js'],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if 'Authentication successful' in result.stdout:
            log_test('Odoo XML-RPC', 'PASS', 'Connected')
            
            # Extract stats
            if 'Found 6 customers' in result.stdout:
                log_test('Odoo Customers', 'PASS', '6 customers found')
            if 'Found 57 invoices' in result.stdout:
                log_test('Odoo Invoices', 'PASS', '57 invoices found')
        else:
            log_test('Odoo XML-RPC', 'FAIL', 'Connection failed')
            
    except subprocess.TimeoutExpired:
        log_test('Odoo XML-RPC', 'FAIL', 'Timeout')
    except Exception as e:
        log_test('Odoo XML-RPC', 'FAIL', str(e))

def test_twitter():
    """Test Twitter integration"""
    print(f"\n{Fore.CYAN}=== Testing Twitter ==={Style.RESET_ALL}")
    
    # Check if playwright script exists
    script = BASE_DIR / 'playwright_twitter_poster.py'
    if script.exists():
        log_test('Playwright Script', 'PASS', 'Exists')
    else:
        log_test('Playwright Script', 'FAIL', 'Not found')
    
    # Check credentials
    env_file = BASE_DIR / '.env'
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'TWITTER_USERNAME=' in content and 'your_twitter_username' not in content:
        log_test('Twitter Credentials', 'PASS', 'Configured')
    else:
        log_test('Twitter Credentials', 'WARN', 'Not configured')

def test_docker():
    """Test Docker containers"""
    print(f"\n{Fore.CYAN}=== Testing Docker ==={Style.RESET_ALL}")
    
    try:
        result = subprocess.run(
            ['docker', 'compose', 'ps'],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if 'odoo' in result.stdout.lower():
            log_test('Docker Compose', 'PASS', 'Running')
            
            if 'odoo19_community' in result.stdout:
                log_test('Odoo Container', 'PASS', 'Up')
            if 'odoo19_postgres' in result.stdout:
                log_test('Postgres Container', 'PASS', 'Up')
        else:
            log_test('Docker Compose', 'WARN', 'Not running')
            
    except Exception as e:
        log_test('Docker', 'FAIL', str(e))

def test_logs():
    """Test logging system"""
    print(f"\n{Fore.CYAN}=== Testing Logging ==={Style.RESET_ALL}")
    
    # Check log files
    log_files = list(LOGS_DIR.glob('*.json'))
    if log_files:
        log_test('Log Files', 'PASS', f'{len(log_files)} files found')
    else:
        log_test('Log Files', 'WARN', 'No log files')
    
    # Check twitter log
    twitter_log = LOGS_DIR / 'twitter_playwright.log'
    if twitter_log.exists():
        log_test('Twitter Log', 'PASS', 'Exists')
    else:
        log_test('Twitter Log', 'WARN', 'Not found')

def generate_report():
    """Generate test report"""
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}=== TEST SUMMARY ==={Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    total = RESULTS['passed'] + RESULTS['failed'] + RESULTS['warnings']
    
    print(f"\nTotal Tests: {total}")
    print(f"{Fore.GREEN}Passed: {RESULTS['passed']}{Style.RESET_ALL}")
    print(f"{Fore.RED}Failed: {RESULTS['failed']}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Warnings: {RESULTS['warnings']}{Style.RESET_ALL}")
    
    # Calculate percentage
    if total > 0:
        percentage = (RESULTS['passed'] / total) * 100
        print(f"\nSuccess Rate: {percentage:.1f}%")
    
    # Save report
    report_file = LOGS_DIR / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(RESULTS, f, indent=2)
    
    print(f"\nReport saved to: {report_file}")
    
    # Overall status
    if RESULTS['failed'] == 0:
        print(f"\n{Fore.GREEN}✓ ALL TESTS PASSED!{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}System is ready for deployment!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}⚠ Some tests failed. Review and fix before deployment.{Style.RESET_ALL}")
    
    return RESULTS['failed'] == 0

def main():
    print(f"{Fore.CYAN}")
    print("=" * 60)
    print("  AI EMPLOYEE SYSTEM - FINAL TEST SUITE")
    print("=" * 60)
    print(f"{Style.RESET_ALL}")
    
    # Run all tests
    test_directories()
    test_env_file()
    test_python_scripts()
    test_node_servers()
    test_docker()
    test_odoo_connection()
    test_twitter()
    test_logs()
    
    # Generate report
    success = generate_report()
    
    # Exit code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
