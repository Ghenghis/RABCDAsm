import os
import sys
import zlib
import json
import struct
import binascii
from typing import Tuple, Optional, Dict, List
from Crypto.Cipher import AES, Blowfish
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA1, MD5
from datetime import datetime

class EvonyDecoder:
    def __init__(self):
        """Initialize Evony decoder with known keys and patterns."""
        # Known static keys
        self.static_keys = {
            'game': b'EvonyGameKey2009',
            'network': b'EvonyNetKey2009',
            'resource': b'EvonyResKey2009',
            'config': b'EvonyConfigKey2009',
            'data': b'EvonyDataKey2009'
        }
        
        # Encryption markers
        self.markers = {
            'aes': {
                'header': b'\x45\x56\x4F\x01',  # EVO1
                'salt': b'\x45\x56\x53\x4C',    # EVSL
                'resource': b'\x52\x45\x53\x01', # RES1
                'config': b'\x43\x46\x47\x01'    # CFG1
            },
            'blowfish': {
                'header': b'\x45\x56\x4F\x02',   # EVO2
                'resource': b'\x52\x45\x53\x02', # RES2
                'data': b'\x44\x41\x54\x01'      # DAT1
            },
            'xor': {
                'header': b'\x45\x56\x4F\x03',   # EVO3
                'resource': b'\x52\x45\x53\x03', # RES3
                'text': b'\x54\x58\x54\x01'      # TXT1
            }
        }
        
        # Create output directory
        self.output_dir = os.path.join("evony_decrypted", 
                                     datetime.now().strftime('%Y%m%d_%H%M%S'))
        os.makedirs(self.output_dir, exist_ok=True)
    
    def detect_encryption(self, data: bytes) -> Tuple[str, Dict[str, int]]:
        """Detect Evony encryption type and markers."""
        encryption_type = "unknown"
        markers_found = {}
        
        for enc_type, markers in self.markers.items():
            for name, pattern in markers.items():
                pos = data.find(pattern)
                if pos >= 0:
                    encryption_type = enc_type
                    markers_found[name] = pos
        
        return encryption_type, markers_found
    
    def derive_key(self, salt: bytes, password: bytes = None) -> Tuple[bytes, bytes]:
        """Derive key and IV using Evony's method."""
        if not password:
            password = self.static_keys['game']
        
        # Use PBKDF2 with SHA1
        key_iv = PBKDF2(
            password,
            salt,
            dkLen=48,  # 32 for key, 16 for IV
            count=1000,
            hmac_hash_module=SHA1
        )
        
        return key_iv[:32], key_iv[32:]
    
    def decrypt_aes(self, data: bytes, key: bytes = None, iv: bytes = None) -> Optional[bytes]:
        """Decrypt AES encrypted data."""
        try:
            # Check for salt marker
            salt_pos = data.find(self.markers['aes']['salt'])
            if salt_pos >= 0:
                salt = data[salt_pos+4:salt_pos+12]
                data = data[salt_pos+12:]
                if not key or not iv:
                    key, iv = self.derive_key(salt)
            
            # Create cipher
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted = cipher.decrypt(data)
            
            # Remove PKCS7 padding
            padding_len = decrypted[-1]
            if padding_len < 16:
                decrypted = decrypted[:-padding_len]
            
            return decrypted
            
        except Exception as e:
            print(f"AES decryption error: {e}")
            return None
    
    def decrypt_blowfish(self, data: bytes, key: bytes = None) -> Optional[bytes]:
        """Decrypt Blowfish encrypted data."""
        try:
            if not key:
                key = self.static_keys['game']
            
            # Create cipher
            cipher = Blowfish.new(key, Blowfish.MODE_ECB)
            decrypted = cipher.decrypt(data)
            
            # Remove PKCS7 padding
            padding_len = decrypted[-1]
            if padding_len < 8:
                decrypted = decrypted[:-padding_len]
            
            return decrypted
            
        except Exception as e:
            print(f"Blowfish decryption error: {e}")
            return None
    
    def decrypt_xor(self, data: bytes, key: bytes = None) -> Optional[bytes]:
        """Decrypt XOR encoded data."""
        try:
            if not key:
                key = self.static_keys['game'][:4]
            
            # Simple XOR with 4-byte key
            result = bytearray()
            for i, b in enumerate(data):
                result.append(b ^ key[i % len(key)])
            
            return bytes(result)
            
        except Exception as e:
            print(f"XOR decryption error: {e}")
            return None
    
    def try_decrypt_resource(self, data: bytes, resource_type: str = None) -> Tuple[Optional[bytes], str]:
        """Try to decrypt a resource using various methods."""
        # Detect encryption
        enc_type, markers = self.detect_encryption(data)
        
        if enc_type == "unknown":
            return None, "unknown"
        
        # Get appropriate key based on resource type
        if resource_type and resource_type in self.static_keys:
            key = self.static_keys[resource_type]
        else:
            key = self.static_keys['game']
        
        # Find start of encrypted data
        start_pos = max(markers.values()) + 4
        encrypted_data = data[start_pos:]
        
        # Try decryption
        if enc_type == 'aes':
            if 'salt' in markers:
                # Use salt-based key derivation
                salt_pos = markers['salt']
                salt = data[salt_pos+4:salt_pos+12]
                key, iv = self.derive_key(salt, key)
            else:
                # Use static IV
                iv = MD5.new(key).digest()
            return self.decrypt_aes(encrypted_data, key, iv), 'aes'
            
        elif enc_type == 'blowfish':
            return self.decrypt_blowfish(encrypted_data, key), 'blowfish'
            
        elif enc_type == 'xor':
            return self.decrypt_xor(encrypted_data, key[:4]), 'xor'
        
        return None, "unknown"
    
    def process_file(self, file_path: str) -> bool:
        """Process a potentially encrypted Evony file."""
        try:
            print(f"\nProcessing: {file_path}")
            
            # Read file
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Try decryption with different resource types
            best_result = None
            best_method = "unknown"
            best_size = 0
            
            for res_type in self.static_keys:
                decrypted, method = self.try_decrypt_resource(data, res_type)
                if decrypted:
                    # Basic validation - prefer larger valid results
                    try:
                        # Try to decompress if it looks compressed
                        if decrypted.startswith(b'\x78\x9C'):
                            decompressed = zlib.decompress(decrypted)
                            if len(decompressed) > best_size:
                                best_result = decompressed
                                best_method = f"{method}+zlib"
                                best_size = len(decompressed)
                        else:
                            # Check if result looks valid
                            if all(32 <= b <= 126 for b in decrypted[:20]):
                                if len(decrypted) > best_size:
                                    best_result = decrypted
                                    best_method = method
                                    best_size = len(decrypted)
                    except:
                        # If validation fails, still keep result if it's our best
                        if not best_result and len(decrypted) > best_size:
                            best_result = decrypted
                            best_method = method
                            best_size = len(decrypted)
            
            if best_result:
                # Save decrypted data
                output_path = os.path.join(
                    self.output_dir,
                    f"decrypted_{os.path.basename(file_path)}"
                )
                
                with open(output_path, 'wb') as f:
                    f.write(best_result)
                
                print(f"Successfully decrypted using {best_method}")
                print(f"Decrypted data saved to: {output_path}")
                
                # Generate report
                report_path = os.path.join(
                    self.output_dir,
                    f"report_{os.path.basename(file_path)}.txt"
                )
                
                with open(report_path, 'w') as f:
                    f.write("Evony Decryption Report\n")
                    f.write("=====================\n\n")
                    
                    f.write("1. File Information:\n")
                    f.write("-----------------\n")
                    f.write(f"Original File: {file_path}\n")
                    f.write(f"Original Size: {len(data):,} bytes\n")
                    f.write(f"Decrypted Size: {len(best_result):,} bytes\n")
                    f.write(f"Decryption Method: {best_method}\n\n")
                    
                    f.write("2. Content Preview:\n")
                    f.write("----------------\n")
                    # Show preview of decrypted data
                    if all(32 <= b <= 126 for b in best_result[:100]):
                        # Text content
                        preview = best_result[:1000].decode('utf-8', 'ignore')
                        f.write(f"Content appears to be text:\n\n{preview}\n")
                    else:
                        # Binary content
                        f.write("Content appears to be binary data\n")
                        f.write(f"First 100 bytes: {best_result[:100].hex()}\n")
                
                return True
            
            print("Could not decrypt file")
            return False
            
        except Exception as e:
            print(f"Error processing file: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python evony_crypto.py <file>")
        sys.exit(1)
    
    decoder = EvonyDecoder()
    decoder.process_file(sys.argv[1])
