from typing import Dict, List, Optional
from pathlib import Path
import subprocess
import json
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QComboBox, QLabel, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal

class AnalysisSuite(QWidget):
    """Integrated analysis tools manager for RABCDAsm"""
    
    analysis_complete = pyqtSignal(dict)  # Emits results when analysis is done
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tools_config = {
            "static": {
                "ghidra": {"path": None, "enabled": False},
                "ida_pro": {"path": None, "enabled": False},
                "binary_ninja": {"path": None, "enabled": False}
            },
            "dynamic": {
                "x64dbg": {"path": None, "enabled": False},
                "process_monitor": {"path": None, "enabled": False},
                "api_monitor": {"path": None, "enabled": False}
            },
            "network": {
                "wireshark": {"path": None, "enabled": False},
                "burp_suite": {"path": None, "enabled": False}
            },
            "supplementary": {
                "pe_explorer": {"path": None, "enabled": False},
                "resource_hacker": {"path": None, "enabled": False},
                "die": {"path": None, "enabled": False},
                "hxd": {"path": None, "enabled": False}
            }
        }
        
        self.init_ui()
        self.load_config()
        self.apply_styles()
        
    def init_ui(self):
        """Initialize the analysis suite UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header = QLabel("Analysis Tools Suite")
        header.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #000000;
                padding: 8px 0;
            }
        """)
        layout.addWidget(header)
        
        # Tool category selector
        category_layout = QHBoxLayout()
        category_layout.setSpacing(8)
        
        category_label = QLabel("Analysis Category:")
        category_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #000000;
            }
        """)
        self.category_combo = QComboBox()
        self.category_combo.addItems([cat.replace('_', ' ').title() for cat in self.tools_config.keys()])
        self.category_combo.currentTextChanged.connect(self.update_tools_list)
        self.category_combo.setMinimumWidth(200)
        
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        category_layout.addStretch()
        layout.addLayout(category_layout)
        
        # Tools list container
        tools_container = QWidget()
        tools_container.setStyleSheet(f"""
            QWidget {{
                background-color: #FFFFFF;
                border: 1px solid #D0D9E4;
                border-radius: 8px;
            }}
        """)
        tools_container_layout = QVBoxLayout(tools_container)
        tools_container_layout.setContentsMargins(12, 12, 12, 12)
        
        self.tools_list = QWidget()
        self.tools_layout = QVBoxLayout(self.tools_list)
        self.tools_layout.setSpacing(8)
        tools_container_layout.addWidget(self.tools_list)
        
        layout.addWidget(tools_container)
        
        # Analysis output
        output_label = QLabel("Analysis Output")
        output_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #000000;
                padding-top: 8px;
            }
        """)
        layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(150)
        layout.addWidget(self.output_text)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        analyze_btn = QPushButton("Run Analysis")
        analyze_btn.clicked.connect(self.run_analysis)
        analyze_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        clear_btn = QPushButton("Clear Output")
        clear_btn.clicked.connect(self.output_text.clear)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addWidget(analyze_btn)
        layout.addLayout(buttons_layout)
        
        self.update_tools_list(self.category_combo.currentText())
        
    def apply_styles(self):
        """Apply custom styles to widgets"""
        self.setStyleSheet("""
            QWidget {
                background-color: #F0F4F8;
            }
            QPushButton {
                background-color: #FF6B00;
                color: #000000;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #FF8533;
            }
            QPushButton[secondary="true"] {
                background-color: #6BA4E7;
            }
            QPushButton[secondary="true"]:hover {
                background-color: #89B8ED;
            }
            QComboBox {
                background-color: #FFFFFF;
                border: 1px solid #D0D9E4;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
            }
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #D0D9E4;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
    def update_tools_list(self, category: str):
        """Update the tools list for the selected category"""
        # Clear existing tools
        while self.tools_layout.count():
            child = self.tools_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Add tools for selected category
        for tool_name, tool_info in self.tools_config[category].items():
            tool_widget = QWidget()
            tool_layout = QHBoxLayout(tool_widget)
            
            # Tool name and status
            tool_layout.addWidget(QLabel(tool_name.replace('_', ' ').title()))
            status_label = QLabel("✓" if tool_info["enabled"] else "✗")
            tool_layout.addWidget(status_label)
            
            # Configure button
            config_btn = QPushButton("Configure")
            config_btn.clicked.connect(lambda checked, t=tool_name: self.configure_tool(t))
            config_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4A90E2;
                    color: #000000;
                    border: none;
                    padding: 3px 10px;
                    border-radius: 2px;
                }
                QPushButton:hover {
                    background-color: #FF6B00;
                }
            """)
            tool_layout.addWidget(config_btn)
            
            self.tools_layout.addWidget(tool_widget)
            
    def configure_tool(self, tool_name: str):
        """Configure a specific analysis tool"""
        # TODO: Implement tool configuration dialog
        pass
        
    def run_analysis(self):
        """Execute analysis using enabled tools"""
        # TODO: Implement analysis execution
        pass
        
    def load_config(self):
        """Load tools configuration from file"""
        config_path = Path(__file__).parent / "config" / "analysis_tools.json"
        if config_path.exists():
            with open(config_path) as f:
                saved_config = json.load(f)
                # Update existing config with saved values
                for category in self.tools_config:
                    if category in saved_config:
                        for tool in self.tools_config[category]:
                            if tool in saved_config[category]:
                                self.tools_config[category][tool].update(
                                    saved_config[category][tool]
                                )
                                
    def save_config(self):
        """Save tools configuration to file"""
        config_path = Path(__file__).parent / "config"
        config_path.mkdir(exist_ok=True)
        
        with open(config_path / "analysis_tools.json", 'w') as f:
            json.dump(self.tools_config, f, indent=4)
