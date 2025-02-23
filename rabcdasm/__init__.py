"""
RABCDAsm - ActionScript 3 Assembler/Disassembler
"""

from .tools import (
    CodeStructureAnalyzer,
    CodePattern,
    AnalysisResult,
    SecurityAnalysis,
    PerformanceAnalysis,
    Dependencies,
    Complexity
)

__version__ = "1.0.0"
__all__ = [
    'CodeStructureAnalyzer',
    'CodePattern',
    'AnalysisResult',
    'SecurityAnalysis',
    'PerformanceAnalysis',
    'Dependencies',
    'Complexity'
]