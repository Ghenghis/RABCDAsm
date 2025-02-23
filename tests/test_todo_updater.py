"""
Test suite for the TODO.txt updater
"""

import pytest
from pathlib import Path
from datetime import timedelta
import tempfile
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Tools.update_todo import TodoUpdater

@pytest.fixture
def sample_todo():
    content = """# Test Project
Start Date: 2025-02-22 05:14 MST
Active Windsurf Time: 0h 45m

## Phase 1
1. Test Component [In Progress]
   - [x] Task 1                                | Est: 2h  | Windsurf: 1h 30m
   - [ ] Task 2                                | Est: 3h  | Windsurf: 0h
   Status: 50% Complete
   Priority: High
   Phase Time: Est: 5h | Windsurf Active: 1h 30m

## Project Summary
Total Estimated Time: 5h
Total Windsurf Active Time: 1h 30m
Overall Progress: 50%

Last Updated: 2025-02-22 05:14 MST
Note: Times are tracked only when Windsurf is actively working on tasks.
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(content)
    yield Path(f.name)
    os.unlink(f.name)

def test_parse_time(sample_todo):
    updater = TodoUpdater(sample_todo)
    assert updater.parse_time("2h 30m") == timedelta(hours=2, minutes=30)
    assert updater.parse_time("0h") == timedelta(hours=0)
    assert updater.parse_time("45m") == timedelta(minutes=45)

def test_format_time(sample_todo):
    updater = TodoUpdater(sample_todo)
    assert updater.format_time(timedelta(hours=2, minutes=30)) == "2h 30m"
    assert updater.format_time(timedelta(hours=1)) == "1h 0m"
    assert updater.format_time(timedelta(minutes=45)) == "0h 45m"

def test_update_task_time(sample_todo):
    updater = TodoUpdater(sample_todo)
    task = "   - [ ] Task                                | Est: 2h  | Windsurf: 1h 30m"
    updated = updater.update_task_time(task, timedelta(hours=1))
    assert "Windsurf: 2h 30m" in updated

def test_calculate_phase_progress(sample_todo):
    updater = TodoUpdater(sample_todo)
    phase_lines = [
        "   - [x] Task 1                                | Est: 2h  | Windsurf: 1h 30m",
        "   - [ ] Task 2                                | Est: 3h  | Windsurf: 0h"
    ]
    progress, est, actual = updater.calculate_phase_progress(phase_lines)
    assert progress == 50
    assert est == timedelta(hours=5)
    assert actual == timedelta(hours=1, minutes=30)

def test_update_todo(sample_todo):
    updater = TodoUpdater(sample_todo)
    updater.update_todo("Task 2", timedelta(hours=2))
    
    with open(sample_todo) as f:
        content = f.read()
    
    assert "[x] Task 2" in content
    assert "Windsurf: 2h 0m" in content
    assert "Status: 100% Complete" in content
    assert "Total Windsurf Active Time: 3h 30m" in content
    assert "Overall Progress: 100%" in content
