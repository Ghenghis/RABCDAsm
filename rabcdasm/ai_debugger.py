"""
AI-powered debugger for ActionScript bytecode
"""

import os
from pathlib import Path
from typing import Dict, List, Any
import struct
import logging
from dataclasses import dataclass
from enum import Enum

class ErrorType(Enum):
    """Types of errors that can be detected"""
    INVALID_METHOD = "invalid_method"
    INVALID_HEADER = "invalid_header"
    CORRUPTED_DATA = "corrupted_data"
    SYNTAX_ERROR = "syntax_error"
    SEMANTIC_ERROR = "semantic_error"
    RUNTIME_ERROR = "runtime_error"
    FILE_TOO_LARGE = "file_too_large"

class ErrorSeverity(Enum):
    """Severity levels for errors"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Error:
    """Represents a detected error"""
    type: ErrorType
    severity: ErrorSeverity
    location: Dict[str, Any]
    description: str

@dataclass
class Fix:
    """Represents a suggested fix"""
    description: str
    action: str
    confidence: float

class AIDebugger:
    """AI-powered debugger for ActionScript bytecode"""
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def detect_errors(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Detect errors in ABC file
        
        Args:
            file_path: Path to ABC file
            
        Returns:
            List of detected errors
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE:
            return [{
                'type': ErrorType.FILE_TOO_LARGE.value,
                'severity': ErrorSeverity.HIGH.value,
                'location': {'offset': 0},
                'description': f'File size ({file_size} bytes) exceeds limit ({self.MAX_FILE_SIZE} bytes)'
            }]
            
        errors = []
        
        try:
            with open(file_path, 'rb') as f:
                # Read header
                header = f.read(4)
                if len(header) < 4:
                    errors.append({
                        'type': ErrorType.INVALID_HEADER.value,
                        'severity': ErrorSeverity.HIGH.value,
                        'location': {'offset': 0},
                        'description': 'Invalid ABC header'
                    })
                    return errors
                    
                # Check method count
                method_count_bytes = f.read(4)
                if len(method_count_bytes) < 4:
                    errors.append({
                        'type': ErrorType.CORRUPTED_DATA.value,
                        'severity': ErrorSeverity.HIGH.value,
                        'location': {'offset': 4},
                        'description': 'Corrupted method count'
                    })
                    return errors
                    
                method_count = struct.unpack('<I', method_count_bytes)[0]
                
                # Validate method count
                if method_count * 4 > file_size - 8:  # Header (4) + Count (4)
                    errors.append({
                        'type': ErrorType.CORRUPTED_DATA.value,
                        'severity': ErrorSeverity.HIGH.value,
                        'location': {'offset': 4},
                        'description': 'Method count exceeds file size'
                    })
                    return errors
                
                # Check method indices
                for i in range(min(method_count, 1000)):  # Limit iteration
                    method_index_bytes = f.read(4)
                    if len(method_index_bytes) < 4:
                        errors.append({
                            'type': ErrorType.CORRUPTED_DATA.value,
                            'severity': ErrorSeverity.HIGH.value,
                            'location': {'offset': 8 + i * 4},
                            'description': f'Corrupted method index at position {i}'
                        })
                        continue
                        
                    method_index = struct.unpack('<I', method_index_bytes)[0]
                    if method_index == 0xFFFFFFFF:
                        errors.append({
                            'type': ErrorType.INVALID_METHOD.value,
                            'severity': ErrorSeverity.HIGH.value,
                            'location': {'offset': 8 + i * 4},
                            'description': f'Invalid method index at position {i}'
                        })
                        
        except Exception as e:
            self.logger.error(f"Error analyzing file: {str(e)}")
            errors.append({
                'type': ErrorType.CORRUPTED_DATA.value,
                'severity': ErrorSeverity.HIGH.value,
                'location': {'offset': 0},
                'description': f'Error analyzing file: {str(e)}'
            })
            
        return errors
        
    def suggest_fixes(self, error: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest fixes for an error
        
        Args:
            error: Error to suggest fixes for
            
        Returns:
            List of suggested fixes
        """
        fixes = []
        
        if error['type'] == ErrorType.INVALID_METHOD.value:
            fixes.append({
                'description': 'Remove invalid method index',
                'action': f'Remove method at offset {error["location"]["offset"]}',
                'confidence': 0.8
            })
            fixes.append({
                'description': 'Replace with valid method index',
                'action': f'Replace index at offset {error["location"]["offset"]} with 0',
                'confidence': 0.6
            })
            
        elif error['type'] == ErrorType.INVALID_HEADER.value:
            fixes.append({
                'description': 'Rebuild ABC header',
                'action': 'Reconstruct ABC header with correct format',
                'confidence': 0.7
            })
            
        elif error['type'] == ErrorType.CORRUPTED_DATA.value:
            fixes.append({
                'description': 'Repair corrupted data',
                'action': f'Attempt to repair data at offset {error["location"]["offset"]}',
                'confidence': 0.5
            })
            fixes.append({
                'description': 'Skip corrupted section',
                'action': f'Skip corrupted data at offset {error["location"]["offset"]}',
                'confidence': 0.4
            })
            
        elif error['type'] == ErrorType.FILE_TOO_LARGE.value:
            fixes.append({
                'description': 'Split file into smaller chunks',
                'action': 'Split ABC file into multiple smaller files',
                'confidence': 0.7
            })
            
        return fixes
        
    def analyze_errors(self, file_path: str) -> Dict[str, Any]:
        """
        Perform detailed error analysis
        
        Args:
            file_path: Path to ABC file
            
        Returns:
            Analysis results
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        errors = self.detect_errors(file_path)
        
        # Count errors by severity
        severity_summary = {
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for error in errors:
            severity_summary[error['severity']] += 1
            
        # Generate fix suggestions
        fix_suggestions = []
        for error in errors:
            fixes = self.suggest_fixes(error)
            fix_suggestions.extend(fixes)
            
        return {
            'error_count': len(errors),
            'severity_summary': severity_summary,
            'fix_suggestions': fix_suggestions
        }
        
    def categorize_errors(self, file_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize errors by type
        
        Args:
            file_path: Path to ABC file
            
        Returns:
            Errors categorized by type
        """
        errors = self.detect_errors(file_path)
        
        categories = {
            'syntax': [],
            'semantic': [],
            'runtime': []
        }
        
        # Count errors by type in each category
        type_counts = {}
        
        for error in errors:
            if error['type'] in [ErrorType.INVALID_HEADER.value, ErrorType.CORRUPTED_DATA.value]:
                category = 'syntax'
            elif error['type'] == ErrorType.INVALID_METHOD.value:
                category = 'semantic'
            else:
                category = 'runtime'
                
            # Update type count
            error_type = error['type']
            if error_type not in type_counts:
                type_counts[error_type] = 0
            type_counts[error_type] += 1
            
            # Add to category with count
            categories[category].append({
                'type': error_type,
                'count': type_counts[error_type]
            })
            
        return categories
