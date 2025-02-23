"""
Quick script to analyze a SWF file
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tools.lib.swf_analyzer import SWFAnalyzer
from tools.lib.rabcdasm_wrapper import RABCDAsmWrapper

def main():
    # Initialize tools
    rabcdasm = RABCDAsmWrapper(os.path.join('tools', 'rabcdasm'))
    analyzer = SWFAnalyzer(rabcdasm)
    
    # Analyze SWF
    swf_path = os.path.join('tests', 'sample_data', 'autoevony.swf')
    results = analyzer.analyze_swf(swf_path)
    
    # Print results
    print('\nAnalysis Results for AutoEvony.swf:')
    print('-' * 40)
    
    print('\nFile Information:')
    for k, v in results['file_info'].items():
        print(f'  {k}: {v}')
        
    print('\nStructure:')
    for k, v in results['structure'].items():
        print(f'  {k}: {v}')
        
    print('\nResources:')
    for resource in results['resources']:
        print(f'  - {resource}')
        
    print('\nSecurity:')
    for k, v in results['security'].items():
        print(f'  {k}: {v}')

if __name__ == '__main__':
    main()
