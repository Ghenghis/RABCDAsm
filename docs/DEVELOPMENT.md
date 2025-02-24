# RABCDAsm Development Guide

## Project Context

RABCDAsm is an ActionScript Bytecode (ABC) Disassembler and Assembler, designed for analyzing and modifying Flash SWF files. The project focuses on:

- ABC tag extraction and analysis
- SWF file structure manipulation
- Flash protection mechanism analysis
- ActionScript code reconstruction

## Code Organization

```
RABCDAsm/
├── src/                    # Core functionality
│   ├── __init__.py        # Package initialization
│   ├── abcfile.py         # ABC file handling
│   ├── assembler.py       # ABC assembly
│   └── swffile.py         # SWF file operations
│
├── Tools/                  # Analysis and utility tools
│   ├── flash/             # Flash-specific tools
│   │   ├── encryption/    # Encryption handlers
│   │   ├── compression/   # ZLIB tools
│   │   └── abc/          # ABC processors
│   ├── binary/           # Binary analysis
│   └── network/          # Network analysis
│
└── tests/                 # Test suite
    ├── unit/             # Unit tests
    ├── integration/      # Integration tests
    └── data/            # Test data files
```

## Coding Conventions

### Python Style Guide

1. **Type Hints**:
```python
from typing import List, Dict, Optional, Union

def process_abc_tag(
    tag_data: bytes,
    offset: int = 0,
    *,
    decrypt: bool = False
) -> Optional[Dict[str, Union[int, bytes]]]:
    """Process an ABC tag from the SWF file.

    Args:
        tag_data: Raw bytes of the ABC tag
        offset: Starting offset in the data
        decrypt: Whether to attempt decryption

    Returns:
        Dict containing processed tag data, or None if invalid
    """
    # Implementation
```

2. **Google-Style Docstrings**:
```python
def analyze_swf(
    file_path: str,
    analysis_type: str = "full"
) -> Dict[str, Any]:
    """Analyzes a SWF file for ABC content and protection mechanisms.

    Performs detailed analysis of SWF file structure, including ABC tags,
    encryption methods, and compression types.

    Args:
        file_path: Path to the SWF file
        analysis_type: Type of analysis to perform ("full", "quick", "deep")

    Returns:
        Dictionary containing analysis results with the following structure:
        {
            'abc_tags': List[Dict],
            'encryption': Dict[str, Any],
            'compression': str,
            'metadata': Dict[str, Any]
        }

    Raises:
        FileNotFoundError: If the SWF file doesn't exist
        InvalidSWFError: If the file is not a valid SWF
    """
    # Implementation
```

### Testing Requirements

1. **Test Organization**:
```python
# tests/test_abc_analysis.py

import pytest
from src.abcfile import ABCFile

@pytest.fixture
def sample_abc_file():
    """Fixture providing a sample ABC file for testing."""
    return ABCFile.from_bytes(TEST_DATA)

def test_abc_tag_extraction(sample_abc_file):
    """Test ABC tag extraction from SWF."""
    assert sample_abc_file.has_valid_header()
    assert len(sample_abc_file.constants) > 0

@pytest.mark.parametrize("encryption_type", [
    "xor",
    "rc4",
    "custom"
])
def test_encryption_handling(sample_abc_file, encryption_type):
    """Test handling of different encryption types."""
    # Test implementation
```

2. **Test Coverage Requirements**:
- Minimum 80% code coverage
- All public APIs must have tests
- Integration tests for main workflows
- Performance tests for critical operations

### Error Handling

```python
class ABCError(Exception):
    """Base exception for ABC-related errors."""
    pass

class InvalidABCTagError(ABCError):
    """Raised when an ABC tag is malformed."""
    pass

class EncryptionError(ABCError):
    """Raised when encryption/decryption fails."""
    pass

def process_tag(tag_data: bytes) -> None:
    """Process an ABC tag with proper error handling."""
    try:
        result = analyze_tag(tag_data)
        if not result.is_valid:
            raise InvalidABCTagError("Malformed ABC tag")
    except EncryptionError as e:
        logger.error(f"Encryption error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise ABCError(f"Failed to process tag: {e}")
```

## Performance Guidelines

1. **Memory Management**:
```python
def process_large_swf(file_path: str, chunk_size: int = 8192):
    """Process large SWF files in chunks to manage memory."""
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            process_chunk(chunk)
            gc.collect()  # Force garbage collection
```

2. **Optimization Tips**:
- Use generators for large datasets
- Implement caching for frequent operations
- Profile code regularly
- Use appropriate data structures

## Security Considerations

1. **Input Validation**:
```python
def validate_swf_header(header: bytes) -> bool:
    """Validate SWF file header."""
    if len(header) < 8:
        raise ValueError("Invalid header length")
    if header[:3] not in (b'FWS', b'CWS', b'ZWS'):
        raise ValueError("Invalid signature")
    return True
```

2. **File Operations**:
```python
from pathlib import Path

def safe_file_operations(file_path: str) -> None:
    """Safely handle file operations."""
    path = Path(file_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not path.suffix.lower() == '.swf':
        raise ValueError("Invalid file type")
```
