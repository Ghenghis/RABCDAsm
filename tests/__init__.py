"""
RABCDAsm Test Suite
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Test data paths
SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), 'sample_data')
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_output')
