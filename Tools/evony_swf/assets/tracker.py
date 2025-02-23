"""Asset tracking and management module"""

import os
import json
import base64
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

@dataclass
class Asset:
    """Represents an asset extracted from the SWF file."""
    original_path: str
    asset_type: str
    data: bytes
    metadata: Dict[str, Any]
    symbol_name: Optional[str] = None
    class_name: Optional[str] = None
    encryption_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert asset to JSON-serializable dictionary."""
        result = {
            'original_path': self.original_path,
            'asset_type': self.asset_type,
            'data': base64.b64encode(self.data).decode('ascii'),
            'metadata': self.metadata
        }
        
        if self.symbol_name:
            result['symbol_name'] = self.symbol_name
        if self.class_name:
            result['class_name'] = self.class_name
        if self.encryption_type:
            result['encryption_type'] = self.encryption_type
            
        return result
        
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Asset':
        """Create asset from dictionary."""
        binary_data = base64.b64decode(data['data'])
        return Asset(
            original_path=data['original_path'],
            asset_type=data['asset_type'],
            data=binary_data,
            metadata=data['metadata'],
            symbol_name=data.get('symbol_name'),
            class_name=data.get('class_name'),
            encryption_type=data.get('encryption_type')
        )

class AssetTracker:
    """Tracks all assets during extraction and generates manifest."""
    
    def __init__(self):
        self.assets: Dict[str, Asset] = {}
        self.symbol_map: Dict[str, str] = {}
        self.class_map: Dict[str, str] = {}
        self.transformations: Dict[str, List[str]] = defaultdict(list)
        
    def add_asset(self, asset: Asset) -> None:
        """Add an asset to tracking."""
        path = asset.original_path
        self.assets[path] = asset
        
        if asset.symbol_name:
            self.symbol_map[asset.symbol_name] = path
            
        if asset.class_name:
            self.class_map[asset.class_name] = path
            
    def track_transformation(self, asset_path: str, operation: str) -> None:
        """Track a transformation applied to an asset."""
        self.transformations[asset_path].append(operation)
        
    def save_manifest(self, output_path: str) -> None:
        """Save asset tracking information to manifest file."""
        manifest = {
            'assets': {
                path: asset.to_dict() for path, asset in self.assets.items()
            },
            'symbol_map': self.symbol_map,
            'class_map': self.class_map,
            'transformations': dict(self.transformations)
        }
        
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
    def load_manifest(self, manifest_path: str) -> None:
        """Load asset tracking information from manifest file."""
        with open(manifest_path) as f:
            manifest = json.load(f)
            
        self.assets = {
            path: Asset.from_dict(data) for path, data in manifest['assets'].items()
        }
        self.symbol_map = manifest['symbol_map']
        self.class_map = manifest['class_map']
        self.transformations = defaultdict(list, manifest['transformations'])
