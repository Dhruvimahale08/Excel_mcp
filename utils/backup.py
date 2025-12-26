"""Backup utility for Excel files."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


def create_backup(file_path: str, backup_dir: str = "backups") -> Optional[str]:
    """
    Create a timestamped backup of the Excel file.
    
    Args:
        file_path: Path to Excel file to backup
        backup_dir: Directory to store backups
    
    Returns:
        Path to backup file, or None if backup failed
    """
    try:
        source = Path(file_path)
        if not source.exists():
            return None
        
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"{source.stem}_{timestamp}{source.suffix}"
        
        # Copy file
        shutil.copy2(source, backup_file)
        
        return str(backup_file)
    except (OSError, IOError, PermissionError) as e:
        print(f"Warning: Could not create backup: {e}")
        return None

