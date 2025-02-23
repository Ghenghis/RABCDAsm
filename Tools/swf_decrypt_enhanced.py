#!/usr/bin/env python3
"""Enhanced SWF extraction with detailed tag and compression info."""
import os
import json
import logging
import zlib
from typing import Dict, List, Optional, Tuple
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Add tools directory to path
tools_dir = os.path.dirname(os.path.abspath(__file__))
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

try:
    from evony_swf.utils.encryption import EncryptionDetector
    from evony_swf.utils.compression import CompressionHandler
except ImportError as e:
    print(f"Error importing modules: {str(e)}")
    print("sys.path:", sys.path)
    raise

class SWFExtractor:
    """Extracts and analyzes SWF files."""
    
    def __init__(self, input_path: str, output_dir: str):
        self.input_path = input_path
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        self.encryption_detector = EncryptionDetector()
        self.compression_handler = CompressionHandler()
        
    def extract(self) -> bool:
        """Extract SWF file contents."""
        try:
            # Create output directories
            os.makedirs(self.output_dir, exist_ok=True)
            for subdir in ['tags', 'scripts', 'shapes', 'symbols']:
                os.makedirs(os.path.join(self.output_dir, subdir), exist_ok=True)
                
            # Read and decompress SWF
            with open(self.input_path, 'rb') as f:
                swf_data = f.read()
                
            # Analyze compression and decompress
            decompressed, compression_info = self.compression_handler.decompress_swf(swf_data)
            
            # Extract tags
            tags_info = self._extract_tags(decompressed)
            
            # Create manifest
            manifest = {
                'version': compression_info['version'],
                'compression': compression_info['method'],
                'file_length': compression_info['length'],
                'compression_params': {
                    'window_bits': compression_info['window_bits'],
                    'mem_level': compression_info['mem_level']
                },
                'tags': tags_info
            }
            
            # Write manifest
            manifest_path = os.path.join(self.output_dir, 'manifest.json')
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error extracting SWF: {str(e)}")
            return False
            
    def _extract_tags(self, data: bytes) -> List[Dict]:
        """Extract and analyze tags from SWF data."""
        tags = []
        offset = 0
        
        while offset < len(data):
            # Read tag header
            if offset + 2 > len(data):
                break
                
            tag_code_and_length = int.from_bytes(data[offset:offset+2], 'little')
            tag_code = tag_code_and_length >> 6
            tag_length = tag_code_and_length & 0x3F
            
            header_size = 2
            if tag_length == 0x3F:
                if offset + 6 > len(data):
                    break
                tag_length = int.from_bytes(data[offset+2:offset+6], 'little')
                header_size = 6
                
            # Extract tag data
            tag_start = offset + header_size
            tag_end = tag_start + tag_length
            if tag_end > len(data):
                break
                
            tag_data = data[tag_start:tag_end]
            
            # Analyze encryption
            encryption_info = self.encryption_detector.analyze_tag(tag_data, tag_code)
            
            # Save tag data
            tag_path = os.path.join(self.output_dir, 'tags', f'tag_{tag_code}_{offset}.bin')
            with open(tag_path, 'wb') as f:
                f.write(tag_data)
                
            # Record tag info
            tag_info = {
                'code': tag_code,
                'offset': offset,
                'length': tag_length,
                'header_size': header_size,
                'path': os.path.relpath(tag_path, self.output_dir).replace('\\', '/'),
                'encrypted': encryption_info['encrypted']
            }
            
            if encryption_info['encrypted']:
                tag_info.update({
                    'method': encryption_info['method'],
                    'key': encryption_info['key'],
                    'layers': encryption_info['layers']
                })
                
            tags.append(tag_info)
            
            # Move to next tag
            offset = tag_end
            
            # Record padding bytes
            while offset < len(data) and data[offset] == 0:
                offset += 1
                tag_info['padding'] = offset - tag_end
                
        return tags
        
def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract and analyze SWF file')
    parser.add_argument('input', help='Input SWF file')
    parser.add_argument('--output-dir', '-o', help='Output directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
    )
    
    # Default output directory
    if not args.output_dir:
        args.output_dir = 'test_output'
        
    # Extract SWF
    extractor = SWFExtractor(args.input, args.output_dir)
    if extractor.extract():
        print(f"Extraction complete. Output in: {args.output_dir}")
    else:
        print("Extraction failed. Check logs for details.")
        exit(1)
        
if __name__ == '__main__':
    main()
