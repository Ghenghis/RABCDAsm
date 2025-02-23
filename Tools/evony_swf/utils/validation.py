"""Validation utilities for SWF processing."""
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ValidationResult:
    """Result of a validation operation."""
    success: bool
    message: str
    details: Optional[Dict] = None

def validate_swf_header(header) -> ValidationResult:
    """Validate SWF header structure."""
    if not header:
        return ValidationResult(False, "Missing header")
        
    if not hasattr(header, 'version'):
        return ValidationResult(False, "Missing version in header")
        
    if header.version < 9:  # Minimum required for AS3
        return ValidationResult(
            False,
            f"Unsupported SWF version: {header.version}. Minimum required: 9"
        )
        
    return ValidationResult(True, "Valid SWF header")

def validate_tag_structure(tag) -> ValidationResult:
    """Validate SWF tag structure."""
    if not tag:
        return ValidationResult(False, "Missing tag")
        
    required_attrs = ['code', 'length', 'data']
    missing = [attr for attr in required_attrs if not hasattr(tag, attr)]
    
    if missing:
        return ValidationResult(
            False,
            f"Missing required tag attributes: {', '.join(missing)}"
        )
        
    if tag.length != len(tag.data):
        return ValidationResult(
            False,
            f"Tag length mismatch. Expected: {tag.length}, Got: {len(tag.data)}"
        )
        
    return ValidationResult(True, "Valid tag structure")

def validate_asset_metadata(metadata: Dict) -> ValidationResult:
    """Validate asset metadata structure."""
    required_fields = ['tag_code', 'offset']
    missing = [field for field in required_fields if field not in metadata]
    
    if missing:
        return ValidationResult(
            False,
            f"Missing required metadata fields: {', '.join(missing)}"
        )
        
    return ValidationResult(True, "Valid metadata structure")

def validate_manifest(manifest: Dict) -> ValidationResult:
    """Validate manifest structure and content."""
    try:
        required_sections = ['assets', 'relationships', 'metadata']
        missing = [section for section in required_sections if section not in manifest]
        
        if missing:
            return ValidationResult(
                False,
                f"Missing required manifest sections: {', '.join(missing)}"
            )
            
        # Check assets
        if not isinstance(manifest['assets'], dict):
            return ValidationResult(False, "Assets must be a dictionary")
            
        for asset_id, asset in manifest['assets'].items():
            if not isinstance(asset, dict):
                return ValidationResult(
                    False,
                    f"Invalid asset format for {asset_id}"
                )
                
            asset_result = validate_asset_metadata(asset.get('metadata', {}))
            if not asset_result.success:
                return ValidationResult(
                    False,
                    f"Invalid asset metadata for {asset_id}: {asset_result.message}"
                )
                
        # Check relationships
        if not isinstance(manifest['relationships'], list):
            return ValidationResult(False, "Relationships must be a list")
            
        for rel in manifest['relationships']:
            if not all(k in rel for k in ['source', 'target', 'type']):
                return ValidationResult(
                    False,
                    "Invalid relationship format"
                )
                
        # Check metadata
        if not isinstance(manifest['metadata'], dict):
            return ValidationResult(False, "Metadata must be a dictionary")
            
        return ValidationResult(True, "Valid manifest structure")
        
    except Exception as e:
        return ValidationResult(False, f"Manifest validation error: {str(e)}")

def validate_extraction(output_dir: str) -> ValidationResult:
    """Validate the complete extraction output."""
    try:
        import os
        import json
        
        # Check required directories
        required_dirs = ['scripts', 'shapes', 'symbols', 'resources', 'analysis']
        missing_dirs = [
            d for d in required_dirs 
            if not os.path.isdir(os.path.join(output_dir, d))
        ]
        
        if missing_dirs:
            return ValidationResult(
                False,
                f"Missing required directories: {', '.join(missing_dirs)}"
            )
            
        # Check required files
        required_files = [
            'manifest.json',
            'relationships.json',
            'extraction_summary.txt'
        ]
        missing_files = [
            f for f in required_files
            if not os.path.isfile(os.path.join(output_dir, f))
        ]
        
        if missing_files:
            return ValidationResult(
                False,
                f"Missing required files: {', '.join(missing_files)}"
            )
            
        # Validate manifest
        manifest_path = os.path.join(output_dir, 'manifest.json')
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        manifest_result = validate_manifest(manifest)
        if not manifest_result.success:
            return manifest_result
            
        # Check asset files
        for asset_id, asset in manifest['assets'].items():
            asset_path = os.path.join(output_dir, asset['original_path'])
            if not os.path.isfile(asset_path):
                return ValidationResult(
                    False,
                    f"Missing asset file: {asset_path}"
                )
                
        return ValidationResult(True, "Valid extraction output")
        
    except Exception as e:
        return ValidationResult(False, f"Extraction validation error: {str(e)}")

def validate_rebuild_manifest(manifest: Dict) -> ValidationResult:
    """Validate rebuild manifest structure."""
    try:
        required_fields = ['version', 'main_class', 'assets', 'build_config']
        missing = [
            field for field in required_fields 
            if field not in manifest
        ]
        
        if missing:
            return ValidationResult(
                False,
                f"Missing required manifest fields: {', '.join(missing)}"
            )
            
        # Check version
        if not isinstance(manifest['version'], int):
            return ValidationResult(False, "Version must be an integer")
            
        # Check main class
        if not isinstance(manifest['main_class'], str):
            return ValidationResult(False, "Main class must be a string")
            
        # Check assets
        if not isinstance(manifest['assets'], list):
            return ValidationResult(False, "Assets must be a list")
            
        for asset in manifest['assets']:
            if not isinstance(asset, dict):
                return ValidationResult(False, "Invalid asset format")
                
            if 'path' not in asset or 'type' not in asset:
                return ValidationResult(
                    False,
                    "Assets must have path and type fields"
                )
                
        # Check build config
        config = manifest['build_config']
        if not isinstance(config, dict):
            return ValidationResult(False, "Build config must be a dictionary")
            
        required_config = ['sdk_version', 'target_player', 'use_network']
        missing_config = [
            field for field in required_config
            if field not in config
        ]
        
        if missing_config:
            return ValidationResult(
                False,
                f"Missing build config fields: {', '.join(missing_config)}"
            )
            
        return ValidationResult(True, "Valid rebuild manifest")
        
    except Exception as e:
        return ValidationResult(
            False,
            f"Rebuild manifest validation error: {str(e)}"
        )
