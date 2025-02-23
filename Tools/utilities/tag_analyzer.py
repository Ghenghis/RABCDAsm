#!/usr/bin/env python3
"""
Special Tag Analyzer for Evony SWF Tags
Focuses on tags 233, 396, and 449 with their specific encryption patterns
"""

import os
import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from Crypto.Cipher import ARC4
from evony_swf.analyzers.pattern_analyzer import PatternAnalyzer

class SpecialTagAnalyzer:
    """Analyzer for special encrypted tags in Evony SWF."""
    
    SPECIAL_TAGS = {
        233: {
            'name': 'Special Data Tag',
            'encryption': ['xor'],
            'keys': [b'\x55', b'\x55\xAA'],
            'header_size': 2
        },
        396: {
            'name': 'Custom Data Tag',
            'encryption': ['rc4'],
            'keys': [b'Evony'],
            'header_size': 3
        },
        449: {
            'name': 'Multi-Layer Tag',
            'encryption': ['xor', 'rc4'],
            'keys': [b'\x55', b'Evony'],
            'header_size': 4
        }
    }
    
    def __init__(self, tags_dir: str, output_dir: str):
        """Initialize analyzer with directories."""
        self.tags_dir = Path(tags_dir)
        self.output_dir = Path(output_dir)
        self.pattern_analyzer = PatternAnalyzer()
        self.logger = logging.getLogger(__name__)
        
        # Setup output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def analyze_tag(self, tag_data: bytes, tag_code: int) -> Dict:
        """Analyze a single tag instance."""
        if tag_code not in self.SPECIAL_TAGS:
            return {'success': False, 'error': 'Not a special tag type'}
            
        tag_info = self.SPECIAL_TAGS[tag_code]
        header = tag_data[:tag_info['header_size']]
        data = tag_data[tag_info['header_size']:]
        
        results = {
            'tag_code': tag_code,
            'tag_name': tag_info['name'],
            'header': header.hex(),
            'size': len(tag_data),
            'decryption_attempts': []
        }
        
        # Try each encryption method
        for method, key in zip(tag_info['encryption'], tag_info['keys']):
            attempt = {'method': method, 'key': key.hex()}
            
            try:
                if method == 'xor':
                    decrypted = self._decrypt_xor(data, key)
                elif method == 'rc4':
                    decrypted = self._decrypt_rc4(data, key)
                    
                attempt.update({
                    'success': True,
                    'hash': hashlib.md5(decrypted).hexdigest(),
                    'sample': decrypted[:20].hex()
                })
                
            except Exception as e:
                attempt.update({
                    'success': False,
                    'error': str(e)
                })
                
            results['decryption_attempts'].append(attempt)
            
        return results
        
    def analyze_all_tags(self) -> Dict:
        """Analyze all instances of special tags."""
        results = {}
        
        for tag_code in self.SPECIAL_TAGS:
            tag_results = []
            tag_pattern = f"tag_{tag_code}_*.bin"
            
            for tag_file in self.tags_dir.glob(tag_pattern):
                with open(tag_file, 'rb') as f:
                    tag_data = f.read()
                    
                analysis = self.analyze_tag(tag_data, tag_code)
                analysis['file'] = tag_file.name
                tag_results.append(analysis)
                
            if tag_results:
                results[tag_code] = tag_results
                
        # Save results
        output_file = self.output_dir / 'special_tags_analysis.json'
        with open(output_file, 'w') as f:
            import json
            json.dump(results, f, indent=2)
            
        return results
        
    def _decrypt_xor(self, data: bytes, key: bytes) -> bytes:
        """XOR decrypt data with key."""
        key_len = len(key)
        return bytes(b ^ key[i % key_len] for i, b in enumerate(data))
        
    def _decrypt_rc4(self, data: bytes, key: bytes) -> bytes:
        """RC4 decrypt data with key."""
        cipher = ARC4.new(key)
        return cipher.decrypt(data)

def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Default paths - adjust as needed
    tags_dir = Path('extracted_tags')
    output_dir = Path('analysis_output')
    
    analyzer = SpecialTagAnalyzer(tags_dir, output_dir)
    results = analyzer.analyze_all_tags()
    
    logger.info(f"Analysis complete. Results saved to {output_dir / 'special_tags_analysis.json'}")
    
if __name__ == '__main__':
    main()
