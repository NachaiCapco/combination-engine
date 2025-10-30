from pathlib import Path
from typing import Optional
import re

def find_report_dir(report_root: Path, timestamp: Optional[str] = None) -> Optional[Path]:
    """
    Find report directory by timestamp.
    
    Args:
        report_root: Root directory containing timestamped report folders
        timestamp: Specific timestamp (e.g., "2025-10-29_19-48-12"). If None, returns latest.
    
    Returns:
        Path to report directory, or None if not found
    """
    if not report_root.exists():
        return None
    
    entries = [p for p in report_root.iterdir() if p.is_dir()]
    if not entries:
        return None
    
    # If specific timestamp requested
    if timestamp is not None:
        # Validate timestamp format (YYYY-MM-DD_HH-MM-SS)
        if not re.match(r'^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$', timestamp):
            return None  # Invalid format
        
        # Find exact match
        for entry in entries:
            if entry.name == timestamp:
                return entry
        return None  # Timestamp not found
    
    # Return latest (sorted by name, descending)
    return sorted(entries, reverse=True)[0]
