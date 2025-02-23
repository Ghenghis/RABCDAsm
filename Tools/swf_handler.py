import os
import struct
from PyQt6.QtCore import QObject, pyqtSignal
from evony_swf.utils.swf import read_swf_header, parse_swf_tag, decompress_swf

class SWFHandler(QObject):
    """Handles SWF file loading and analysis"""
    
    # Tag type constants
    TAG_DEFINE_BITS = 6
    TAG_DEFINE_BUTTON = 7
    TAG_JPEG_TABLES = 8
    TAG_DEFINE_BITS_JPEG2 = 21
    TAG_DEFINE_BITS_JPEG3 = 35
    TAG_DEFINE_BITS_LOSSLESS = 20
    TAG_DEFINE_BITS_LOSSLESS2 = 36
    TAG_DEFINE_SOUND = 14
    TAG_DEFINE_FONT = 10
    TAG_DEFINE_FONT2 = 48
    TAG_DEFINE_FONT3 = 75
    TAG_DEFINE_TEXT = 11
    TAG_DEFINE_TEXT2 = 33
    TAG_DEFINE_SPRITE = 39
    TAG_DO_ACTION = 12
    TAG_DO_ABC = 82
    TAG_FILE_ATTRIBUTES = 69
    TAG_FRAME_LABEL = 43
    TAG_PLACE_OBJECT = 4
    TAG_PLACE_OBJECT2 = 26
    TAG_PLACE_OBJECT3 = 70
    TAG_REMOVE_OBJECT = 5
    TAG_REMOVE_OBJECT2 = 28
    TAG_SHOW_FRAME = 1
    TAG_SET_BACKGROUND_COLOR = 9
    TAG_SYMBOL_CLASS = 76
    
    # Signals
    loading_progress = pyqtSignal(int)  # Progress percentage
    loading_status = pyqtSignal(str)    # Status message
    analysis_complete = pyqtSignal(dict) # Analysis results
    error_occurred = pyqtSignal(str)     # Error message
    
    def __init__(self):
        super().__init__()
        self.current_tags = []
        self.current_header = None
        self.raw_data = None
        
    def load_swf(self, file_path):
        """Load and analyze a SWF file"""
        try:
            self.loading_status.emit(f"Loading {os.path.basename(file_path)}...")
            self.loading_progress.emit(0)
            
            # Read SWF file
            with open(file_path, 'rb') as f:
                self.raw_data = f.read()
                
            # Parse header
            self.current_header = read_swf_header(self.raw_data)
            self.loading_progress.emit(20)
            
            # Decompress if needed
            data = self.raw_data
            if self.current_header['compression'] != 'none':
                data = decompress_swf(self.raw_data)
                if not data:
                    raise ValueError("Failed to decompress SWF file")
            self.loading_progress.emit(40)
            
            # Parse tags
            self.current_tags = []
            pos = self.current_header['header_size']
            while pos < len(data):
                try:
                    tag_code, tag_length, tag_data = parse_swf_tag(data[pos:])
                    tag_info = self.parse_tag_content(tag_code, tag_data)
                    tag_info.update({
                        'code': tag_code,
                        'length': tag_length,
                        'offset': pos
                    })
                    self.current_tags.append(tag_info)
                    pos += tag_length + (6 if tag_length >= 0x3F else 2)
                except ValueError as e:
                    self.loading_status.emit(f"Warning: {str(e)}")
                    break
                    
            self.loading_progress.emit(60)
            
            # Analyze resources
            resources = self.analyze_resources()
            self.loading_progress.emit(80)
            
            # Prepare results
            results = {
                'metadata': {
                    'version': self.current_header['version'],
                    'compression': self.current_header['compression'],
                    'filesize': len(self.raw_data),
                    'decompressed_size': len(data),
                    'tag_count': len(self.current_tags)
                },
                'resources': resources
            }
            
            self.loading_progress.emit(100)
            self.loading_status.emit("Analysis complete")
            self.analysis_complete.emit(results)
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Error loading SWF: {str(e)}")
            return False
            
    def parse_tag_content(self, tag_code, data):
        """Parse tag content based on tag type"""
        try:
            if tag_code == self.TAG_SET_BACKGROUND_COLOR:
                return {
                    'type': 'SetBackgroundColor',
                    'color': f"#{data[0]:02x}{data[1]:02x}{data[2]:02x}"
                }
                
            elif tag_code in {self.TAG_DEFINE_BITS_JPEG2, self.TAG_DEFINE_BITS_JPEG3}:
                char_id = struct.unpack('<H', data[0:2])[0]
                return {
                    'type': 'Image',
                    'subtype': 'JPEG',
                    'id': char_id,
                    'data': data[2:]
                }
                
            elif tag_code in {self.TAG_DEFINE_BITS_LOSSLESS, self.TAG_DEFINE_BITS_LOSSLESS2}:
                char_id = struct.unpack('<H', data[0:2])[0]
                format = data[2]
                width = struct.unpack('<H', data[3:5])[0]
                height = struct.unpack('<H', data[5:7])[0]
                return {
                    'type': 'Image',
                    'subtype': 'Lossless',
                    'id': char_id,
                    'format': format,
                    'width': width,
                    'height': height,
                    'data': data[7:]
                }
                
            elif tag_code == self.TAG_DEFINE_SOUND:
                char_id = struct.unpack('<H', data[0:2])[0]
                flags = data[2]
                sample_rate = (flags >> 2) & 0x03
                sample_size = (flags >> 1) & 0x01
                channels = flags & 0x01
                sample_count = struct.unpack('<L', data[3:7])[0]
                return {
                    'type': 'Sound',
                    'id': char_id,
                    'format': flags >> 4,
                    'sample_rate': [5512, 11025, 22050, 44100][sample_rate],
                    'sample_size': 8 if sample_size == 0 else 16,
                    'channels': 1 if channels == 0 else 2,
                    'sample_count': sample_count,
                    'data': data[7:]
                }
                
            elif tag_code in {self.TAG_DEFINE_FONT, self.TAG_DEFINE_FONT2, self.TAG_DEFINE_FONT3}:
                char_id = struct.unpack('<H', data[0:2])[0]
                return {
                    'type': 'Font',
                    'id': char_id,
                    'version': tag_code,
                    'data': data[2:]
                }
                
            elif tag_code == self.TAG_DO_ABC:
                # Skip flags and name
                pos = 4
                while pos < len(data) and data[pos] != 0:
                    pos += 1
                return {
                    'type': 'Script',
                    'subtype': 'ABC',
                    'data': data[pos+1:]
                }
                
            elif tag_code == self.TAG_DO_ACTION:
                return {
                    'type': 'Script',
                    'subtype': 'Action',
                    'data': data
                }
                
            else:
                return {
                    'type': 'Unknown',
                    'data': data
                }
                
        except Exception as e:
            return {
                'type': 'Error',
                'error': str(e),
                'data': data
            }
            
    def analyze_resources(self):
        """Analyze resources in the SWF file"""
        if not self.current_tags:
            return {
                'images': [],
                'sounds': [],
                'fonts': [],
                'scripts': [],
                'other': []
            }
            
        resources = {
            'images': [],
            'sounds': [],
            'fonts': [],
            'scripts': [],
            'other': []
        }
        
        for tag in self.current_tags:
            if tag['type'] == 'Image':
                resources['images'].append({
                    'id': tag['id'],
                    'type': tag.get('subtype', 'Unknown'),
                    'size': len(tag['data']),
                    'dimensions': f"{tag.get('width', '?')}x{tag.get('height', '?')}"
                })
            elif tag['type'] == 'Sound':
                resources['sounds'].append({
                    'id': tag['id'],
                    'format': tag['format'],
                    'rate': tag['sample_rate'],
                    'size': len(tag['data']),
                    'duration': f"{tag['sample_count'] / tag['sample_rate']:.2f}s"
                })
            elif tag['type'] == 'Font':
                resources['fonts'].append({
                    'id': tag['id'],
                    'version': tag['version'],
                    'size': len(tag['data'])
                })
            elif tag['type'] == 'Script':
                resources['scripts'].append({
                    'type': tag['subtype'],
                    'size': len(tag['data'])
                })
            elif tag['type'] not in {'Unknown', 'Error'}:
                resources['other'].append({
                    'type': tag['type'],
                    'size': len(tag['data'])
                })
                
        return resources
        
    def get_abc_content(self):
        """Get ABC content from current SWF"""
        if not self.current_tags:
            return None
            
        # Look for DoABC tags
        for tag in self.current_tags:
            if tag['type'] == 'Script' and tag['subtype'] == 'ABC':
                return tag['data']
        return None
        
    def get_resource_content(self, resource_id):
        """Get content of a specific resource"""
        if not self.current_tags:
            return None
            
        # Find tag by resource ID
        for tag in self.current_tags:
            if tag.get('id') == resource_id:
                return tag['data']
        return None
