"""
Evony Master Toolkit - Real-time SWF Analysis and Decryption
Integrates all tools for comprehensive file processing
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import argparse

from swf_decrypt_enhanced import SWFDecrypter
from evony_abc_analyzer import EvonyABCAnalyzer
from evony_full_decryptor import EvonyFullDecryptor

def json_serializable(obj: Any) -> Any:
    """Convert objects to JSON serializable format"""
    if isinstance(obj, (datetime, Path)):
        return str(obj)
    elif isinstance(obj, bytes):
        return obj.hex()
    elif isinstance(obj, dict):
        return {k: json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [json_serializable(x) for x in obj]
    return obj

class EvonyMasterToolkit:
    def __init__(self):
        """Initialize the master toolkit."""
        self.logger = logging.getLogger('evony_master_toolkit')
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Create output directories
        self.output_dir = os.path.join("analysis_results", 
                                     datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize components
        self.decrypter = SWFDecrypter()
        self.analyzer = EvonyABCAnalyzer()
        self.full_decryptor = EvonyFullDecryptor()
        
        # Analysis results
        self.analysis_results = {}
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process a file through the toolkit pipeline."""
        try:
            self.logger.info(f"Processing file: {file_path}")
            
            # Step 1: Initial decryption
            decrypted_data = self.decrypter.decrypt_file(file_path)
            decrypted_path = None
            if decrypted_data:
                # Save decrypted file
                decrypted_path = os.path.join(
                    self.output_dir,
                    f"decrypted_{os.path.basename(file_path)}"
                )
                with open(decrypted_path, 'wb') as f:
                    f.write(decrypted_data)
                
                # Run low-level analysis
                self.logger.info("Running low-level analysis...")
                self._analyze_binary(decrypted_path)
            
            # Step 2: ABC analysis
            self.logger.info("Running ABC analysis...")
            abc_results = self.analyzer.analyze_file(file_path)
            
            # Step 3: Full decryption
            self.logger.info("Running full decryption analysis...")
            decryption_results = self.full_decryptor.process_file(
                file_path,
                self.output_dir
            )
            
            # Collect all results
            results = {
                'timestamp': datetime.now().isoformat(),
                'file_path': file_path,
                'decryption': {
                    'success': decrypted_data is not None,
                    'output_path': decrypted_path
                },
                'abc_analysis': abc_results,
                'full_decryption': decryption_results
            }
            
            # Save results
            self.analysis_results[file_path] = results
            self._save_results()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing file: {e}")
            return {'error': str(e)}
    
    def _analyze_binary(self, file_path: str):
        """Perform low-level binary analysis using available tools."""
        try:
            import r2pipe
            
            # Initialize radare2
            r2 = r2pipe.open(file_path)
            r2.cmd('aaa')  # Analyze all
            
            # Get function list
            functions = r2.cmdj('aflj')
            if functions:
                # Save function analysis
                output_file = os.path.join(
                    self.output_dir,
                    f"functions_{os.path.basename(file_path)}.json"
                )
                with open(output_file, 'w') as f:
                    json.dump(functions, f, indent=2)
                
                self.logger.info(f"Found {len(functions)} functions")
                
                # Get strings
                strings = r2.cmdj('izj')
                if strings:
                    strings_file = os.path.join(
                        self.output_dir,
                        f"strings_{os.path.basename(file_path)}.json"
                    )
                    with open(strings_file, 'w') as f:
                        json.dump(strings, f, indent=2)
                    
                    self.logger.info(f"Found {len(strings)} strings")
                
                # Get imports
                imports = r2.cmdj('iij')
                if imports:
                    imports_file = os.path.join(
                        self.output_dir,
                        f"imports_{os.path.basename(file_path)}.json"
                    )
                    with open(imports_file, 'w') as f:
                        json.dump(imports, f, indent=2)
                    
                    self.logger.info(f"Found {len(imports)} imports")
            
            r2.quit()
            
        except ImportError:
            self.logger.warning("r2pipe not available, skipping binary analysis")
        except Exception as e:
            self.logger.error(f"Error in binary analysis: {e}")
    
    def _save_results(self):
        """Save analysis results to file."""
        try:
            results_file = os.path.join(
                self.output_dir,
                f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            # Convert results to JSON serializable format
            results = json_serializable(self.analysis_results)
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            self.logger.info(f"Results saved to {results_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Evony Master Toolkit')
    parser.add_argument('path', help='Path to SWF file or directory')
    parser.add_argument('--watch', action='store_true', help='Watch directory for changes')
    
    args = parser.parse_args()
    
    toolkit = EvonyMasterToolkit()
    
    try:
        if os.path.isfile(args.path):
            result = toolkit.process_file(args.path)
            print(json.dumps(result, indent=2))
        elif os.path.isdir(args.path):
            if args.watch:
                print("Directory watching not implemented yet")
            else:
                for root, _, files in os.walk(args.path):
                    for file in files:
                        if file.endswith('.swf'):
                            file_path = os.path.join(root, file)
                            toolkit.process_file(file_path)
        else:
            print(f"Path not found: {args.path}")
    except KeyboardInterrupt:
        print("\nInterrupted by user")

if __name__ == '__main__':
    main()
