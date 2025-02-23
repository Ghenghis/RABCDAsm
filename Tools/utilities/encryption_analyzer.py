#!/usr/bin/env python3
"""
Enhanced encryption analyzer for Evony SWF files.
Handles all special tags with complete decryption support.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

@dataclass
class DecryptionResult:
    """Result of decryption operation."""
    success: bool
    decrypted: Optional[bytes] = None
    details: Dict = None

class EncryptionAnalyzer:
    """Analyze and decrypt special encrypted tags."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def setup_rc4_state(self, key: Union[str, bytes]) -> List[int]:
        """Initialize RC4 state array."""
        S = list(range(256))
        j = 0
        key_bytes = key.encode() if isinstance(key, str) else key
        
        for i in range(256):
            j = (j + S[i] + key_bytes[i % len(key_bytes)]) % 256
            S[i], S[j] = S[j], S[i]
            
        return S
        
    def decrypt_rc4(self, data: bytes, key: Union[str, bytes]) -> bytes:
        """Decrypt data using RC4 algorithm."""
        S = self.setup_rc4_state(key)
        i = j = 0
        result = bytearray()
        
        for byte in data:
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            k = S[(S[i] + S[j]) % 256]
            result.append(byte ^ k)
            
        return bytes(result)
        
    def decrypt_xor_pattern(self, data: bytes, key: int = 0x55) -> bytes:
        """Decrypt data using XOR pattern."""
        result = bytearray()
        current_key = key
        
        for i, byte in enumerate(data):
            result.append(byte ^ current_key)
            # Rotate key every 2 bytes
            if i % 2 == 1:
                current_key = ((current_key << 1) | (current_key >> 7)) & 0xFF
                
        return bytes(result)
        
    def analyze_tag_449(self, data: bytes) -> DecryptionResult:
        """
        Analyze and decrypt Tag 449 (multi-layer encryption).
        Layer 1: XOR with static key
        Layer 2: RC4 with "Evony" key
        Layer 3: Position-based XOR
        """
        try:
            if len(data) < 4:
                return DecryptionResult(False, None, {'error': 'Data too short'})
                
            # Get layer count from header
            layer_count = data[0]
            if layer_count < 1 or layer_count > 3:
                return DecryptionResult(False, None, {'error': f'Invalid layer count: {layer_count}'})
                
            # Preserve header
            header = data[:4]
            encrypted = data[4:]
            current = encrypted
            
            # Layer 1: XOR
            if layer_count >= 1:
                current = self.decrypt_xor_pattern(current)
                
            # Layer 2: RC4
            if layer_count >= 2 and len(current) > 16:
                current = self.decrypt_rc4(current, "Evony")
                
            # Layer 3: Position-based XOR
            if layer_count >= 3 and len(current) > 16:
                result = bytearray()
                for i, byte in enumerate(current):
                    key = (i * 0x55) & 0xFF
                    result.append(byte ^ key)
                current = bytes(result)
                
            return DecryptionResult(True, header + current, {
                'layer_count': layer_count,
                'original_size': len(data),
                'decrypted_size': len(current) + 4
            })
            
        except Exception as e:
            self.logger.error(f"Error analyzing tag 449: {e}", exc_info=True)
            return DecryptionResult(False, None, {'error': str(e)})
            
    def analyze_tag_233(self, data: bytes) -> DecryptionResult:
        """
        Analyze and decrypt Tag 233 (XOR patterns).
        Supports multiple XOR pattern types.
        """
        try:
            if len(data) < 2:
                return DecryptionResult(False, None, {'error': 'Data too short'})
                
            # Get pattern type from header
            pattern_type = data[0] & 0x0F
            if pattern_type > 2:
                return DecryptionResult(False, None, {'error': f'Invalid pattern type: {pattern_type}'})
                
            # Preserve header
            header = data[:2]
            encrypted = data[2:]
            
            # Apply appropriate XOR pattern
            if pattern_type == 0:
                # Basic single-byte XOR
                decrypted = self.decrypt_xor_pattern(encrypted, 0x55)
            elif pattern_type == 1:
                # Two-byte pattern
                result = bytearray()
                pattern = [0x55, 0xAA]
                for i, byte in enumerate(encrypted):
                    result.append(byte ^ pattern[i % 2])
                decrypted = bytes(result)
            else:
                # Three-byte pattern
                result = bytearray()
                pattern = [0x55, 0xAA, 0x55]
                for i, byte in enumerate(encrypted):
                    result.append(byte ^ pattern[i % 3])
                decrypted = bytes(result)
                
            return DecryptionResult(True, header + decrypted, {
                'pattern_type': pattern_type,
                'original_size': len(data),
                'decrypted_size': len(decrypted) + 2
            })
            
        except Exception as e:
            self.logger.error(f"Error analyzing tag 233: {e}", exc_info=True)
            return DecryptionResult(False, None, {'error': str(e)})
            
    def analyze_tag_396(self, data: bytes) -> DecryptionResult:
        """
        Analyze and decrypt Tag 396 (RC4 encryption).
        Uses modified RC4 with position-based stream modifications.
        """
        try:
            if len(data) < 3:
                return DecryptionResult(False, None, {'error': 'Data too short'})
                
            # Preserve header
            header = data[:3]
            encrypted = data[3:]
            
            # Apply RC4 decryption
            decrypted = self.decrypt_rc4(encrypted, "Evony")
            
            # Apply position-based modifications
            result = bytearray()
            for i, byte in enumerate(decrypted):
                modifier = (i * 0x33) & 0xFF
                result.append(byte ^ modifier)
                
            return DecryptionResult(True, header + bytes(result), {
                'original_size': len(data),
                'decrypted_size': len(result) + 3
            })
            
        except Exception as e:
            self.logger.error(f"Error analyzing tag 396: {e}", exc_info=True)
            return DecryptionResult(False, None, {'error': str(e)})
            
    def analyze_abc_tag(self, data: bytes) -> DecryptionResult:
        """
        Analyze and decrypt ABC tag strings.
        Handles both constant pool and string pool encryption.
        """
        try:
            if len(data) < 4:
                return DecryptionResult(False, None, {'error': 'Data too short'})
                
            # Check for encryption markers
            if data[0:2] != b'\xBF\x14':
                return DecryptionResult(True, data, {'encrypted': False})
                
            # Get key from header
            key = 0
            for byte in data[2:6]:
                key = (key << 8) | byte
            key &= 0xFFFFFFFF
            
            # Decrypt content
            encrypted = data[6:]
            result = bytearray()
            
            for i, byte in enumerate(encrypted):
                # Mix key based on position
                mixed_key = (key + i * 0x55) & 0xFF
                result.append(byte ^ mixed_key)
                
            return DecryptionResult(True, data[:6] + bytes(result), {
                'key': key,
                'original_size': len(data),
                'decrypted_size': len(result) + 6
            })
            
        except Exception as e:
            self.logger.error(f"Error analyzing ABC tag: {e}", exc_info=True)
            return DecryptionResult(False, None, {'error': str(e)})

