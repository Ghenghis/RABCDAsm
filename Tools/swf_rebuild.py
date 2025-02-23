"""SWF rebuilding tool with proper compression and encryption handling."""
import os
import json
import logging
from typing import Dict, List, Optional
from evony_swf.utils.encryption import EncryptionDetector, TagDecryptor
from evony_swf.utils.compression import CompressionHandler

class SWFRebuilder:
    """Rebuilds SWF files from extracted components."""
    
    def __init__(self, manifest_path: str):
        self.logger = logging.getLogger(__name__)
        self.manifest_path = manifest_path
        self.manifest = self._load_manifest()
        self.encryption_detector = EncryptionDetector()
        self.tag_decryptor = TagDecryptor()
        self.compression_handler = CompressionHandler()
        
    def _load_manifest(self) -> Dict:
        """Load and validate the manifest file."""
        try:
            with open(self.manifest_path, 'r') as f:
                manifest = json.load(f)
                
            required_fields = ['version', 'compression', 'file_length', 'tags']
            missing_fields = [f for f in required_fields if f not in manifest]
            if missing_fields:
                raise ValueError(f"Missing required manifest fields: {', '.join(missing_fields)}")
                
            return manifest
            
        except Exception as e:
            self.logger.error(f"Error loading manifest: {str(e)}")
            raise
            
    def rebuild(self, output_path: str) -> bool:
        """Rebuild the SWF file."""
        try:
            # Collect all tag data
            tag_data_list = []
            base_dir = os.path.dirname(self.manifest_path)
            
            for tag_info in self.manifest['tags']:
                tag_path = os.path.join(base_dir, tag_info['path'])
                if not os.path.exists(tag_path):
                    raise FileNotFoundError(f"Tag file not found: {tag_path}")
                    
                with open(tag_path, 'rb') as f:
                    tag_data = f.read()
                    
                # Handle encryption if present
                if tag_info.get('encrypted'):
                    encryption_info = {
                        'encrypted': True,
                        'method': tag_info['method'],
                        'key': tag_info.get('key'),
                        'layers': tag_info.get('layers', [])
                    }
                    tag_data = self.tag_decryptor.decrypt_tag(tag_data, encryption_info)
                    
                tag_data_list.append(tag_data)
                
            # Combine all tags
            combined_data = b''.join(tag_data_list)
            
            # Compress if needed
            compression_info = {
                'method': self.manifest['compression'],
                'version': self.manifest['version'],
                'length': self.manifest['file_length']
            }
            
            if 'compression_params' in self.manifest:
                compression_info.update(self.manifest['compression_params'])
                
            final_data = self.compression_handler.compress_swf(combined_data, compression_info)
            
            # Write output file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(final_data)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error rebuilding SWF: {str(e)}")
            return False
            
def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Rebuild SWF file from manifest')
    parser.add_argument('manifest', help='Path to manifest JSON file')
    parser.add_argument('--output', '-o', required=True, help='Output SWF file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
    )
    
    # Rebuild SWF
    rebuilder = SWFRebuilder(args.manifest)
    if rebuilder.rebuild(args.output):
        print(f"Rebuild complete. Output: {args.output}")
    else:
        print("Rebuild failed. Check logs for details.")
        exit(1)
        
if __name__ == '__main__':
    main()
