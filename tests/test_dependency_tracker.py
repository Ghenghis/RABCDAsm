"""
Test suite for the dependency tracker
"""

import pytest
from pathlib import Path
import tempfile
import os
import networkx as nx

from Tools.dependency_tracker import DependencyTracker, ASClass

@pytest.fixture
def sample_as_file():
    content = """
package com.example.game

import com.example.core.Entity
import com.example.utils.Logger
import com.example.ai.Behavior

class Player extends Entity implements IMovable, ICollidable {
    private var logger:Logger;
    private var behavior:Behavior;
    private var inventory:Inventory;
    private var position:Vector3D;
    
    public function Player() {
        logger = new Logger();
        behavior = new Behavior();
        inventory = new Inventory();
    }
}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.as', delete=False) as f:
        f.write(content)
    yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def tracker():
    return DependencyTracker()

def test_analyze_file(tracker, sample_as_file):
    as_class = tracker.analyze_file(sample_as_file)
    
    assert as_class.name == 'Player'
    assert as_class.package == 'com.example.game'
    assert as_class.superclass == 'Entity'
    assert as_class.interfaces == {'IMovable', 'ICollidable'}
    assert 'com.example.core.Entity' in as_class.imports
    assert 'com.example.utils.Logger' in as_class.imports
    assert 'com.example.ai.Behavior' in as_class.imports
    assert {'Logger', 'Behavior', 'Inventory', 'Vector3D'} == as_class.used_classes

def test_get_dependencies(tracker, sample_as_file):
    tracker.analyze_file(sample_as_file)
    deps = tracker.get_dependencies('com.example.game.Player')
    
    assert 'com.example.core.Entity' in deps['imports']
    assert 'Entity' in deps['superclass']
    assert {'IMovable', 'ICollidable'} == set(deps['interfaces'])
    assert {'Logger', 'Behavior', 'Inventory', 'Vector3D'} == set(deps['used_classes'])

def test_circular_dependencies(tracker):
    # Create temporary files for circular dependency test
    files = []
    try:
        # Class A depends on B
        content_a = """
        package test
        import test.B
        class A {
            private var b:B;
        }
        """
        # Class B depends on A
        content_b = """
        package test
        import test.A
        class B {
            private var a:A;
        }
        """
        
        # Create temporary files
        for content in [content_a, content_b]:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.as', delete=False) as f:
                f.write(content)
                files.append(Path(f.name))
        
        # Analyze files
        for file in files:
            tracker.analyze_file(file)
        
        circles = tracker.find_circular_dependencies()
        assert len(circles) == 1
        assert {'test.A', 'test.B'} == set(circles[0])
        
    finally:
        # Cleanup
        for file in files:
            os.unlink(file)

def test_dependency_metrics(tracker, sample_as_file):
    tracker.analyze_file(sample_as_file)
    metrics = tracker.get_dependency_metrics()
    player_metrics = metrics['com.example.game.Player']
    
    assert player_metrics['incoming_dependencies'] == 0  # No classes depend on Player
    assert player_metrics['outgoing_dependencies'] == 6  # Superclass + 2 interfaces + 3 used classes
    assert player_metrics['total_dependencies'] == 6

def test_export_graph(tracker, sample_as_file, tmp_path):
    tracker.analyze_file(sample_as_file)
    output_file = tmp_path / 'test_graph'
    tracker.export_graph(output_file)
    
    assert (output_file.with_suffix('.gv.png')).exists()

def test_export_json(tracker, sample_as_file, tmp_path):
    tracker.analyze_file(sample_as_file)
    output_file = tmp_path / 'dependencies.json'
    tracker.export_json(output_file)
    
    assert output_file.exists()
    assert output_file.stat().st_size > 0
