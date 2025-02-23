from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QTreeWidget, QTreeWidgetItem, QSplitter,
                            QPlainTextEdit, QFileDialog, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from tool_page import ToolPage
from enhanced_chat import CodeEditor
from swf_handler import SWFHandler

class DecompilerPage(ToolPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_title("Flash Decompiler")
        self.swf_handler = SWFHandler()
        self.setup_handlers()
        self.init_ui()
        
    def setup_handlers(self):
        """Setup SWF handler connections"""
        self.swf_handler.loading_progress.connect(self.update_progress)
        self.swf_handler.loading_status.connect(self.update_status)
        self.swf_handler.analysis_complete.connect(self.handle_analysis_results)
        self.swf_handler.error_occurred.connect(self.handle_error)
        
    def init_ui(self):
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - File tree and structure
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # File structure tree
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["SWF Structure"])
        self.file_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1D2B3A;
                color: #E6E6E6;
                border: 1px solid #4A90E2;
                border-radius: 2px;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background: #FF6B00;
                color: black;
            }
        """)
        self.file_tree.itemClicked.connect(self.on_item_selected)
        left_layout.addWidget(self.file_tree)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        load_btn = QPushButton("Load SWF")
        load_btn.setStyleSheet("""
            QPushButton {
                background: #FF6B00;
                color: black;
                border: none;
                border-radius: 2px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #FF8533;
            }
        """)
        load_btn.clicked.connect(self.load_swf)
        button_layout.addWidget(load_btn)
        
        extract_btn = QPushButton("Extract")
        extract_btn.setStyleSheet("""
            QPushButton {
                background: #4A90E2;
                color: black;
                border: none;
                border-radius: 2px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: #5BA1E2;
            }
        """)
        extract_btn.clicked.connect(self.extract_resources)
        button_layout.addWidget(extract_btn)
        
        left_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #4A90E2;
                border-radius: 2px;
                background: #1D2B3A;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #FF6B00;
            }
        """)
        self.progress.hide()
        left_layout.addWidget(self.progress)
        
        splitter.addWidget(left_widget)
        
        # Right side - Code view with tabs
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Code editor
        self.code_editor = CodeEditor()
        right_splitter.addWidget(self.code_editor)
        
        # Console output
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1D2B3A;
                color: #E6E6E6;
                border: 1px solid #4A90E2;
                border-radius: 2px;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
        """)
        right_splitter.addWidget(self.console)
        
        # Set initial sizes for right splitter
        right_splitter.setSizes([700, 300])
        
        splitter.addWidget(right_splitter)
        
        # Set initial sizes for main splitter
        splitter.setSizes([300, 700])
        
        self.content_layout.addWidget(splitter)
        
    def load_swf(self):
        """Load and analyze a SWF file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SWF File",
            "",
            "Flash Files (*.swf);;All Files (*.*)"
        )
        if file_path:
            self.progress.show()
            self.progress.setValue(0)
            self.swf_handler.load_swf(file_path)
            
    def update_progress(self, value):
        """Update progress bar"""
        self.progress.setValue(value)
        if value == 100:
            self.progress.hide()
            
    def update_status(self, message):
        """Update console with status message"""
        self.console.appendPlainText(f" {message}")
        
    def handle_error(self, message):
        """Handle error messages"""
        self.console.appendPlainText(f" {message}")
        self.progress.hide()
        
    def handle_analysis_results(self, results):
        """Handle analysis results from SWF handler"""
        self.file_tree.clear()
        
        # Add metadata
        metadata = QTreeWidgetItem(["Metadata"])
        metadata.setForeground(0, QColor("#4A90E2"))
        for key, value in results['metadata'].items():
            item = QTreeWidgetItem([f"{key.replace('_', ' ').title()}: {value}"])
            item.setForeground(0, QColor("#E6E6E6"))
            metadata.addChild(item)
        self.file_tree.addTopLevelItem(metadata)
        
        # Add scripts
        scripts = QTreeWidgetItem(["Scripts"])
        scripts.setForeground(0, QColor("#4A90E2"))
        for script in results['resources']['scripts']:
            name = f"{script['type']} Script ({script['size']} bytes)"
            item = QTreeWidgetItem([name])
            item.setForeground(0, QColor("#E6E6E6"))
            item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'script', 'data': script})
            scripts.addChild(item)
        self.file_tree.addTopLevelItem(scripts)
        
        # Add resources
        resources = QTreeWidgetItem(["Resources"])
        resources.setForeground(0, QColor("#4A90E2"))
        
        # Images
        if results['resources']['images']:
            images = QTreeWidgetItem(["Images"])
            images.setForeground(0, QColor("#4A90E2"))
            for img in results['resources']['images']:
                name = f"ID {img['id']}: {img['type']} {img.get('dimensions', '')} ({img['size']} bytes)"
                item = QTreeWidgetItem([name])
                item.setForeground(0, QColor("#E6E6E6"))
                item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'image', 'data': img})
                images.addChild(item)
            resources.addChild(images)
            
        # Sounds
        if results['resources']['sounds']:
            sounds = QTreeWidgetItem(["Sounds"])
            sounds.setForeground(0, QColor("#4A90E2"))
            for snd in results['resources']['sounds']:
                name = f"ID {snd['id']}: {snd['rate']}Hz {snd['duration']} ({snd['size']} bytes)"
                item = QTreeWidgetItem([name])
                item.setForeground(0, QColor("#E6E6E6"))
                item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'sound', 'data': snd})
                sounds.addChild(item)
            resources.addChild(sounds)
            
        # Fonts
        if results['resources']['fonts']:
            fonts = QTreeWidgetItem(["Fonts"])
            fonts.setForeground(0, QColor("#4A90E2"))
            for font in results['resources']['fonts']:
                name = f"ID {font['id']}: Font v{font['version']} ({font['size']} bytes)"
                item = QTreeWidgetItem([name])
                item.setForeground(0, QColor("#E6E6E6"))
                item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'font', 'data': font})
                fonts.addChild(item)
            resources.addChild(fonts)
            
        # Other resources
        if results['resources']['other']:
            other = QTreeWidgetItem(["Other"])
            other.setForeground(0, QColor("#4A90E2"))
            for res in results['resources']['other']:
                name = f"{res['type']} ({res['size']} bytes)"
                item = QTreeWidgetItem([name])
                item.setForeground(0, QColor("#E6E6E6"))
                item.setData(0, Qt.ItemDataRole.UserRole, {'type': 'other', 'data': res})
                other.addChild(item)
            resources.addChild(other)
            
        self.file_tree.addTopLevelItem(resources)
        self.file_tree.expandAll()
        
    def on_item_selected(self, item):
        """Handle tree item selection"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        if data['type'] == 'script':
            content = self.swf_handler.get_abc_content()
            if content:
                self.code_editor.setPlainText(content)
        
    def extract_resources(self):
        """Extract selected resources"""
        selected = self.file_tree.selectedItems()
        if not selected:
            self.console.appendPlainText("")
            return
            
        save_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Save Resources"
        )
        if save_dir:
            self.progress.show()
            self.progress.setValue(0)
            
            # TODO: Implement actual resource extraction
            total = len(selected)
            for i, item in enumerate(selected):
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data:
                    content = self.swf_handler.get_resource_content(data.get('id'))
                    if content:
                        # Save content
                        pass
                self.progress.setValue(int((i + 1) / total * 100))
            
            self.progress.hide()
            self.console.appendPlainText(f"Resources extracted to {save_dir}")
