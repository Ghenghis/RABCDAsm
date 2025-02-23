"""
Module for tracking dependencies in ActionScript code.

This module analyzes ActionScript code to:
1. Track class dependencies and inheritance relationships
2. Map import statements and their usage
3. Identify external library dependencies
4. Generate dependency graphs for visualization
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
import json
import networkx as nx
from graphviz import Digraph

@dataclass
class ASClass:
    """Represents an ActionScript class with its dependencies"""
    name: str
    package: str
    imports: Set[str]
    superclass: Optional[str]
    interfaces: Set[str]
    used_classes: Set[str]
    file_path: Path

class DependencyTracker:
    def __init__(self):
        self.classes: Dict[str, ASClass] = {}
        self.package_map: Dict[str, Set[str]] = {}
        self.dependency_graph = nx.DiGraph()
        
    def analyze_file(self, file_path: Path) -> ASClass:
        """Analyze an ActionScript file for dependencies"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract package name
        package_match = re.search(r'package\s+([\w.]+)', content)
        package = package_match.group(1) if package_match else ''
        
        # Extract class name
        class_match = re.search(r'class\s+(\w+)', content)
        if not class_match:
            raise ValueError(f"No class found in {file_path}")
        class_name = class_match.group(1)
        
        # Extract imports
        imports = set(re.findall(r'import\s+([\w.]+)', content))
        
        # Extract superclass
        extends_match = re.search(r'extends\s+([\w.]+)', content)
        superclass = extends_match.group(1) if extends_match else None
        
        # Extract interfaces
        implements_match = re.search(r'implements\s+([\w.,\s]+)', content)
        interfaces = set()
        if implements_match:
            interfaces = {i.strip() for i in implements_match.group(1).split(',')}
            
        # Extract used classes (excluding built-in types)
        builtin_types = {'String', 'Number', 'Boolean', 'Array', 'Object', 'int', 'uint'}
        type_usages = set(re.findall(r':\s*([\w.]+)', content))
        var_declarations = set(re.findall(r'new\s+([\w.]+)', content))
        used_classes = {cls for cls in (type_usages | var_declarations) 
                       if cls not in builtin_types}
        
        # Create ASClass instance
        as_class = ASClass(
            name=class_name,
            package=package,
            imports=imports,
            superclass=superclass,
            interfaces=interfaces,
            used_classes=used_classes,
            file_path=file_path
        )
        
        # Update class registry
        full_name = f"{package}.{class_name}" if package else class_name
        self.classes[full_name] = as_class
        
        # Update package map
        if package:
            if package not in self.package_map:
                self.package_map[package] = set()
            self.package_map[package].add(class_name)
            
        # Update dependency graph
        self._update_graph(as_class)
        
        return as_class
    
    def analyze_directory(self, directory: Path):
        """Analyze all ActionScript files in a directory recursively"""
        for file_path in directory.rglob('*.as'):
            try:
                self.analyze_file(file_path)
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
    
    def _update_graph(self, as_class: ASClass):
        """Update the dependency graph with a class's dependencies"""
        class_id = f"{as_class.package}.{as_class.name}" if as_class.package else as_class.name
        
        # Add node for current class
        self.dependency_graph.add_node(class_id)
        
        # Add edges for superclass
        if as_class.superclass:
            self.dependency_graph.add_edge(class_id, as_class.superclass)
            
        # Add edges for interfaces
        for interface in as_class.interfaces:
            self.dependency_graph.add_edge(class_id, interface)
            
        # Add edges for used classes
        for used_class in as_class.used_classes:
            if used_class != class_id:  # Avoid self-references
                self.dependency_graph.add_edge(class_id, used_class)
    
    def get_dependencies(self, class_name: str) -> Dict[str, List[str]]:
        """Get all dependencies for a class"""
        if class_name not in self.classes:
            raise ValueError(f"Class {class_name} not found")
            
        as_class = self.classes[class_name]
        return {
            'imports': list(as_class.imports),
            'superclass': [as_class.superclass] if as_class.superclass else [],
            'interfaces': list(as_class.interfaces),
            'used_classes': list(as_class.used_classes)
        }
    
    def get_dependents(self, class_name: str) -> List[str]:
        """Get all classes that depend on the specified class"""
        return [
            name for name, cls in self.classes.items()
            if (class_name in cls.used_classes or
                class_name == cls.superclass or
                class_name in cls.interfaces)
        ]
    
    def export_graph(self, output_file: Path, format: str = 'png'):
        """Export the dependency graph to a file"""
        dot = Digraph(comment='ActionScript Dependencies')
        dot.attr(rankdir='LR')
        
        # Add nodes
        for node in self.dependency_graph.nodes():
            dot.node(node)
            
        # Add edges
        for edge in self.dependency_graph.edges():
            dot.edge(edge[0], edge[1])
            
        dot.render(str(output_file), format=format, cleanup=True)
    
    def export_json(self, output_file: Path):
        """Export dependency data to JSON"""
        data = {
            'classes': {
                name: {
                    'package': cls.package,
                    'imports': list(cls.imports),
                    'superclass': cls.superclass,
                    'interfaces': list(cls.interfaces),
                    'used_classes': list(cls.used_classes),
                    'file_path': str(cls.file_path)
                }
                for name, cls in self.classes.items()
            },
            'packages': {
                pkg: list(classes)
                for pkg, classes in self.package_map.items()
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the codebase"""
        return list(nx.simple_cycles(self.dependency_graph))
    
    def get_dependency_metrics(self) -> Dict[str, Dict[str, int]]:
        """Calculate dependency metrics for each class"""
        metrics = {}
        for class_name, as_class in self.classes.items():
            incoming = len(self.get_dependents(class_name))
            outgoing = (
                len(as_class.used_classes) +
                (1 if as_class.superclass else 0) +
                len(as_class.interfaces)
            )
            metrics[class_name] = {
                'incoming_dependencies': incoming,
                'outgoing_dependencies': outgoing,
                'total_dependencies': incoming + outgoing
            }
        return metrics

if __name__ == '__main__':
    # Example usage
    tracker = DependencyTracker()
    src_dir = Path('src')  # Replace with actual source directory
    
    # Analyze all ActionScript files
    tracker.analyze_directory(src_dir)
    
    # Export dependency graph
    tracker.export_graph(Path('dependencies.gv'))
    
    # Export detailed data as JSON
    tracker.export_json(Path('dependencies.json'))
    
    # Check for circular dependencies
    circles = tracker.find_circular_dependencies()
    if circles:
        print("Warning: Circular dependencies found:")
        for circle in circles:
            print(" -> ".join(circle))
