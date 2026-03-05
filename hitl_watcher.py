#!/usr/bin/env python3
"""
Human-in-the-Loop (HITL) Approval Workflow Watcher

Watches Approved/ and Rejected/ folders to execute or cancel actions
based on human decisions. Also handles expiry of pending approvals.
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Expiry time for pending approvals (24 hours)
APPROVAL_EXPIRY_HOURS = 24

# Watch interval in seconds
DEFAULT_WATCH_INTERVAL = 15


class HITLWatcher:
    """Human-in-the-Loop approval workflow watcher."""

    def __init__(self, base_dir: Path, dry_run: bool = False):
        self.base_dir = base_dir
        self.dry_run = dry_run
        self.approved_dir = base_dir / 'Approved'
        self.rejected_dir = base_dir / 'Rejected'
        self.pending_dir = base_dir / 'Pending_Approval'
        self.done_dir = base_dir / 'Done'
        self.logs_dir = base_dir / 'Logs'
        self.dashboard_file = base_dir / 'Dashboard.md'
        self.inbox_linkedin_dir = base_dir / 'Inbox' / 'linkedin_posts'
        self.processed_files: set = set()

    def ensure_directories(self):
        """Ensure all required directories exist."""
        for dir_path in [self.approved_dir, self.rejected_dir, self.pending_dir,
                         self.done_dir, self.logs_dir, self.inbox_linkedin_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def load_processed_files(self):
        """Load set of already processed filenames."""
        processed_file = self.base_dir / 'hitl_processed.txt'
        if processed_file.exists():
            try:
                with open(processed_file, 'r', encoding='utf-8') as f:
                    self.processed_files = set(line.strip() for line in f if line.strip())
                logger.info(f"Loaded {len(self.processed_files)} processed file records")
            except Exception as e:
                logger.error(f"Error loading processed files: {e}")
                self.processed_files = set()
        else:
            self.processed_files = set()

    def save_processed_file(self, filename: str):
        """Save a filename to the processed file."""
        processed_file = self.base_dir / 'hitl_processed.txt'
        try:
            with open(processed_file, 'a', encoding='utf-8') as f:
                f.write(f"{filename}\n")
            self.processed_files.add(filename)
        except Exception as e:
            logger.error(f"Error saving processed file: {e}")

    def is_file_processed(self, filename: str) -> bool:
        """Check if a file has already been processed."""
        return filename in self.processed_files

    def parse_approval_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse YAML-like frontmatter from approval file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract frontmatter between --- markers
            if not content.startswith('---'):
                logger.error(f"Invalid approval file format: {file_path.name}")
                return None

            parts = content.split('---', 2)
            if len(parts) < 3:
                logger.error(f"Missing closing --- in: {file_path.name}")
                return None

            frontmatter = parts[1].strip()
            body = parts[2].strip() if len(parts) > 2 else ""

            # Parse key-value pairs
            data = {}
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip()] = value.strip()

            # Parse created and expires timestamps
            if 'created' in data:
                try:
                    data['created_dt'] = datetime.fromisoformat(data['created'])
                except ValueError:
                    data['created_dt'] = datetime.now()

            if 'expires' in data:
                try:
                    data['expires_dt'] = datetime.fromisoformat(data['expires'])
                except ValueError:
                    data['expires_dt'] = datetime.now() + timedelta(hours=APPROVAL_EXPIRY_HOURS)

            data['body'] = body
            data['filename'] = file_path.name
            data['filepath'] = file_path

            return data

        except Exception as e:
            logger.error(f"Error parsing approval file {file_path.name}: {e}")
            return None

    def is_expired(self, data: Dict[str, Any]) -> bool:
        """Check if approval has expired."""
        if 'expires_dt' in data:
            return datetime.now() > data['expires_dt']
        elif 'created_dt' in data:
            # Default expiry: 24 hours from creation
            return datetime.now() > data['created_dt'] + timedelta(hours=APPROVAL_EXPIRY_HOURS)
        return False

    def execute_email_action(self, data: Dict[str, Any]) -> bool:
        """Execute send_email action via MCP server."""
        logger.info("Executing send_email action...")

        action_details = data.get('action_details', '')

        # Parse action details (expecting JSON or structured text)
        try:
            # Try to parse as JSON first
            details = json.loads(action_details)
            to = details.get('to', '')
            subject = details.get('subject', '')
            body = details.get('body', '')
        except json.JSONDecodeError:
            # Fallback: extract from text format
            to = self.extract_field(action_details, 'to')
            subject = self.extract_field(action_details, 'subject')
            body = self.extract_field(action_details, 'body')

        if not to or not subject:
            logger.error("Missing required email fields (to, subject)")
            return False

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would send email to: {to}, subject: {subject}")
            return True

        # Try to call email MCP server via claude CLI
        try:
            prompt = f"""Use the send_email tool to send this email:
- To: {to}
- Subject: {subject}
- Body: {body}

This email was approved by human in HITL workflow."""

            result = subprocess.run(
                ['claude', '--prompt', prompt],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.base_dir)
            )

            if result.returncode == 0:
                logger.info("Email sent successfully via MCP server")
                return True
            else:
                logger.error(f"MCP server error: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("MCP server call timed out")
            return False
        except FileNotFoundError:
            logger.error("Claude CLI not found. Email action requires MCP server.")
            return False
        except Exception as e:
            logger.error(f"Error executing email action: {e}")
            return False

    def execute_linkedin_post_action(self, data: Dict[str, Any], file_path: Path) -> bool:
        """Execute linkedin_post action by moving to Inbox/linkedin_posts/."""
        logger.info("Executing linkedin_post action...")

        action_details = data.get('action_details', '')

        # Extract post content
        try:
            details = json.loads(action_details)
            post_content = details.get('content', details.get('post', ''))
        except json.JSONDecodeError:
            post_content = self.extract_field(action_details, 'content') or action_details

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would move post to Inbox/linkedin_posts/")
            logger.info(f"[DRY-RUN] Content: {post_content[:100]}...")
            return True

        # Create post file in LinkedIn inbox
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_subject = data.get('subject', 'post')[:30].replace(' ', '_')
        post_filename = f"approved_{safe_subject}_{timestamp}.txt"
        post_path = self.inbox_linkedin_dir / post_filename

        try:
            with open(post_path, 'w', encoding='utf-8') as f:
                f.write(post_content)
            logger.info(f"Created LinkedIn post file: {post_filename}")
            return True
        except Exception as e:
            logger.error(f"Error creating LinkedIn post file: {e}")
            return False

    def execute_payment_action(self, data: Dict[str, Any]) -> bool:
        """Execute payment action - LOG ONLY, never auto-pay per Company Handbook."""
        logger.info("Processing payment action (LOG ONLY - requires manual processing)...")

        action_details = data.get('action_details', '')
        filename = data.get('filename', 'unknown')

        # Create payment log entry
        log_entry = {
            'type': 'payment_approved',
            'file': filename,
            'details': action_details,
            'approved_at': datetime.now().isoformat(),
            'status': 'pending_manual_processing',
            'note': 'Payment approved but requires manual processing per Company Handbook rules'
        }

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would log payment: {action_details[:100]}...")
            return True

        # Save to Logs directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_path = self.logs_dir / f"payment_{timestamp}.json"

        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, indent=2)
            logger.info(f"Payment logged: {log_path.name}")
            logger.warning("⚠️ PAYMENT REQUIRES MANUAL PROCESSING - Not auto-executed")
            return True
        except Exception as e:
            logger.error(f"Error logging payment: {e}")
            return False

    def extract_field(self, text: str, field: str) -> str:
        """Extract a field value from text (fallback parser)."""
        import re
        pattern = rf'{field}:\s*([^\n]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ''

    def execute_approval(self, file_path: Path) -> bool:
        """Execute an approved action based on its type."""
        data = self.parse_approval_file(file_path)

        if not data:
            logger.error(f"Failed to parse approval file: {file_path.name}")
            return False

        action_type = data.get('type', '').lower()
        logger.info(f"Executing approval type: {action_type}")

        success = False

        if action_type == 'send_email':
            success = self.execute_email_action(data)
        elif action_type == 'linkedin_post':
            success = self.execute_linkedin_post_action(data, file_path)
        elif action_type == 'payment':
            success = self.execute_payment_action(data)
        else:
            logger.warning(f"Unknown action type: {action_type}")
            success = False

        return success

    def process_rejection(self, file_path: Path):
        """Process a rejected approval file."""
        data = self.parse_approval_file(file_path)

        if not data:
            logger.error(f"Failed to parse rejection file: {file_path.name}")
            return

        logger.info(f"Processing rejection: {file_path.name}")

        # Log the rejection
        self.create_log_entry(
            filename=file_path.name,
            status='rejected',
            details=data.get('action_details', 'No details provided')[:200]
        )

        # Update Dashboard
        self.update_dashboard('rejection_processed', file_path.name)

        # Move to Done with rejected status
        self.move_to_done(file_path, status='rejected')

    def move_to_done(self, file_path: Path, status: str = 'completed'):
        """Move file to Done/ folder."""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would move {file_path.name} to Done/")
            return

        try:
            dest = self.done_dir / file_path.name
            shutil.copy2(file_path, dest)

            # Add status note
            status_file = self.done_dir / f"{file_path.stem}_status.txt"
            with open(status_file, 'w', encoding='utf-8') as f:
                f.write(f"Status: {status}\nProcessed: {datetime.now().isoformat()}\n")

            file_path.unlink()
            logger.info(f"Moved {file_path.name} to Done/ ({status})")
        except Exception as e:
            logger.error(f"Error moving to Done: {e}")

    def create_log_entry(self, filename: str, status: str, details: str = ""):
        """Create a log entry for the action."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"hitl_{timestamp}.md"
        log_path = self.logs_dir / log_filename

        content = f"""---
type: hitl_action
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

    def update_dashboard(self, action: str, filename: str):
        """Update Dashboard.md with the action result."""
        if self.dry_run:
            logger.info(f"[DRY-RUN] Would update Dashboard.md")
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        try:
            if not self.dashboard_file.exists():
                logger.warning("Dashboard.md not found, creating basic version")
                return

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

            # Add to Recently Completed section
            if '## Recently Completed' in content:
                entry = f"- [{timestamp}] HITL: {action} - {filename}"
                content = content.replace(
                    '## Recently Completed',
                    f'## Recently Completed\n{entry}'
                )

            with open(self.dashboard_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info("Dashboard.md updated")

        except Exception as e:
            logger.error(f"Error updating Dashboard.md: {e}")

    def check_expired_pending(self):
        """Check for expired files in Pending_Approval/ and move to Rejected/."""
        if not self.pending_dir.exists():
            return

        expired_count = 0
        for file_path in self.pending_dir.glob('*.md'):
            data = self.parse_approval_file(file_path)
            if data and self.is_expired(data):
                logger.info(f"Expired approval found: {file_path.name}")

                if self.dry_run:
                    logger.info(f"[DRY-RUN] Would move {file_path.name} to Rejected/ (expired)")
                    continue

                # Create expiry note
                note_file = self.rejected_dir / f"{file_path.stem}_expiry_note.txt"
                with open(note_file, 'w', encoding='utf-8') as f:
                    f.write(f"Expired — no human response\n")
                    f.write(f"Original created: {data.get('created', 'unknown')}\n")
                    f.write(f"Expired at: {datetime.now().isoformat()}\n")

                # Move to Rejected
                dest = self.rejected_dir / file_path.name
                shutil.copy2(file_path, dest)
                file_path.unlink()

                logger.info(f"Moved expired {file_path.name} to Rejected/")
                expired_count += 1

        if expired_count > 0:
            logger.info(f"Processed {expired_count} expired approval(s)")

    def process_approved_folder(self):
        """Process all files in Approved/ folder."""
        if not self.approved_dir.exists():
            return

        files = [f for f in self.approved_dir.glob('*.md') if not self.is_file_processed(f.name)]

        if not files:
            logger.debug("No new files in Approved/")
            return

        logger.info(f"Found {len(files)} approval(s) to process")

        for file_path in files:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"[{timestamp}] Processing approval: {file_path.name}")

            success = self.execute_approval(file_path)

            if success:
                self.create_log_entry(file_path.name, 'approved_executed')
                self.update_dashboard('approval_executed', file_path.name)
                self.move_to_done(file_path, status='approved')
                self.save_processed_file(file_path.name)
                logger.info(f"[{timestamp}] Approval executed successfully")
            else:
                self.create_log_entry(file_path.name, 'approved_failed')
                logger.error(f"[{timestamp}] Failed to execute approval")

    def process_rejected_folder(self):
        """Process all files in Rejected/ folder."""
        if not self.rejected_dir.exists():
            return

        files = [f for f in self.rejected_dir.glob('*.md') if not self.is_file_processed(f.name)]

        if not files:
            logger.debug("No new files in Rejected/")
            return

        logger.info(f"Found {len(files)} rejection(s) to process")

        for file_path in files:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"[{timestamp}] Processing rejection: {file_path.name}")

            self.process_rejection(file_path)
            self.save_processed_file(file_path.name)

    def run(self, check_interval: int = DEFAULT_WATCH_INTERVAL):
        """Main watcher loop."""
        logger.info("=" * 60)
        logger.info("AI Employee HITL (Human-in-the-Loop) Approval Watcher")
        logger.info("=" * 60)
        logger.info(f"Base directory: {self.base_dir}")
        logger.info(f"Watch interval: {check_interval}s")
        logger.info(f"Approval expiry: {APPROVAL_EXPIRY_HOURS} hours")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 60)

        # Ensure directories exist
        self.ensure_directories()

        # Load processed files
        self.load_processed_files()

        while True:
            try:
                # Check for expired pending approvals
                logger.debug("Checking for expired pending approvals...")
                self.check_expired_pending()

                # Process approved files
                logger.debug("Processing Approved/ folder...")
                self.process_approved_folder()

                # Process rejected files
                logger.debug("Processing Rejected/ folder...")
                self.process_rejected_folder()

                # Wait before next check
                logger.info(f"Next check in {check_interval} seconds... (Press Ctrl+C to stop)")
                time.sleep(check_interval)

            except KeyboardInterrupt:
                logger.info("Stopping HITL watcher...")
                break
            except Exception as e:
                logger.error(f"Error in HITL watcher loop: {e}")
                logger.info(f"Retrying in {check_interval} seconds...")
                time.sleep(check_interval)

        logger.info("HITL watcher stopped.")


def main():
    parser = argparse.ArgumentParser(
        description='HITL Approval Workflow Watcher for Personal AI Employee System'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate actions without executing'
    )
    parser.add_argument(
        '--check-interval',
        type=int,
        default=DEFAULT_WATCH_INTERVAL,
        help=f'Seconds between checks (default: {DEFAULT_WATCH_INTERVAL})'
    )
    parser.add_argument(
        '--base-dir',
        type=str,
        default='.',
        help='Base directory of the vault (default: current directory)'
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()

    watcher = HITLWatcher(
        base_dir=base_dir,
        dry_run=args.dry_run
    )

    try:
        watcher.run(check_interval=args.check_interval)
    except KeyboardInterrupt:
        logger.info("HITL watcher stopped by user.")
    except Exception as e:
        logger.error(f"HITL watcher error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
