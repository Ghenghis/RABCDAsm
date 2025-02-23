"""
Code Structure Analyzer for RABCDAsm
Provides intelligent code analysis and pattern detection
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Set, Optional
import re
import ast
import logging

@dataclass
class CodePattern:
    """Represents a detected code pattern"""
    name: str
    category: str
    severity: str
    location: Dict[str, int]  # line, column
    description: str
    recommendation: str

@dataclass
class Dependencies:
    """Represents code dependencies"""
    imports: Set[str]
    external_refs: Set[str]
    internal_refs: Set[str]

@dataclass
class Complexity:
    """Code complexity metrics"""
    cyclomatic_complexity: int
    cognitive_complexity: int
    maintainability_index: float
    halstead_metrics: Dict[str, float]

@dataclass
class SecurityVulnerability:
    """Security vulnerability information"""
    type: str
    severity: str
    location: Dict[str, int]
    description: str
    recommendation: str

@dataclass
class SecurityAnalysis:
    """Security analysis results"""
    vulnerabilities: List[SecurityVulnerability]
    risk_level: str
    best_practices: List[str]

@dataclass
class PerformanceBottleneck:
    """Performance bottleneck information"""
    type: str
    severity: str
    location: Dict[str, int]
    impact: str
    recommendation: str

@dataclass
class PerformanceAnalysis:
    """Performance analysis results"""
    bottlenecks: List[PerformanceBottleneck]
    recommendations: List[str]
    metrics: Dict[str, float]

@dataclass
class AnalysisResult:
    """Complete code analysis results"""
    class_count: int
    method_count: int
    property_count: int
    patterns: List[CodePattern]
    dependencies: Dependencies
    complexity: Complexity
    security: SecurityAnalysis
    performance: PerformanceAnalysis

class CodeStructureAnalyzer:
    """Analyzes ActionScript code structure and patterns"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        self.pattern_cache = {}
        self.ast_cache = {}
        self.metrics = {
            'analyzed_files': 0,
            'patterns_found': 0,
            'security_issues': 0
        }

    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def analyze_structure(self, file_path: Path) -> AnalysisResult:
        """Analyze code structure of an ActionScript file"""
        self.logger.info(f"Analyzing structure of {file_path}")
        
        try:
            # Cache check
            if str(file_path) in self.ast_cache:
                self.logger.debug("Using cached AST")
                ast_tree = self.ast_cache[str(file_path)]
            else:
                ast_tree = self._parse_file(file_path)
                self.ast_cache[str(file_path)] = ast_tree

            # Core structure analysis
            structure = {
                'classes': self._analyze_classes(ast_tree),
                'interfaces': self._analyze_interfaces(ast_tree),
                'namespaces': self._analyze_namespaces(ast_tree),
                'imports': self._analyze_imports(ast_tree)
            }

            # Advanced metrics
            complexity = self._calculate_complexity(ast_tree)
            dependencies = self._analyze_dependencies(ast_tree)
            security = self._analyze_security_patterns(ast_tree)
            performance = self._analyze_performance_patterns(ast_tree)

            self.metrics['analyzed_files'] += 1
            
            return AnalysisResult(
                class_count=len(structure['classes']),
                method_count=sum(len(c['methods']) for c in structure['classes']),
                property_count=sum(len(c['properties']) for c in structure['classes']),
                patterns=self._detect_code_patterns(ast_tree),
                dependencies=dependencies,
                complexity=complexity,
                security=security,
                performance=performance
            )

        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {str(e)}")
            raise

    def _analyze_classes(self, ast_tree) -> List[Dict]:
        """Analyze class structures"""
        classes = []
        for node in ast_tree.class_nodes:
            class_info = {
                'name': node.name,
                'methods': self._analyze_methods(node),
                'properties': self._analyze_properties(node),
                'metrics': {
                    'inheritance_depth': self._calculate_inheritance_depth(node),
                    'coupling': self._calculate_coupling(node),
                    'cohesion': self._calculate_cohesion(node)
                }
            }
            classes.append(class_info)
        return classes

    def _analyze_security_patterns(self, ast_tree) -> SecurityAnalysis:
        """Analyze security patterns and vulnerabilities"""
        vulnerabilities = []
        
        # Common ActionScript security patterns
        patterns = {
            'unsafe_dynamic': r'dynamic\s+class',
            'eval_usage': r'eval\s*\(',
            'unsafe_native': r'flash\.system\.Security\.allowDomain',
            'plain_text_credentials': r'(username|password|secret)\s*=\s*["\'][^"\']+["\']'
        }

        for pattern_name, pattern in patterns.items():
            matches = self._find_pattern_matches(ast_tree, pattern)
            if matches:
                self.metrics['security_issues'] += len(matches)
                for match in matches:
                    vulnerabilities.append(
                        SecurityVulnerability(
                            type=pattern_name,
                            severity='HIGH' if pattern_name in ['eval_usage', 'unsafe_native'] else 'MEDIUM',
                            location=match['location'],
                            description=f"Found {pattern_name} pattern",
                            recommendation=self._get_security_recommendation(pattern_name)
                        )
                    )

        return SecurityAnalysis(
            vulnerabilities=vulnerabilities,
            risk_level=self._calculate_risk_level(vulnerabilities),
            best_practices=self._generate_security_recommendations(vulnerabilities)
        )

    def _analyze_performance_patterns(self, ast_tree) -> PerformanceAnalysis:
        """Analyze code for performance patterns"""
        issues = []
        
        patterns = {
            'tight_loop': r'while\s*\(\s*true\s*\)',
            'large_array': r'new\s+Array\s*\(\s*\d{5,}\s*\)',
            'nested_loops': r'for\s*\([^)]+\)\s*\{[^}]*for\s*\([^)]+\)',
            'expensive_calls': r'\.indexOf\s*\(\s*[^)]+\)\s*\)'
        }

        for pattern_name, pattern in patterns.items():
            matches = self._find_pattern_matches(ast_tree, pattern)
            for match in matches:
                issues.append(
                    PerformanceBottleneck(
                        type=pattern_name,
                        severity='HIGH' if pattern_name in ['tight_loop', 'nested_loops'] else 'MEDIUM',
                        location=match['location'],
                        impact=self._calculate_performance_impact(pattern_name),
                        recommendation=self._get_performance_recommendation(pattern_name)
                    )
                )

        return PerformanceAnalysis(
            bottlenecks=issues,
            recommendations=self._generate_optimization_suggestions(issues),
            metrics=self._calculate_performance_metrics(ast_tree)
        )

    def _parse_file(self, file_path: Path) -> ast.AST:
        """Parse ActionScript file into an AST"""
        with open(file_path, 'r') as file:
            content = file.read()
        return ast.parse(content)

    def _analyze_interfaces(self, ast_tree) -> List[Dict]:
        """Analyze interface structures"""
        interfaces = []
        for node in ast_tree.interface_nodes:
            interface_info = {
                'name': node.name,
                'methods': self._analyze_methods(node),
                'properties': self._analyze_properties(node),
                'metrics': {
                    'inheritance_depth': self._calculate_inheritance_depth(node),
                    'coupling': self._calculate_coupling(node),
                    'cohesion': self._calculate_cohesion(node)
                }
            }
            interfaces.append(interface_info)
        return interfaces

    def _analyze_namespaces(self, ast_tree) -> List[Dict]:
        """Analyze namespace structures"""
        namespaces = []
        for node in ast_tree.namespace_nodes:
            namespace_info = {
                'name': node.name,
                'classes': self._analyze_classes(node),
                'interfaces': self._analyze_interfaces(node),
                'metrics': {
                    'inheritance_depth': self._calculate_inheritance_depth(node),
                    'coupling': self._calculate_coupling(node),
                    'cohesion': self._calculate_cohesion(node)
                }
            }
            namespaces.append(namespace_info)
        return namespaces

    def _analyze_imports(self, ast_tree) -> List[Dict]:
        """Analyze import statements"""
        imports = []
        for node in ast_tree.import_nodes:
            import_info = {
                'name': node.name,
                'alias': node.alias,
                'metrics': {
                    'inheritance_depth': self._calculate_inheritance_depth(node),
                    'coupling': self._calculate_coupling(node),
                    'cohesion': self._calculate_cohesion(node)
                }
            }
            imports.append(import_info)
        return imports

    def _analyze_methods(self, node) -> List[Dict]:
        """Analyze method structures"""
        methods = []
        for method_node in node.method_nodes:
            method_info = {
                'name': method_node.name,
                'parameters': self._analyze_parameters(method_node),
                'metrics': {
                    'cyclomatic_complexity': self._calculate_cyclomatic_complexity(method_node),
                    'cognitive_complexity': self._calculate_cognitive_complexity(method_node),
                    'maintainability_index': self._calculate_maintainability_index(method_node)
                }
            }
            methods.append(method_info)
        return methods

    def _analyze_properties(self, node) -> List[Dict]:
        """Analyze property structures"""
        properties = []
        for property_node in node.property_nodes:
            property_info = {
                'name': property_node.name,
                'type': property_node.type,
                'metrics': {
                    'inheritance_depth': self._calculate_inheritance_depth(property_node),
                    'coupling': self._calculate_coupling(property_node),
                    'cohesion': self._calculate_cohesion(property_node)
                }
            }
            properties.append(property_info)
        return properties

    def _analyze_parameters(self, method_node) -> List[Dict]:
        """Analyze method parameters"""
        parameters = []
        for parameter_node in method_node.parameter_nodes:
            parameter_info = {
                'name': parameter_node.name,
                'type': parameter_node.type,
                'metrics': {
                    'inheritance_depth': self._calculate_inheritance_depth(parameter_node),
                    'coupling': self._calculate_coupling(parameter_node),
                    'cohesion': self._calculate_cohesion(parameter_node)
                }
            }
            parameters.append(parameter_info)
        return parameters

    def _calculate_complexity(self, ast_tree) -> Complexity:
        """Calculate code complexity metrics"""
        cyclomatic_complexity = 0
        cognitive_complexity = 0
        maintainability_index = 0
        halstead_metrics = {
            'operators': 0,
            'operands': 0,
            'volume': 0
        }

        for node in ast_tree.nodes:
            cyclomatic_complexity += self._calculate_cyclomatic_complexity(node)
            cognitive_complexity += self._calculate_cognitive_complexity(node)
            maintainability_index += self._calculate_maintainability_index(node)
            halstead_metrics['operators'] += self._calculate_halstead_operators(node)
            halstead_metrics['operands'] += self._calculate_halstead_operands(node)
            halstead_metrics['volume'] += self._calculate_halstead_volume(node)

        return Complexity(
            cyclomatic_complexity=cyclomatic_complexity,
            cognitive_complexity=cognitive_complexity,
            maintainability_index=maintainability_index,
            halstead_metrics=halstead_metrics
        )

    def _calculate_inheritance_depth(self, node) -> int:
        """Calculate inheritance depth"""
        depth = 0
        for parent in node.parents:
            depth += 1
            depth += self._calculate_inheritance_depth(parent)
        return depth

    def _calculate_coupling(self, node) -> int:
        """Calculate coupling"""
        coupling = 0
        for child in node.children:
            coupling += 1
            coupling += self._calculate_coupling(child)
        return coupling

    def _calculate_cohesion(self, node) -> int:
        """Calculate cohesion"""
        cohesion = 0
        for method in node.methods:
            cohesion += 1
            cohesion += self._calculate_cohesion(method)
        return cohesion

    def _calculate_cyclomatic_complexity(self, node) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 0
        for child in node.children:
            complexity += 1
            complexity += self._calculate_cyclomatic_complexity(child)
        return complexity

    def _calculate_cognitive_complexity(self, node) -> int:
        """Calculate cognitive complexity"""
        complexity = 0
        for child in node.children:
            complexity += 1
            complexity += self._calculate_cognitive_complexity(child)
        return complexity

    def _calculate_maintainability_index(self, node) -> float:
        """Calculate maintainability index"""
        index = 0
        for child in node.children:
            index += 1
            index += self._calculate_maintainability_index(child)
        return index

    def _calculate_halstead_operators(self, node) -> int:
        """Calculate Halstead operators"""
        operators = 0
        for child in node.children:
            operators += 1
            operators += self._calculate_halstead_operators(child)
        return operators

    def _calculate_halstead_operands(self, node) -> int:
        """Calculate Halstead operands"""
        operands = 0
        for child in node.children:
            operands += 1
            operands += self._calculate_halstead_operands(child)
        return operands

    def _calculate_halstead_volume(self, node) -> int:
        """Calculate Halstead volume"""
        volume = 0
        for child in node.children:
            volume += 1
            volume += self._calculate_halstead_volume(child)
        return volume

    def _detect_code_patterns(self, ast_tree) -> List[CodePattern]:
        """Detect code patterns"""
        patterns = []
        for node in ast_tree.nodes:
            for pattern in self.pattern_cache:
                if re.search(pattern, node.code):
                    patterns.append(CodePattern(
                        name=self.pattern_cache[pattern],
                        category='code_pattern',
                        severity='LOW',
                        location={'line': node.line, 'column': node.column},
                        description=f"Found {self.pattern_cache[pattern]} pattern",
                        recommendation=f"Consider refactoring {self.pattern_cache[pattern]} pattern"
                    ))
        return patterns

    def _find_pattern_matches(self, ast_tree, pattern) -> List[Dict]:
        """Find pattern matches"""
        matches = []
        for node in ast_tree.nodes:
            if re.search(pattern, node.code):
                matches.append({
                    'location': {'line': node.line, 'column': node.column},
                    'code': node.code
                })
        return matches

    def _get_security_recommendation(self, pattern_name) -> str:
        """Get security recommendation"""
        recommendations = {
            'unsafe_dynamic': 'Avoid using dynamic classes',
            'eval_usage': 'Avoid using eval()',
            'unsafe_native': 'Avoid using native code',
            'plain_text_credentials': 'Avoid storing credentials in plain text'
        }
        return recommendations.get(pattern_name, 'Unknown recommendation')

    def _calculate_risk_level(self, vulnerabilities) -> str:
        """Calculate risk level"""
        risk_level = 'LOW'
        for vulnerability in vulnerabilities:
            if vulnerability.severity == 'HIGH':
                risk_level = 'HIGH'
                break
        return risk_level

    def _generate_security_recommendations(self, vulnerabilities) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        for vulnerability in vulnerabilities:
            recommendations.append(self._get_security_recommendation(vulnerability.type))
        return recommendations

    def _calculate_performance_impact(self, pattern_name) -> str:
        """Calculate performance impact"""
        impacts = {
            'tight_loop': 'High performance impact',
            'large_array': 'Medium performance impact',
            'nested_loops': 'High performance impact',
            'expensive_calls': 'Medium performance impact'
        }
        return impacts.get(pattern_name, 'Unknown impact')

    def _get_performance_recommendation(self, pattern_name) -> str:
        """Get performance recommendation"""
        recommendations = {
            'tight_loop': 'Optimize loop structure',
            'large_array': 'Optimize array usage',
            'nested_loops': 'Optimize loop structure',
            'expensive_calls': 'Optimize function calls'
        }
        return recommendations.get(pattern_name, 'Unknown recommendation')

    def _generate_optimization_suggestions(self, issues) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = []
        for issue in issues:
            suggestions.append(self._get_performance_recommendation(issue.type))
        return suggestions

    def _calculate_performance_metrics(self, ast_tree) -> Dict[str, float]:
        """Calculate performance metrics"""
        metrics = {
            'loop_count': 0,
            'array_count': 0,
            'function_count': 0
        }
        for node in ast_tree.nodes:
            metrics['loop_count'] += self._calculate_loop_count(node)
            metrics['array_count'] += self._calculate_array_count(node)
            metrics['function_count'] += self._calculate_function_count(node)
        return metrics

    def _calculate_loop_count(self, node) -> int:
        """Calculate loop count"""
        count = 0
        for child in node.children:
            count += 1
            count += self._calculate_loop_count(child)
        return count

    def _calculate_array_count(self, node) -> int:
        """Calculate array count"""
        count = 0
        for child in node.children:
            count += 1
            count += self._calculate_array_count(child)
        return count

    def _calculate_function_count(self, node) -> int:
        """Calculate function count"""
        count = 0
        for child in node.children:
            count += 1
            count += self._calculate_function_count(child)
        return count
