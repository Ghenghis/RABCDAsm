"""
Test suite for the code structure analyzer component
"""

import pytest
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rabcdasm.tools import (
    CodeStructureAnalyzer,
    CodePattern,
    AnalysisResult,
    SecurityAnalysis,
    PerformanceAnalysis,
    Dependencies,
    Complexity
)

@pytest.fixture
def analyzer():
    """Create a CodeStructureAnalyzer instance"""
    return CodeStructureAnalyzer()

@pytest.fixture
def test_files_dir():
    """Create and return test files directory"""
    test_dir = Path(__file__).parent / "test_files"
    test_dir.mkdir(exist_ok=True)
    return test_dir

def write_test_file(test_files_dir: Path, filename: str, content: str) -> Path:
    """Write content to a test file"""
    file_path = test_files_dir / filename
    file_path.write_text(content)
    return file_path

def test_basic_structure_analysis(analyzer, test_files_dir):
    """Test basic code structure analysis"""
    file_path = write_test_file(test_files_dir, "simple_class.as", """
    package {
        public class SimpleClass {
            private var count:int = 0;
            
            public function increment():void {
                count++;
            }
            
            public function getCount():int {
                return count;
            }
        }
    }
    """)
    
    result = analyzer.analyze_structure(file_path)
    
    assert isinstance(result, AnalysisResult)
    assert result.class_count == 1
    assert result.method_count == 2
    assert result.property_count == 1

def test_pattern_detection(analyzer, test_files_dir):
    """Test pattern detection in code"""
    file_path = write_test_file(test_files_dir, "crypto_handler.as", """
    package {
        import flash.utils.ByteArray;
        import flash.crypto.generateRandomBytes;
        
        public class CryptoHandler {
            private var key:ByteArray;
            private var data:ByteArray;
            
            public function CryptoHandler() {
                key = generateRandomBytes(32);
                data = new ByteArray();
            }
            
            public function encrypt(input:String):ByteArray {
                // Potential security issue: using weak encryption
                var result:ByteArray = new ByteArray();
                for (var i:int = 0; i < input.length; i++) {
                    result[i] = input.charCodeAt(i) ^ key[i % key.length];
                }
                return result;
            }
            
            public function decrypt(input:ByteArray):String {
                var result:String = "";
                for (var i:int = 0; i < input.length; i++) {
                    result += String.fromCharCode(input[i] ^ key[i % key.length]);
                }
                return result;
            }
        }
    }
    """)
    
    patterns = analyzer.detect_patterns(file_path)
    
    # Check for crypto patterns
    crypto_patterns = [p for p in patterns if p.category == "crypto"]
    assert any(p.name == "weak_encryption" for p in crypto_patterns)
    
    # Check for security patterns
    security_patterns = [p for p in patterns if p.category == "security"]
    assert any(p.severity == "high" for p in security_patterns)

def test_dependency_analysis(analyzer, test_files_dir):
    """Test dependency analysis"""
    file_path = write_test_file(test_files_dir, "crypto_handler.as", """
    package {
        import flash.utils.ByteArray;
        import flash.crypto.generateRandomBytes;
        
        public class CryptoHandler {
            private var key:ByteArray;
            private var data:ByteArray;
            
            public function CryptoHandler() {
                key = generateRandomBytes(32);
                data = new ByteArray();
            }
            
            public function encrypt(input:String):ByteArray {
                // Potential security issue: using weak encryption
                var result:ByteArray = new ByteArray();
                for (var i:int = 0; i < input.length; i++) {
                    result[i] = input.charCodeAt(i) ^ key[i % key.length];
                }
                return result;
            }
            
            public function decrypt(input:ByteArray):String {
                var result:String = "";
                for (var i:int = 0; i < input.length; i++) {
                    result += String.fromCharCode(input[i] ^ key[i % key.length]);
                }
                return result;
            }
        }
    }
    """)
    
    deps = analyzer.analyze_dependencies(file_path)
    
    assert "flash.utils.ByteArray" in deps.imports
    assert "flash.crypto.generateRandomBytes" in deps.imports

def test_complexity_analysis(analyzer, test_files_dir):
    """Test code complexity analysis"""
    file_path = write_test_file(test_files_dir, "crypto_handler.as", """
    package {
        import flash.utils.ByteArray;
        import flash.crypto.generateRandomBytes;
        
        public class CryptoHandler {
            private var key:ByteArray;
            private var data:ByteArray;
            
            public function CryptoHandler() {
                key = generateRandomBytes(32);
                data = new ByteArray();
            }
            
            public function encrypt(input:String):ByteArray {
                // Potential security issue: using weak encryption
                var result:ByteArray = new ByteArray();
                for (var i:int = 0; i < input.length; i++) {
                    result[i] = input.charCodeAt(i) ^ key[i % key.length];
                }
                return result;
            }
            
            public function decrypt(input:ByteArray):String {
                var result:String = "";
                for (var i:int = 0; i < input.length; i++) {
                    result += String.fromCharCode(input[i] ^ key[i % key.length]);
                }
                return result;
            }
        }
    }
    """)
    
    complexity = analyzer.analyze_complexity(file_path)
    
    assert complexity.cyclomatic_complexity > 1
    assert complexity.cognitive_complexity > 0

