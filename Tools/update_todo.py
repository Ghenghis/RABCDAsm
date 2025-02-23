"""
Script to automatically update TODO.txt with progress and time tracking
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

class TodoUpdater:
    def __init__(self, todo_path: Path):
        self.todo_path = todo_path
        self.current_time = datetime.now()
        self.active_time = timedelta()
        self.total_estimated_time = timedelta()
        self.total_windsurf_time = timedelta()
        
    def parse_time(self, time_str: str) -> timedelta:
        """Parse time string in format 'Xh Ym' to timedelta"""
        hours = minutes = 0
        parts = time_str.strip().split()
        
        for part in parts:
            if 'h' in part:
                hours = int(part.replace('h', ''))
            elif 'm' in part:
                minutes = int(part.replace('m', ''))
                
        return timedelta(hours=hours, minutes=minutes)
    
    def format_time(self, td: timedelta) -> str:
        """Format timedelta to 'Xh Ym' string"""
        total_minutes = int(td.total_seconds() / 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes}m"
    
    def update_task_time(self, task: str, additional_time: timedelta) -> str:
        """Update Windsurf time for a task"""
        if '|' not in task:
            return task
            
        parts = task.split('|')
        if len(parts) != 3:
            return task
            
        task_name, est_time, windsurf_time = [p.strip() for p in parts]
        current_time = self.parse_time(windsurf_time.split(': ')[1])
        new_time = current_time + additional_time
        
        return f"{task_name} | {est_time} | Windsurf: {self.format_time(new_time)}"
    
    def calculate_phase_progress(self, phase_lines: List[str]) -> Tuple[int, timedelta, timedelta]:
        """Calculate progress percentage and times for a phase"""
        total_tasks = completed_tasks = 0
        phase_est = phase_actual = timedelta()
        
        for line in phase_lines:
            if line.strip().startswith('-'):
                total_tasks += 1
                if '[x]' in line:
                    completed_tasks += 1
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) == 3:
                        est = self.parse_time(parts[1].split(':')[1].strip())
                        actual = self.parse_time(parts[2].split(':')[1].strip())
                        phase_est += est
                        phase_actual += actual
        
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        return int(progress), phase_est, phase_actual
    
    def update_todo(self, completed_task: str, time_spent: timedelta):
        """Update TODO.txt with completed task and time tracking"""
        with open(self.todo_path, 'r') as f:
            lines = f.readlines()
        
        updated_lines = []
        in_relevant_phase = False
        phase_lines = []
        
        for line in lines:
            if line.startswith('##'):
                if phase_lines:
                    progress, est, actual = self.calculate_phase_progress(phase_lines)
                    updated_lines.extend(self.update_phase_summary(phase_lines, progress, est, actual))
                    phase_lines = []
                in_relevant_phase = False
            
            if completed_task in line:
                line = line.replace('[ ]', '[x]')
                line = self.update_task_time(line, time_spent)
                in_relevant_phase = True
            
            if in_relevant_phase:
                phase_lines.append(line)
            else:
                updated_lines.append(line)
        
        if phase_lines:
            progress, est, actual = self.calculate_phase_progress(phase_lines)
            updated_lines.extend(self.update_phase_summary(phase_lines, progress, est, actual))
        
        # Update project summary
        self.update_project_summary(updated_lines)
        
        with open(self.todo_path, 'w') as f:
            f.writelines(updated_lines)
    
    def update_phase_summary(self, phase_lines: List[str], progress: int, 
                           est_time: timedelta, actual_time: timedelta) -> List[str]:
        """Update phase summary with progress and times"""
        updated = []
        for line in phase_lines:
            if 'Status:' in line:
                updated.append(f"   Status: {progress}% Complete\n")
            elif 'Phase Time:' in line:
                updated.append(f"   Phase Time: Est: {self.format_time(est_time)} | "
                             f"Windsurf Active: {self.format_time(actual_time)}\n")
            else:
                updated.append(line)
        return updated
    
    def update_project_summary(self, lines: List[str]):
        """Update project summary section"""
        total_est = total_actual = timedelta()
        total_tasks = completed_tasks = 0
        
        for line in lines:
            if '|' in line and line.strip().startswith('-'):
                parts = line.split('|')
                if len(parts) == 3:
                    total_tasks += 1
                    if '[x]' in line:
                        completed_tasks += 1
                    est = self.parse_time(parts[1].split(':')[1].strip())
                    actual = self.parse_time(parts[2].split(':')[1].strip())
                    total_est += est
                    total_actual += actual
        
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        summary_lines = [
            "\n## Project Summary\n",
            f"Total Estimated Time: {self.format_time(total_est)}\n",
            f"Total Windsurf Active Time: {self.format_time(total_actual)}\n",
            f"Overall Progress: {int(progress)}%\n",
            f"\nLast Updated: {self.current_time.strftime('%Y-%m-%d %H:%M %Z')}\n",
            "Note: Times are tracked only when Windsurf is actively working on tasks.\n"
        ]
        
        # Find and replace existing summary
        summary_start = -1
        summary_end = -1
        for i, line in enumerate(lines):
            if line.strip() == "## Project Summary":
                summary_start = i
            elif summary_start != -1 and line.strip().startswith("##"):
                summary_end = i
                break
        
        if summary_start != -1:
            if summary_end == -1:
                summary_end = len(lines)
            lines[summary_start:summary_end] = summary_lines
        else:
            lines.extend(summary_lines)

if __name__ == '__main__':
    todo_path = Path(__file__).parent.parent / 'TODO.txt'
    updater = TodoUpdater(todo_path)
    
    # Example usage:
    # updater.update_todo("Build dependency tracker", timedelta(hours=2, minutes=30))
