import struct
import zlib
import os
from typing import List, Dict, Any, Tuple

class ABCExtractor:
    def __init__(self, filename: str):
        self.filename = filename
        self.output_dir = "extracted_abc"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def read_ui32(self, data: bytes, offset: int) -> Tuple[int, int]:
        """Read a variable-length encoded 32-bit unsigned integer."""
        result = 0
        shift = 0
        while True:
            byte = data[offset]
            offset += 1
            result |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                break
            shift += 7
        return result, offset
    
    def read_string(self, data: bytes, offset: int) -> Tuple[str, int]:
        """Read a string from the constant pool."""
        length, offset = self.read_ui32(data, offset)
        if length == 0:
            return "", offset
        string = data[offset:offset+length].decode('utf-8', errors='replace')
        return string, offset + length
    
    def extract_constant_pool(self, data: bytes, offset: int) -> Tuple[Dict[str, List[Any]], int]:
        """Extract the constant pool from ABC data."""
        pool = {
            'integers': [],
            'uintegers': [],
            'doubles': [],
            'strings': [],
            'namespaces': [],
            'namespace_sets': [],
            'multinames': []
        }
        
        # Read integer pool
        count, offset = self.read_ui32(data, offset)
        if count > 0:
            for _ in range(count - 1):
                value, offset = self.read_ui32(data, offset)
                pool['integers'].append(value)
        
        # Read unsigned integer pool
        count, offset = self.read_ui32(data, offset)
        if count > 0:
            for _ in range(count - 1):
                value, offset = self.read_ui32(data, offset)
                pool['uintegers'].append(value)
        
        # Read double pool
        count, offset = self.read_ui32(data, offset)
        if count > 0:
            for _ in range(count - 1):
                value = struct.unpack('d', data[offset:offset+8])[0]
                pool['doubles'].append(value)
                offset += 8
        
        # Read string pool
        count, offset = self.read_ui32(data, offset)
        if count > 0:
            for _ in range(count - 1):
                string, offset = self.read_string(data, offset)
                pool['strings'].append(string)
        
        return pool, offset
    
    def extract_abc(self, data: bytes) -> Dict[str, Any]:
        """Extract and analyze ABC bytecode."""
        try:
            offset = 0
            
            # Read ABC version
            minor = struct.unpack("<H", data[offset:offset+2])[0]
            major = struct.unpack("<H", data[offset+2:offset+4])[0]
            offset += 4
            
            # Extract constant pool
            constant_pool, offset = self.extract_constant_pool(data, offset)
            
            # Analyze strings for interesting content
            interesting_strings = []
            for string in constant_pool['strings']:
                if any(keyword in string.lower() for keyword in [
                    'encrypt', 'decrypt', 'password', 'key', 'http', 
                    'socket', 'connect', 'load', 'send', 'receive'
                ]):
                    interesting_strings.append(string)
            
            return {
                'version': {
                    'major': major,
                    'minor': minor
                },
                'constant_pool': {
                    'integer_count': len(constant_pool['integers']),
                    'uinteger_count': len(constant_pool['uintegers']),
                    'double_count': len(constant_pool['doubles']),
                    'string_count': len(constant_pool['strings'])
                },
                'interesting_strings': interesting_strings
            }
            
        except Exception as e:
            print(f"Error extracting ABC: {e}")
            return {}
    
    def process_file(self):
        """Process the SWF file and extract ABC code."""
        try:
            with open(self.filename, "rb") as f:
                data = f.read()
            
            # Check if compressed
            signature = data[:3].decode('ascii')
            if signature == "CWS":
                print("Decompressing SWF...")
                decompressed = zlib.decompress(data[8:])
                data = data[:8] + decompressed
            
            # Find DoABC tags
            offset = 8  # Skip header
            abc_blocks = []
            
            while offset < len(data) - 2:
                tag_code_and_length = struct.unpack("<H", data[offset:offset+2])[0]
                tag_code = tag_code_and_length >> 6
                tag_length = tag_code_and_length & 0x3F
                
                # Long tag
                if tag_length == 0x3F:
                    tag_length = struct.unpack("<I", data[offset+2:offset+6])[0]
                    offset += 6
                else:
                    offset += 2
                
                # DoABC tag
                if tag_code == 82:
                    print(f"Found DoABC tag at offset {offset}, length {tag_length}")
                    abc_data = data[offset:offset+tag_length]
                    
                    # Skip flags and name
                    abc_offset = 4
                    while abc_data[abc_offset] != 0:
                        abc_offset += 1
                    abc_offset += 1
                    
                    # Extract ABC
                    abc_content = self.extract_abc(abc_data[abc_offset:])
                    abc_blocks.append(abc_content)
                    
                    # Save raw ABC
                    output_file = os.path.join(self.output_dir, f"abc_block_{len(abc_blocks)}.abc")
                    with open(output_file, "wb") as f:
                        f.write(abc_data[abc_offset:])
                    print(f"Saved ABC block to {output_file}")
                
                offset += tag_length
            
            return abc_blocks
            
        except Exception as e:
            print(f"Error processing file: {e}")
            return []

if __name__ == "__main__":
    extractor = ABCExtractor("extracted_swfs/embedded_0_43575309.swf")
    abc_blocks = extractor.process_file()
    
    if abc_blocks:
        print("\nABC Analysis Results:")
        for i, block in enumerate(abc_blocks, 1):
            print(f"\nABC Block {i}:")
            print("Version:", block['version'])
            print("Constant Pool Stats:", block['constant_pool'])
            if block['interesting_strings']:
                print("\nInteresting Strings:")
                for string in block['interesting_strings']:
                    print(f"  - {string}")
    else:
        print("\nNo ABC blocks were successfully extracted.")
