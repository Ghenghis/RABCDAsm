"""Asset relationship tracker for managing dependencies and references."""
import json
import logging
from typing import Dict, List, Optional, Set

class AssetRelationship:
    """Represents a relationship between assets."""
    def __init__(self, source: str, target: str, rel_type: str):
        self.source = source
        self.target = target
        self.rel_type = rel_type

    def to_dict(self) -> Dict:
        """Convert relationship to dictionary."""
        return {
            'source': self.source,
            'target': self.target,
            'type': self.rel_type
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'AssetRelationship':
        """Create relationship from dictionary."""
        return cls(data['source'], data['target'], data['type'])

class RelationshipTracker:
    """Tracks relationships between assets."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._relationships: List[AssetRelationship] = []
        self._forward_deps: Dict[str, Set[str]] = {}  # Asset -> Dependencies
        self._reverse_deps: Dict[str, Set[str]] = {}  # Asset -> Dependents
        self._asset_groups: Dict[str, Set[str]] = {}  # Group -> Assets

    def add_relationship(self, source: str, target: str, rel_type: str) -> None:
        """Add a relationship between assets."""
        relationship = AssetRelationship(source, target, rel_type)
        self._relationships.append(relationship)
        
        # Update dependency maps
        if rel_type == 'depends_on':
            self._add_dependency(source, target)
        elif rel_type == 'references':
            self._add_reference(source, target)
        elif rel_type == 'includes':
            self._add_inclusion(source, target)

    def _add_dependency(self, source: str, target: str) -> None:
        """Add a dependency relationship."""
        if source not in self._forward_deps:
            self._forward_deps[source] = set()
        self._forward_deps[source].add(target)
        
        if target not in self._reverse_deps:
            self._reverse_deps[target] = set()
        self._reverse_deps[target].add(source)

    def _add_reference(self, source: str, target: str) -> None:
        """Add a reference relationship."""
        if source not in self._forward_deps:
            self._forward_deps[source] = set()
        self._forward_deps[source].add(target)

    def _add_inclusion(self, container: str, member: str) -> None:
        """Add an inclusion relationship."""
        if container not in self._asset_groups:
            self._asset_groups[container] = set()
        self._asset_groups[container].add(member)

    def get_dependencies(self, asset_id: str) -> Set[str]:
        """Get all dependencies of an asset."""
        return self._forward_deps.get(asset_id, set())

    def get_dependents(self, asset_id: str) -> Set[str]:
        """Get all assets that depend on this asset."""
        return self._reverse_deps.get(asset_id, set())

    def get_group_members(self, group_id: str) -> Set[str]:
        """Get all members of an asset group."""
        return self._asset_groups.get(group_id, set())

    def get_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the relationship graph."""
        visited = set()
        path = []
        cycles = []

        def dfs(node: str) -> None:
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return
                
            if node in visited:
                return
                
            visited.add(node)
            path.append(node)
            
            for dep in self._forward_deps.get(node, set()):
                dfs(dep)
                
            path.pop()

        for node in self._forward_deps:
            if node not in visited:
                dfs(node)

        return cycles

    def save_to_file(self, filepath: str) -> None:
        """Save relationships to a JSON file."""
        try:
            data = {
                'relationships': [r.to_dict() for r in self._relationships],
                'groups': {k: list(v) for k, v in self._asset_groups.items()}
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.info(f"Saved {len(self._relationships)} relationships to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving relationships: {str(e)}")

    def load_from_file(self, filepath: str) -> None:
        """Load relationships from a JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Clear existing data
            self._relationships.clear()
            self._forward_deps.clear()
            self._reverse_deps.clear()
            self._asset_groups.clear()
            
            # Load relationships
            for rel_data in data['relationships']:
                rel = AssetRelationship.from_dict(rel_data)
                self._relationships.append(rel)
                if rel.rel_type == 'depends_on':
                    self._add_dependency(rel.source, rel.target)
                elif rel.rel_type == 'references':
                    self._add_reference(rel.source, rel.target)
                elif rel.rel_type == 'includes':
                    self._add_inclusion(rel.source, rel.target)
            
            # Load groups
            for group_id, members in data['groups'].items():
                self._asset_groups[group_id] = set(members)
                
            self.logger.info(f"Loaded {len(self._relationships)} relationships from {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error loading relationships: {str(e)}")

    def verify_integrity(self) -> bool:
        """Verify the integrity of relationship data."""
        try:
            # Check for dangling references
            all_assets = set()
            for rel in self._relationships:
                all_assets.add(rel.source)
                all_assets.add(rel.target)
            
            for deps in self._forward_deps.values():
                if not deps.issubset(all_assets):
                    return False
            
            for deps in self._reverse_deps.values():
                if not deps.issubset(all_assets):
                    return False
            
            # Check for consistency between forward and reverse deps
            for source, targets in self._forward_deps.items():
                for target in targets:
                    if source not in self._reverse_deps.get(target, set()):
                        return False
            
            return True
            
        except Exception:
            return False