def test_security_analysis(analyzer, test_files_dir):
    """Test security pattern detection"""
    # Create test file with security issues
    code_with_security_issues = """
    package {
        dynamic class UnsafeClass {
            private var username:String = "admin";
            private var password:String = "secret123";
            
            public function executeCode(code:String):void {
                eval(code);  // Unsafe eval usage
            }
            
            public function allowAllDomains():void {
                flash.system.Security.allowDomain("*");  // Unsafe domain policy
            }
        }
    }
    """
    file_path = write_test_file(test_files_dir, "security_test.as", code_with_security_issues)
    
    # Analyze security patterns
    result = analyzer.analyze_structure(file_path)
    
    # Verify security analysis results
    assert result.security is not None
    assert len(result.security.vulnerabilities) >= 4
    assert result.security.risk_level == "HIGH"
    
    # Verify specific vulnerabilities
    vuln_types = [v.type for v in result.security.vulnerabilities]
    assert "unsafe_dynamic" in vuln_types
    assert "eval_usage" in vuln_types
    assert "unsafe_native" in vuln_types
    assert "plain_text_credentials" in vuln_types

def test_performance_analysis(analyzer, test_files_dir):
    """Test performance pattern detection"""
    # Create test file with performance issues
    code_with_performance_issues = """
    package {
        public class SlowClass {
            private var largeArray:Array = new Array(100000);
            
            public function findItem(item:String):int {
                while(true) {  // Tight loop
                    for(var i:int = 0; i < largeArray.length; i++) {
                        for(var j:int = 0; j < largeArray.length; j++) {  // Nested loops
                            if(largeArray[i].indexOf(item) >= 0) {  // Expensive call
                                return i;
                            }
                        }
                    }
                }
                return -1;
            }
        }
    }
    """
    file_path = write_test_file(test_files_dir, "performance_test.as", code_with_performance_issues)
    
    # Analyze performance patterns
    result = analyzer.analyze_structure(file_path)
    
    # Verify performance analysis results
    assert result.performance is not None
    assert len(result.performance.issues) >= 4
    
    # Verify specific performance issues
    issue_types = [i.type for i in result.performance.issues]
    assert "tight_loop" in issue_types
    assert "large_array" in issue_types
    assert "nested_loops" in issue_types
    assert "expensive_calls" in issue_types
    
    # Verify optimization suggestions
    assert len(result.performance.optimization_suggestions) > 0

def test_error_handling(analyzer, test_files_dir):
    """Test error handling for invalid files"""
    # Test with non-existent file
    with pytest.raises(FileNotFoundError):
        analyzer.analyze_structure(test_files_dir / "nonexistent.as")
        
    # Test with invalid content
    write_test_file(test_files_dir, "invalid.as", "invalid { content")
    with pytest.raises(ValueError):
        analyzer.analyze_structure(test_files_dir / "invalid.as")

def test_security_analysis_2(analyzer, test_files_dir):
    """Test security vulnerability detection"""
    code_with_security_issues = """
    package {
        import flash.utils.ByteArray;
        import flash.crypto.generateRandomBytes;
        
        public class InsecureHandler {
            private var key:String = "hardcoded_key";  // Security issue: hardcoded credentials
            
            public function processData(input:String):void {
                eval(input);  // Security issue: eval usage
                
                var obj:* = new (getDefinitionByName(input))();  // Security issue: unsafe dynamic instantiation
            }
        }
    }
    """
    
    file_path = write_test_file(test_files_dir, "security_test.as", code_with_security_issues)
    
    # Analyze security patterns
    result = analyzer.analyze_structure(file_path)
    
    # Verify security analysis results
    assert result.security is not None
    assert any(v.severity == "high" for v in result.security.vulnerabilities)
    assert any(v.type == "hardcoded_credentials" for v in result.security.vulnerabilities)
    assert any(v.type == "eval_usage" for v in result.security.vulnerabilities)
    assert any(v.type == "unsafe_dynamic_class" for v in result.security.vulnerabilities)

def test_performance_analysis_2(analyzer, test_files_dir):
    """Test performance issue detection"""
    code_with_performance_issues = """
    package {
        import flash.utils.ByteArray;
        
        public class SlowHandler {
            private var data:Array = [];
            
            public function processLargeData():void {
                // Performance issue: large array allocation
                var largeArray:Array = new Array(1000000);
                
                // Performance issue: nested loops
                for (var i:int = 0; i < 1000; i++) {
                    for (var j:int = 0; j < 1000; j++) {
                        for (var k:int = 0; k < 100; k++) {
                            data.push(i * j * k);
                        }
                    }
                }
            }
        }
    }
    """
    
    file_path = write_test_file(test_files_dir, "performance_test.as", code_with_performance_issues)
    
    # Analyze performance patterns
    result = analyzer.analyze_structure(file_path)
    
    # Verify performance analysis results
    assert result.performance is not None
    assert any(i.type == "large_allocation" for i in result.performance.issues)
    assert any(i.type == "nested_loops" for i in result.performance.issues)
    assert any(i.severity == "high" for i in result.performance.issues)
