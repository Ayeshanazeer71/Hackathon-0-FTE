#!/usr/bin/env python3
"""
Claude Reasoning Loop Orchestrator for Personal AI Employee System

Watches Needs_Action/ folder and automatically triggers Claude CLI to process
new files, generate Plans, and update Dashboard.
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Set, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Claude trigger prompt template
CLAUDE_PROMPT = """Read the file Needs_Action/{filename}. Then read Company_Handbook.md. Based on the rules, create a detailed action plan in Plans/PLAN_{plan_name} with checkboxes for every required step. If any step requires human approval based on handbook rules, create an approval request in Pending_Approval/ instead. Finally update Dashboard.md Last Check timestamp and Pending Actions section. End your response with: PLAN_CREATED"""

# Success marker that Claude should output
SUCCESS_MARKER = "PLAN_CREATED"

# Maximum retries for failed processing
MAX_RETRIES = 2


class Orchestrator:
    """Orchestrates Claude CLI to process files in Needs_Action/."""

    def __init__(self, base_dir: Path, processed_file: Path, dry_run: bool = False):
        self.base_dir = base_dir
        self.processed_file = processed_file
        self.dry_run = dry_run
        self.needs_action_dir = base_dir / 'Needs_Action'
        self.plans_dir = base_dir / 'Plans'
        self.logs_dir = base_dir / 'Logs'
        self.failed_dir = self.logs_dir / 'failed'
        self.dashboard_file = base_dir / 'Dashboard.md'
        self.handbook_file = base_dir / 'Company_Handbook.md'
        self.processed_files: Set[str] = set()

    def ensure_directories(self):
        """Ensure all required directories exist."""
        self.needs_action_dir.mkdir(parents=True, exist_ok=True)
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.failed_dir.mkdir(parents=True, exist_ok=True)

    def load_processed_files(self):
        """Load set of already processed filenames."""
        if self.processed_file.exists():
            try:
                with open(self.processed_file, 'r', encoding='utf-8') as f:
                    self.processed_files = set(line.strip() for line in f if line.strip())
                logger.info(f"Loaded {len(self.processed_files)} processed file records")
            except Exception as e:
                logger.error(f"Error loading processed files: {e}")
                self.processed_files = set()
        else:
            self.processed_files = set()

    def save_processed_file(self, filename: str):
        """Save a filename to the processed file."""
        try:
            with open(self.processed_file, 'a', encoding='utf-8') as f:
                f.write(f"{filename}\n")
            self.processed_files.add(filename)
        except Exception as e:
            logger.error(f"Error saving processed file: {e}")

    def is_file_processed(self, filename: str) -> bool:
        """Check if a file has already been processed."""
        return filename in self.processed_files

    def get_md_files(self) -> List[Path]:
        """Get list of .md files in Needs_Action/ that haven't been processed."""
        if not self.needs_action_dir.exists():
            return []

        files = []
        for f in self.needs_action_dir.glob('*.md'):
            if not self.is_file_processed(f.name):
                files.append(f)

        return sorted(files, key=lambda x: x.stat().st_mtime)

    def trigger_claude(self, filename: str) -> Tuple[bool, str]:
        """
        Trigger Claude CLI with the processing prompt.
        Returns (success, output/error_message)
        """
        plan_name = filename.replace('.md', '')
        prompt = CLAUDE_PROMPT.format(filename=filename, plan_name=plan_name)

        logger.info(f"Triggering Claude CLI for: {filename}")

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would trigger Claude with prompt:")
            logger.info(f"[DRY-RUN] {prompt[:200]}...")
            return True, "DRY-RUN SUCCESS"

        try:
            # Run Claude CLI with the prompt
            # Using subprocess to capture output
            result = subprocess.run(
                ['claude', '--prompt', prompt],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(self.base_dir)
            )

            output = result.stdout + result.stderr

            # Check for success marker
            if SUCCESS_MARKER in output:
                logger.info("Claude completed with success marker")
                return True, output
            elif result.returncode == 0:
                # Command succeeded but no marker - might still be ok
                logger.warning("Claude completed but no success marker found")
                return True, output
            else:
                logger.error(f"Claude CLI failed with code {result.returncode}")
                return False, f"Exit code: {result.returncode}, Output: {output}"

        except subprocess.TimeoutExpired:
            logger.error("Claude CLI timed out (5 minutes)")
            return False, "Timeout: Claude took too long to respond"
        except FileNotFoundError:
            logger.error("Claude CLI not found. Is it installed and in PATH?")
            return False, "Claude CLI not found in PATH"
        except Exception as e:
            logger.error(f"Error triggering Claude: {e}")
            return False, str(e)

    def check_plan_created(self, filename: str) -> bool:
        """Check if a Plan file was created for the processed file."""
        plan_name = filename.replace('.md', '')
        
        # Look for any plan file that might have been created
        # Claude might create PLAN_YYYY-MM-DD.md or similar
        plan_files = list(self.plans_dir.glob(f'PLAN_*{plan_name}*.md'))
        
        # Also check for any recently modified plan files (last 2 minutes)
        now = datetime.now()
        for plan_file in self.plans_dir.glob('PLAN_*.md'):
            try:
                mtime = datetime.fromtimestamp(plan_file.stat().st_mtime)
                if (now - mtime).total_seconds() < 120:  # Created in last 2 minutes
                    plan_files.append(plan_file)
        
        return len(plan_files) > 0

    def update_dashboard(self, filename: str, status: str):
        """Update Dashboard.md with the processing result."""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would update Dashboard.md")
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        try:
            if not self.dashboard_file.exists():
                logger.warning("Dashboard.md not found, creating basic version")
                content = f"""---
last_updated: {datetime.now().strftime('%Y-%m-%d')}
status: active
---

# AI Employee Dashboard

## System Status
- File Watcher: RUNNING
- Last Check: {timestamp}

## Pending Actions
- {filename}: {status}

## Recently Completed
_Empty_

## Alerts
_No alerts_

---
*Updated by AI Employee*
"""
            else:
                with open(self.dashboard_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Update Last Check timestamp
                if 'Last Check:' in content:
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'Last Check:' in line:
                            lines[i] = f'- Last Check: {timestamp}'
                            break
                    content = '\n'.join(lines)
                else:
                    # Add Last Check if not present
                    content = content.replace(
                        '## System Status',
                        f'## System Status\n- Last Check: {timestamp}'
                    )

                # Update Pending Actions section
                if '## Pending Actions' in content:
                    # Add new pending action
                    pending_entry = f'- {filename}: {status}'
                    content = content.replace(
                        '## Pending Actions',
                        f'## Pending Actions\n{pending_entry}'
                    )

            with open(self.dashboard_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("Dashboard.md updated")

        except Exception as e:
            logger.error(f"Error updating Dashboard.md: {e}")

    def create_log_entry(self, filename: str, status: str, details: str = ""):
        """Create a log entry for the processing attempt."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"orchestrator_{timestamp}.md"
        log_path = self.logs_dir / log_filename

        content = f"""---
type: orchestrator_run
file: {filename}
status: {status}
timestamp: {datetime.now().isoformat()}
details: {details if details else 'None'}
---
"""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would create log: {log_filename}")
            return

        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Created log entry: {log_filename}")
        except Exception as e:
            logger.error(f"Error creating log entry: {e}")

    def move_to_failed(self, file_path: Path, error: str):
        """Move file to failed folder with error note."""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would move {file_path.name} to failed/")
            return

        try:
            # Copy to failed folder
            dest = self.failed_dir / file_path.name
            shutil.copy2(file_path, dest)

            # Create error note
            error_file = self.failed_dir / f"{file_path.stem}_error.txt"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"Processing failed\nError: {error}\nTimestamp: {datetime.now().isoformat()}\n")

            # Remove original
            file_path.unlink()
            logger.info(f"Moved {file_path.name} to failed/ with error note")

        except Exception as e:
            logger.error(f"Error moving to failed: {e}")

    def process_file(self, file_path: Path) -> bool:
        """
        Process a single file through the Claude reasoning loop.
        Returns True if successful, False otherwise.
        """
        filename = file_path.name
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        logger.info(f"[{timestamp}] Processing: {filename}")

        # Trigger Claude
        success, output = self.trigger_claude(filename)

        if success:
            # Check if plan was created
            if self.check_plan_created(filename):
                timestamp_end = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"[{timestamp_end}] Plan created successfully")
                self.update_dashboard(filename, 'processed')
                self.create_log_entry(filename, 'success', 'Plan created by Claude')
                self.save_processed_file(filename)
                return True
            else:
                logger.warning(f"Plan not detected after Claude run")
                return False
        else:
            timestamp_end = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"[{timestamp_end}] Plan creation failed")
            logger.error(f"Error: {output}")
            return False

    def run(self, check_interval: int = 60):
        """Main orchestrator loop."""
        logger.info("=" * 60)
        logger.info("AI Employee Claude Reasoning Loop Orchestrator")
        logger.info("=" * 60)
        logger.info(f"Base directory: {self.base_dir}")
        logger.info(f"Watch directory: {self.needs_action_dir}")
        logger.info(f"Check interval: {check_interval}s")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 60)

        # Ensure directories exist
        self.ensure_directories()

        # Load processed files
        self.load_processed_files()

        while True:
            try:
                # Get files to process
                files = self.get_md_files()

                if not files:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    logger.info(f"[{timestamp}] No new files to process")
                else:
                    logger.info(f"Found {len(files)} file(s) to process")

                    for file_path in files:
                        filename = file_path.name
                        retry_count = 0
                        success = False

                        while retry_count < MAX_RETRIES and not success:
                            if retry_count > 0:
                                logger.info(f"Retry attempt {retry_count + 1}/{MAX_RETRIES} for {filename}")

                            success = self.process_file(file_path)

                            if not success:
                                retry_count += 1
                                if retry_count < MAX_RETRIES:
                                    logger.info(f"Waiting 10 seconds before retry...")
                                    time.sleep(10)

                        if not success:
                            # Max retries reached, move to failed
                            logger.error(f"Failed to process {filename} after {MAX_RETRIES} attempts")
                            self.move_to_failed(file_path, f"Failed after {MAX_RETRIES} retries")
                            self.create_log_entry(filename, 'failed', f'Max retries exceeded')

                # Wait before next check
                logger.info(f"Next check in {check_interval} seconds... (Press Ctrl+C to stop)")
                time.sleep(check_interval)

            except KeyboardInterrupt:
                logger.info("Stopping orchestrator...")
                break
            except Exception as e:
                logger.error(f"Error in orchestrator loop: {e}")
                logger.info(f"Retrying in {check_interval} seconds...")
                time.sleep(check_interval)

        logger.info("Orchestrator stopped.")


def main():
    parser = argparse.ArgumentParser(
        description='Claude Reasoning Loop Orchestrator for Personal AI Employee System'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate actions without triggering Claude'
    )
    parser.add_argument(
        '--check-interval',
        type=int,
        default=60,
        help='Seconds between checks (default: 60)'
    )
    parser.add_argument(
        '--base-dir',
        type=str,
        default='.',
        help='Base directory of the vault (default: current directory)'
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    processed_file = base_dir / 'orchestrator_processed.txt'

    orchestrator = Orchestrator(
        base_dir=base_dir,
        processed_file=processed_file,
        dry_run=args.dry_run
    )

    try:
        orchestrator.run(check_interval=args.check_interval)
    except KeyboardInterrupt:
        logger.info("Orchestrator stopped by user.")
    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
