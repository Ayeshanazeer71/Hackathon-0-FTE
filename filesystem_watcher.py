#!/usr/bin/env python3
"""
File System Watcher for Personal AI Employee System

Monitors the Inbox folder for new files and moves them to Needs_Action
with accompanying metadata files.
"""

import argparse
import logging
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class InboxEventHandler(FileSystemEventHandler):
    """Handles file creation events in the Inbox folder."""

    def __init__(self, source_dir: Path, dest_dir: Path, dry_run: bool = False):
        super().__init__()
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.dry_run = dry_run

    def on_created(self, event):
        """Called when a file or directory is created."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Skip hidden files and temporary files
        if file_path.name.startswith('.') or file_path.name.endswith('.tmp'):
            logger.debug(f"Ignoring temporary/hidden file: {file_path.name}")
            return

        # Skip metadata files we create
        if file_path.suffix == '.md' and self._is_metadata_file(file_path):
            return

        logger.info(f"New file detected: {file_path.name}")
        self.process_new_file(file_path)

    def _is_metadata_file(self, file_path: Path) -> bool:
        """Check if file is a metadata file created by this script."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(100)
                return 'type: file_drop' in content
        except Exception:
            return False

    def process_new_file(self, file_path: Path):
        """Process a newly detected file."""
        try:
            # Wait briefly to ensure file is fully written
            time.sleep(0.5)

            if not file_path.exists():
                logger.warning(f"File no longer exists: {file_path.name}")
                return

            # Get file info
            file_size = file_path.stat().st_size
            timestamp = datetime.now().isoformat()

            if self.dry_run:
                logger.info(f"[DRY-RUN] Would copy {file_path.name} ({file_size} bytes) to Needs_Action/")
                logger.info(f"[DRY-RUN] Would create metadata file: {file_path.stem}.md")
                return

            # Ensure destination directory exists
            self.dest_dir.mkdir(parents=True, exist_ok=True)

            # Copy file to Needs_Action
            dest_path = self.dest_dir / file_path.name
            shutil.copy2(file_path, dest_path)
            logger.info(f"Copied {file_path.name} to Needs_Action/")

            # Create metadata file
            metadata_path = self.dest_dir / f"{file_path.stem}.md"
            self.create_metadata_file(metadata_path, file_path.name, file_size, timestamp)
            logger.info(f"Created metadata file: {metadata_path.name}")

            # Remove original from Inbox
            file_path.unlink()
            logger.info(f"Removed original from Inbox: {file_path.name}")

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {str(e)}")

    def create_metadata_file(self, metadata_path: Path, original_name: str, 
                             file_size: int, timestamp: str):
        """Create a metadata markdown file."""
        metadata_content = f"""---
type: file_drop
original_name: {original_name}
file_size: {file_size}
dropped_at: {timestamp}
status: pending
---

New file dropped and ready for processing.
"""
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(metadata_content)


def validate_directories(source_dir: Path, dest_dir: Path):
    """Validate that required directories exist or can be created."""
    if not source_dir.exists():
        logger.info(f"Creating source directory: {source_dir}")
        source_dir.mkdir(parents=True, exist_ok=True)

    if not dest_dir.exists():
        logger.info(f"Creating destination directory: {dest_dir}")
        dest_dir.mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description='File System Watcher for Personal AI Employee System'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate actions without making changes'
    )
    parser.add_argument(
        '--source',
        type=str,
        default='./Inbox',
        help='Source directory to monitor (default: ./Inbox)'
    )
    parser.add_argument(
        '--dest',
        type=str,
        default='./Needs_Action',
        help='Destination directory (default: ./Needs_Action)'
    )
    args = parser.parse_args()

    source_dir = Path(args.source).resolve()
    dest_dir = Path(args.dest).resolve()

    logger.info("=" * 50)
    logger.info("AI Employee File System Watcher")
    logger.info("=" * 50)
    logger.info(f"Source (Inbox): {source_dir}")
    logger.info(f"Destination (Needs_Action): {dest_dir}")
    logger.info(f"Dry Run: {args.dry_run}")
    logger.info("=" * 50)

    # Validate directories
    validate_directories(source_dir, dest_dir)

    # Set up the observer
    event_handler = InboxEventHandler(source_dir, dest_dir, args.dry_run)
    observer = Observer()
    observer.schedule(event_handler, str(source_dir), recursive=False)

    # Start watching
    observer.start()
    logger.info("File watcher started. Press Ctrl+C to stop.")
    logger.info(f"Monitoring: {source_dir}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping file watcher...")
        observer.stop()

    observer.join()
    logger.info("File watcher stopped.")


if __name__ == '__main__':
    main()
