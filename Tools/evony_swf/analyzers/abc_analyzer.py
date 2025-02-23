"""ABC tag analysis and decompilation utilities."""
import logging
import os
import subprocess
from typing import Dict, List, Optional, Tuple
from ..utils.encryption import EncryptionAnalyzer

class ABCAnalyzer:
    """Analyzes and decompiles ABC tags."""
    
    def __init__(self, as3s_path: str = "j:/AI_evony/tools/_development/tools/AS3Sorcerer/as3s.exe"):
        self.logger = logging.getLogger(__name__)
        self.as3s_path = as3s_path
        self.encryption_analyzer = EncryptionAnalyzer()
        
    def process_abc_tag(self, tag_data: bytes, output_dir: str) -> Dict:
        """Process an ABC tag and extract its contents."""
        result = {
            'success': False,
            'classes': [],
            'scripts': [],
            'errors': []
        }
        
        try:
            # First check if tag is encrypted
            encryption_info = self.encryption_analyzer.analyze_tag(tag_data, 82)  # 82 is DoABC tag
            if encryption_info['encrypted']:
                self.logger.info(f"ABC tag is encrypted using {encryption_info['method']}")
                tag_data = self.encryption_analyzer.decrypt_tag(tag_data, encryption_info)
            
            # Save ABC data to temporary file
            temp_abc = os.path.join(output_dir, "temp.abc")
            with open(temp_abc, "wb") as f:
                f.write(tag_data)
                
            # Use AS3 Sorcerer to decompile
            result.update(self._decompile_with_as3s(temp_abc, output_dir))
            
            # Clean up temp file
            os.remove(temp_abc)
            
        except Exception as e:
            self.logger.error(f"Error processing ABC tag: {str(e)}")
            result['errors'].append(str(e))
            
        return result
        
    def _decompile_with_as3s(self, abc_file: str, output_dir: str) -> Dict:
        """Decompile ABC file using AS3 Sorcerer."""
        result = {
            'success': False,
            'classes': [],
            'scripts': [],
            'errors': []
        }
        
        try:
            # Create output directory for decompiled code
            os.makedirs(output_dir, exist_ok=True)
            
            # Run AS3 Sorcerer
            cmd = [
                self.as3s_path,
                "-input", abc_file,
                "-output", output_dir,
                "-exclude", "*.p",  # Exclude p-code files
                "-timeout", "300",  # 5 minute timeout
                "-mode", "script"  # Get both scripts and classes
            ]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Process output
            if process.returncode == 0:
                result['success'] = True
                
                # Get list of decompiled files
                for root, _, files in os.walk(output_dir):
                    for file in files:
                        if file.endswith(".as"):
                            path = os.path.join(root, file)
                            if "scripts" in path:
                                result['scripts'].append(path)
                            else:
                                result['classes'].append(path)
                                
            else:
                result['errors'].append(process.stderr)
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"AS3 Sorcerer error: {str(e)}")
            result['errors'].append(str(e))
            
        except Exception as e:
            self.logger.error(f"Decompilation error: {str(e)}")
            result['errors'].append(str(e))
            
        return result
        
    def analyze_class(self, class_file: str) -> Dict:
        """Analyze a decompiled ActionScript class."""
        result = {
            'name': os.path.basename(class_file),
            'imports': [],
            'extends': None,
            'implements': [],
            'methods': [],
            'properties': []
        }
        
        try:
            with open(class_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse imports
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('import '):
                    result['imports'].append(line[7:].rstrip(';'))
                    
            # Find class declaration
            class_lines = [l for l in content.split('\n') if 'class ' in l]
            if class_lines:
                decl = class_lines[0]
                if 'extends' in decl:
                    result['extends'] = decl.split('extends')[1].split('{')[0].strip()
                if 'implements' in decl:
                    impls = decl.split('implements')[1].split('{')[0]
                    result['implements'] = [i.strip() for i in impls.split(',')]
                    
            # Find methods and properties
            lines = content.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Look for methods
                if ('function ' in line and 
                    not line.startswith('//')):
                    result['methods'].append(self._parse_method(line))
                    
                # Look for properties
                elif ('var ' in line or 'const ' in line) and not line.startswith('//'):
                    result['properties'].append(self._parse_property(line))
                    
        except Exception as e:
            self.logger.error(f"Error analyzing class {class_file}: {str(e)}")
            
        return result
        
    def _parse_method(self, line: str) -> Dict:
        """Parse a method declaration line."""
        result = {
            'name': '',
            'access': 'public',
            'static': False,
            'returns': 'void',
            'params': []
        }
        
        # Check access modifier
        if 'private ' in line:
            result['access'] = 'private'
        elif 'protected ' in line:
            result['access'] = 'protected'
            
        # Check if static
        if 'static ' in line:
            result['static'] = True
            
        # Get method name
        name_start = line.find('function ') + 9
        name_end = line.find('(', name_start)
        result['name'] = line[name_start:name_end].strip()
        
        # Get parameters
        params_start = line.find('(') + 1
        params_end = line.find(')', params_start)
        params = line[params_start:params_end].split(',')
        
        for param in params:
            param = param.strip()
            if param:
                param_parts = param.split(':')
                param_info = {
                    'name': param_parts[0].strip(),
                    'type': param_parts[1].strip() if len(param_parts) > 1 else 'Object'
                }
                result['params'].append(param_info)
                
        # Get return type
        if ':' in line[params_end:]:
            result['returns'] = line[params_end:].split(':')[1].split('{')[0].strip()
            
        return result
        
    def _parse_property(self, line: str) -> Dict:
        """Parse a property declaration line."""
        result = {
            'name': '',
            'type': 'Object',
            'access': 'public',
            'static': False,
            'const': False
        }
        
        # Check if const
        if line.startswith('const '):
            result['const'] = True
            
        # Check access modifier
        if 'private ' in line:
            result['access'] = 'private'
        elif 'protected ' in line:
            result['access'] = 'protected'
            
        # Check if static
        if 'static ' in line:
            result['static'] = True
            
        # Get name and type
        parts = line.split('=')[0].strip().split(':')
        name_parts = parts[0].split(' ')
        result['name'] = name_parts[-1].strip()
        
        if len(parts) > 1:
            result['type'] = parts[1].strip()
            
        return result