def main():
    """Main entry point."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Check arguments
    if len(sys.argv) != 3:
        print("Usage: analyze_encryption.py <tag_file> <output_dir>")
        sys.exit(1)
        
    tag_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    # Create analyzer
    analyzer = EncryptionAnalyzer()
    
    try:
        # Read tag data
        with open(tag_path, 'rb') as f:
            data = f.read()
            
        # Determine tag type from filename
        tag_code = int(os.path.basename(tag_path).split('_')[1].split('.')[0])
        
        # Analyze based on tag type
        if tag_code == 449:
            result = analyzer.analyze_tag_449(data)
        elif tag_code == 233:
            result = analyzer.analyze_tag_233(data)
        elif tag_code == 396:
            result = analyzer.analyze_tag_396(data)
        elif tag_code == 0:
            result = analyzer.analyze_abc_tag(data)
        else:
            logger.error(f"Unsupported tag type: {tag_code}")
            sys.exit(1)
            
        if result and result.get('decrypted'):
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Save decrypted data
            output_path = os.path.join(output_dir, f"decrypted_tag_{tag_code}.bin")
            with open(output_path, 'wb') as f:
                f.write(result['decrypted'])
                
            # Save analysis results
            result_path = os.path.join(output_dir, f"analysis_tag_{tag_code}.json")
            with open(result_path, 'w') as f:
                json.dump(result['details'], f, indent=2)
                
            logger.info(f"Analysis completed successfully for tag {tag_code}")
        else:
            logger.error(f"Analysis failed for tag {tag_code}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
