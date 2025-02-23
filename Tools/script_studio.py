"""
AI-Powered Script Studio for RABCDAsm
Provides an intelligent interface for script management, testing, and execution
"""

import os
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                            QPushButton, QTextEdit, QListWidget, QLabel, 
                            QComboBox, QProgressBar, QSplitter, QTreeWidget,
                            QTreeWidgetItem, QCheckBox, QSpinBox, QFileDialog,
                            QGroupBox, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QColor, QPalette, QIcon, QFont
from .script_engine import ScriptEngine, ScriptResult
from .ai_features import AIFeatureManager, AIAnalysisResult

class ScriptStudioTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.script_engine = ScriptEngine(os.path.join('tools', 'rabcdasm'))
        self.ai_manager = AIFeatureManager()
        self.init_ui()
        self.setup_connections()
        self.setup_ai_features()
        
    def init_ui(self):
        """Initialize the Script Studio UI"""
        layout = QVBoxLayout()
        
        # Create main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Script Organization
        left_panel = self.create_left_panel()
        
        # Middle panel - Script Configuration
        middle_panel = self.create_middle_panel()
        
        # Right panel - Script Execution
        right_panel = self.create_right_panel()
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([300, 400, 500])
        
        # Add splitter to main layout
        layout.addWidget(splitter)
        self.setLayout(layout)
        
        # Set dark theme
        self.setStyleSheet("""
            QWidget {
                background-color: #1B2838;
                color: #FFFFFF;
            }
            QGroupBox {
                border: 1px solid #4A90E2;
                margin-top: 0.5em;
                padding-top: 0.5em;
            }
            QGroupBox::title {
                color: #FFFFFF;
            }
        """)
        
    def create_left_panel(self):
        """Create the left panel with script organization"""
        left_panel = QWidget()
        layout = QVBoxLayout(left_panel)
        
        # Script Categories Tree
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabel("Script Categories")
        self.category_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1D2B3A;
                border: none;
            }
            QTreeWidget::item:selected {
                background-color: #FF6B00;
                color: #000000;
            }
        """)
        
        # Add categories
        categories = {
            "SWF Analysis": [
                "Analyze SWF Structure",
                "Extract Resources",
                "Analyze Tags",
                "Check Compression",
                "Validate Format"
            ],
            "ABC Manipulation": [
                "Extract ABC",
                "Disassemble ABC",
                "Modify Assembly",
                "Reassemble ABC",
                "Replace in SWF"
            ],
            "Crypto Analysis": [
                "Detect Encryption",
                "Extract Keys",
                "Analyze Patterns",
                "String Analysis",
                "Decrypt Content"
            ],
            "Integration Tests": [
                "Run All Tests",
                "Test SWF Analysis",
                "Test ABC Manipulation",
                "Test Crypto",
                "Generate Report"
            ],
            "Advanced Analysis": [
                "AI Pattern Recognition",
                "Code Flow Analysis",
                "Security Audit",
                "Performance Analysis",
                "Batch Processing"
            ]
        }
        
        for category, scripts in categories.items():
            cat_item = QTreeWidgetItem([category])
            for script in scripts:
                script_item = QTreeWidgetItem([script])
                cat_item.addChild(script_item)
            self.category_tree.addTopLevelItem(cat_item)
            
        # Expand all categories
        self.category_tree.expandAll()
        
        # Add to layout
        layout.addWidget(self.category_tree)
        
        return left_panel
        
    def create_middle_panel(self):
        """Create the middle panel with script configuration"""
        middle_panel = QWidget()
        layout = QVBoxLayout(middle_panel)
        
        # Script Info
        info_group = QGroupBox("Script Information")
        info_layout = QVBoxLayout(info_group)
        
        self.script_name_label = QLabel("Select a script")
        self.script_name_label.setStyleSheet("font-weight: bold; color: #FF6B00;")
        
        self.script_desc = QTextEdit()
        self.script_desc.setReadOnly(True)
        self.script_desc.setStyleSheet("""
            QTextEdit {
                background-color: #1D2B3A;
                border: none;
            }
        """)
        
        info_layout.addWidget(self.script_name_label)
        info_layout.addWidget(self.script_desc)
        
        # Script Parameters
        params_group = QGroupBox("Parameters")
        params_layout = QVBoxLayout(params_group)
        
        # File Selection
        file_layout = QHBoxLayout()
        self.file_path = QLabel("No file selected")
        select_file_btn = QPushButton("Select SWF")
        select_file_btn.clicked.connect(self.select_file)
        select_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6B00;
                color: #000000;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #FF8533;
            }
        """)
        
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(select_file_btn)
        
        # Options
        self.options_layout = QVBoxLayout()
        self.update_options()
        
        params_layout.addLayout(file_layout)
        params_layout.addLayout(self.options_layout)
        
        # Add groups to layout
        layout.addWidget(info_group)
        layout.addWidget(params_group)
        layout.addStretch()
        
        return middle_panel
        
    def create_right_panel(self):
        """Create the right panel with execution controls"""
        right_panel = QWidget()
        layout = QVBoxLayout(right_panel)
        
        # AI Control
        ai_group = QGroupBox("AI Control")
        ai_layout = QVBoxLayout(ai_group)
        
        # AI Mode Selection
        mode_layout = QHBoxLayout()
        self.ai_toggle = QPushButton("AI Mode: Semi-Auto")
        self.ai_toggle.setStyleSheet("""
            QPushButton {
                background-color: #FF6B00;
                color: #000000;
                border: none;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #FF8533;
            }
        """)
        
        self.auto_checkbox = QCheckBox("Auto-Run")
        self.auto_checkbox.setStyleSheet("color: #FFFFFF;")
        
        mode_layout.addWidget(self.ai_toggle)
        mode_layout.addWidget(self.auto_checkbox)
        
        # AI Feature Controls
        ai_features_group = QGroupBox("AI Features")
        ai_features_layout = QVBoxLayout(ai_features_group)
        
        # Intelligent Analysis
        self.intelligent_analysis_btn = QPushButton("Run Intelligent Analysis")
        self.intelligent_analysis_btn.setStyleSheet(self.ai_toggle.styleSheet())
        self.intelligent_analysis_btn.clicked.connect(self.run_intelligent_analysis)
        
        # Auto-Optimization
        self.auto_optimize_btn = QPushButton("Auto-Optimize Code")
        self.auto_optimize_btn.setStyleSheet(self.ai_toggle.styleSheet())
        self.auto_optimize_btn.clicked.connect(self.run_auto_optimization)
        
        # Predictive Analysis
        self.predict_issues_btn = QPushButton("Predict Issues")
        self.predict_issues_btn.setStyleSheet(self.ai_toggle.styleSheet())
        self.predict_issues_btn.clicked.connect(self.run_predictive_analysis)
        
        # Smart Debug
        self.smart_debug_btn = QPushButton("Smart Debug")
        self.smart_debug_btn.setStyleSheet(self.ai_toggle.styleSheet())
        self.smart_debug_btn.clicked.connect(self.run_smart_debug)
        
        # Add AI feature buttons
        ai_features_layout.addWidget(self.intelligent_analysis_btn)
        ai_features_layout.addWidget(self.auto_optimize_btn)
        ai_features_layout.addWidget(self.predict_issues_btn)
        ai_features_layout.addWidget(self.smart_debug_btn)
        
        ai_layout.addLayout(mode_layout)
        ai_layout.addWidget(ai_features_group)
        
        # Execution Controls
        exec_group = QGroupBox("Execution")
        exec_layout = QVBoxLayout(exec_group)
        
        self.run_button = QPushButton("Run Script")
        self.run_button.setStyleSheet(self.ai_toggle.styleSheet())
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #2A3F5A;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #FF6B00;
            }
        """)
        
        exec_layout.addWidget(self.run_button)
        exec_layout.addWidget(self.progress_bar)
        
        # Output Console
        console_group = QGroupBox("Output")
        console_layout = QVBoxLayout(console_group)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1D2B3A;
                border: none;
                font-family: Consolas, monospace;
            }
        """)
        
        console_layout.addWidget(self.output_text)
        
        # Add all groups to layout
        layout.addWidget(ai_group)
        layout.addWidget(exec_group)
        layout.addWidget(console_group)
        
        return right_panel
        
    def setup_connections(self):
        """Set up signal connections"""
        self.category_tree.itemSelectionChanged.connect(self.script_selected)
        self.ai_toggle.clicked.connect(self.toggle_ai_mode)
        self.run_button.clicked.connect(self.run_script)
        
        # Connect script engine signals
        self.script_engine.progress_update.connect(self.update_progress)
        self.script_engine.script_complete.connect(self.script_completed)
        self.script_engine.log_message.connect(self.log_message)
        
    def setup_ai_features(self):
        """Set up AI feature connections and handlers"""
        # Connect AI manager signals
        self.ai_manager.analysis_complete.connect(self.handle_analysis_complete)
        self.ai_manager.insight_available.connect(self.handle_insight)
        self.ai_manager.recommendation_ready.connect(self.handle_recommendation)
        self.ai_manager.automation_status.connect(self.handle_automation_status)
        
    def script_selected(self):
        """Handle script selection"""
        items = self.category_tree.selectedItems()
        if not items:
            return
            
        item = items[0]
        if item.parent():  # It's a script, not a category
            script_name = item.text(0)
            self.script_name_label.setText(script_name)
            self.update_script_info(script_name)
            self.update_options()
            
    def update_script_info(self, script_name: str):
        """Update script information"""
        descriptions = {
            "Analyze SWF Structure": "Perform detailed analysis of SWF file structure including tags, frames, and resources.",
            "Extract Resources": "Extract embedded resources such as images, sounds, and binary data from SWF file.",
            "AI Pattern Recognition": "Use AI to identify patterns in code, resources, and behavior.",
            # Add more descriptions
        }
        
        self.script_desc.setText(descriptions.get(script_name, "No description available."))
        
    def update_options(self):
        """Update parameter options based on selected script"""
        # Clear existing options
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Add script-specific options
        items = self.category_tree.selectedItems()
        if not items:
            return
            
        item = items[0]
        if not item.parent():  # It's a category
            return
            
        script_name = item.text(0)
        
        if "Analysis" in script_name:
            self.add_analysis_options()
        elif "Extract" in script_name:
            self.add_extraction_options()
        elif "Crypto" in script_name:
            self.add_crypto_options()
            
    def add_analysis_options(self):
        """Add analysis-specific options"""
        depth_label = QLabel("Analysis Depth:")
        depth_combo = QComboBox()
        depth_combo.addItems(["Basic", "Standard", "Deep"])
        depth_combo.setStyleSheet("""
            QComboBox {
                background-color: #1D2B3A;
                color: #FFFFFF;
                border: none;
                padding: 5px;
            }
        """)
        
        self.options_layout.addWidget(depth_label)
        self.options_layout.addWidget(depth_combo)
        
    def add_extraction_options(self):
        """Add extraction-specific options"""
        format_label = QLabel("Output Format:")
        format_combo = QComboBox()
        format_combo.addItems(["Raw", "Organized", "Compressed"])
        format_combo.setStyleSheet("""
            QComboBox {
                background-color: #1D2B3A;
                color: #FFFFFF;
                border: none;
                padding: 5px;
            }
        """)
        
        self.options_layout.addWidget(format_label)
        self.options_layout.addWidget(format_combo)
        
    def add_crypto_options(self):
        """Add cryptography-specific options"""
        method_label = QLabel("Detection Method:")
        method_combo = QComboBox()
        method_combo.addItems(["Pattern Matching", "Entropy Analysis", "Combined"])
        method_combo.setStyleSheet("""
            QComboBox {
                background-color: #1D2B3A;
                color: #FFFFFF;
                border: none;
                padding: 5px;
            }
        """)
        
        self.options_layout.addWidget(method_label)
        self.options_layout.addWidget(method_combo)
        
    def select_file(self):
        """Open file dialog to select SWF file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select SWF File", "", "SWF Files (*.swf)"
        )
        if file_path:
            self.file_path.setText(file_path)
            
    def toggle_ai_mode(self):
        """Toggle between Semi-Auto and Full AI modes"""
        current_text = self.ai_toggle.text()
        if "Semi-Auto" in current_text:
            self.ai_toggle.setText("AI Mode: Full Control")
            self.log_message("Switched to Full AI Control Mode")
        else:
            self.ai_toggle.setText("AI Mode: Semi-Auto")
            self.log_message("Switched to Semi-Automated Mode")
            
    def run_script(self):
        """Execute the selected script"""
        items = self.category_tree.selectedItems()
        if not items or not items[0].parent():
            return
            
        script_name = items[0].text(0)
        swf_path = self.file_path.text()
        
        if swf_path == "No file selected":
            self.log_message("Error: Please select a SWF file first")
            return
            
        # Prepare parameters
        params = {
            'swf_path': swf_path,
            'analysis_depth': self.depth_spin.value(),
            'auto_run': self.auto_checkbox.isChecked()
        }
        
        # Execute script
        self.run_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.script_engine.execute_script(script_name, params)
        
    def update_progress(self, value: int, message: str):
        """Update progress bar and log message"""
        self.progress_bar.setValue(value)
        self.log_message(message)
        
    def script_completed(self, result: ScriptResult):
        """Handle script completion"""
        self.run_button.setEnabled(True)
        
        if result.success:
            self.log_message("\nScript completed successfully!")
            self.log_message("Results:")
            for key, value in result.data.items():
                self.log_message(f"{key}: {value}")
        else:
            self.log_message("\nScript failed with errors:")
            for error in result.errors:
                self.log_message(f"Error: {error}")
                
    def log_message(self, message: str):
        """Add message to output console"""
        self.output_text.append(message)
        
    async def run_intelligent_analysis(self):
        """Run intelligent code analysis"""
        self.log_message("Running intelligent analysis...")
        self.progress_bar.setValue(0)
        
        try:
            # Get current file content
            file_path = self.file_path.text()
            if file_path == "No file selected":
                self.log_message("Error: Please select a file first")
                return
                
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Run analysis
            result = await self.ai_manager.analyze_code_patterns(content)
            self.handle_analysis_complete(result)
            
        except Exception as e:
            self.log_message(f"Error during analysis: {str(e)}")
            
    async def run_auto_optimization(self):
        """Run automatic code optimization"""
        self.log_message("Running auto-optimization...")
        self.progress_bar.setValue(0)
        
        try:
            file_path = self.file_path.text()
            if file_path == "No file selected":
                self.log_message("Error: Please select a file first")
                return
                
            optimizations = await self.ai_manager.suggest_optimizations(file_path)
            self.handle_optimizations(optimizations)
            
        except Exception as e:
            self.log_message(f"Error during optimization: {str(e)}")
            
    async def run_predictive_analysis(self):
        """Run predictive analysis for potential issues"""
        self.log_message("Running predictive analysis...")
        self.progress_bar.setValue(0)
        
        try:
            file_path = self.file_path.text()
            if file_path == "No file selected":
                self.log_message("Error: Please select a file first")
                return
                
            # Get file changes
            changes = [{'file': file_path, 'type': 'modification'}]
            predictions = await self.ai_manager.predict_issues(changes)
            self.handle_predictions(predictions)
            
        except Exception as e:
            self.log_message(f"Error during prediction: {str(e)}")
            
    async def run_smart_debug(self):
        """Run smart debugging"""
        self.log_message("Running smart debug...")
        self.progress_bar.setValue(0)
        
        try:
            file_path = self.file_path.text()
            if file_path == "No file selected":
                self.log_message("Error: Please select a file first")
                return
                
            # Get error info
            error_info = {'file': file_path, 'type': 'runtime_error'}
            suggestions = await self.ai_manager.debug_suggestion(error_info)
            self.handle_debug_suggestions(suggestions)
            
        except Exception as e:
            self.log_message(f"Error during debugging: {str(e)}")
            
    def handle_analysis_complete(self, result: AIAnalysisResult):
        """Handle completed analysis results"""
        self.log_message("\nAnalysis Results:")
        self.log_message(f"Category: {result.category}")
        self.log_message(f"Confidence: {result.confidence:.2%}")
        
        self.log_message("\nFindings:")
        for finding in result.findings:
            self.log_message(f"- {finding}")
            
        self.log_message("\nRecommendations:")
        for rec in result.recommendations:
            self.log_message(f"- {rec}")
            
        self.progress_bar.setValue(100)
        
    def handle_optimizations(self, optimizations: List[Dict]):
        """Handle optimization suggestions"""
        self.log_message("\nOptimization Suggestions:")
        for opt in optimizations:
            self.log_message(f"\nType: {opt['type']}")
            self.log_message(f"Target: {opt['target']}")
            self.log_message(f"Suggestion: {opt['suggestion']}")
            self.log_message(f"Confidence: {opt['confidence']:.2%}")
            
        self.progress_bar.setValue(100)
        
    def handle_predictions(self, predictions: List[Dict]):
        """Handle issue predictions"""
        self.log_message("\nPredicted Issues:")
        for pred in predictions:
            self.log_message(f"\nSeverity: {pred['severity']}")
            self.log_message(f"Category: {pred['category']}")
            self.log_message(f"Description: {pred['description']}")
            self.log_message(f"Confidence: {pred['confidence']:.2%}")
            
        self.progress_bar.setValue(100)
        
    def handle_debug_suggestions(self, suggestions: List[str]):
        """Handle debugging suggestions"""
        self.log_message("\nDebugging Suggestions:")
        for suggestion in suggestions:
            self.log_message(f"- {suggestion}")
            
        self.progress_bar.setValue(100)
        
    def handle_insight(self, category: str, data: dict):
        """Handle real-time AI insights"""
        self.log_message(f"\nNew Insight ({category}):")
        for key, value in data.items():
            self.log_message(f"{key}: {value}")
            
    def handle_recommendation(self, category: str, recommendations: list):
        """Handle AI recommendations"""
        self.log_message(f"\nRecommendations for {category}:")
        for rec in recommendations:
            self.log_message(f"- {rec}")
            
    def handle_automation_status(self, task: str, success: bool):
        """Handle automation task status updates"""
        status = "completed successfully" if success else "failed"
        self.log_message(f"\nAutomation task '{task}' {status}")
