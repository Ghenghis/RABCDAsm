from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QTreeWidget, QTreeWidgetItem, QSplitter,
                            QListWidget, QListWidgetItem, QFileDialog, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from tool_page import ToolPage
from swf_handler import SWFHandler
import os

class ResourceExtractorPage(ToolPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_title("Resource Extractor")
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
        
        # Left side - Resource list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Resource list
        self.resource_list = QListWidget()
        self.resource_list.setStyleSheet("""
            QListWidget {
                background-color: #1D2B3A;
                color: #E6E6E6;
                border: 1px solid #4A90E2;
                border-radius: 2px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background: #FF6B00;
                color: black;
            }
        """)
        self.resource_list.itemClicked.connect(self.on_resource_selected)
        left_layout.addWidget(self.resource_list)
        
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
        
        extract_btn = QPushButton("Extract Selected")
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
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #E6E6E6;")
        left_layout.addWidget(self.status_label)
        
        splitter.addWidget(left_widget)
        
        # Right side - Preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Preview label
        preview_label = QLabel("Resource Preview")
        preview_label.setStyleSheet("color: #E6E6E6; font-size: 14px;")
        right_layout.addWidget(preview_label)
        
        # Preview area
        self.preview = QLabel()
        self.preview.setStyleSheet("""
            QLabel {
                background: #1D2B3A;
                border: 1px solid #4A90E2;
                border-radius: 2px;
                padding: 10px;
            }
        """)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.preview)
        
        splitter.addWidget(right_widget)
        
        # Set initial sizes
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
        """Update status label"""
        self.status_label.setText(message)
        
    def handle_error(self, message):
        """Handle error messages"""
        self.status_label.setText(f"Error: {message}")
        self.progress.hide()
        
    def handle_analysis_results(self, results):
        """Handle analysis results from SWF handler"""
        self.resource_list.clear()
        
        # Add resources to list
        for res_type in ['images', 'sounds', 'fonts']:
            for res in results['resources'][res_type]:
                item = QListWidgetItem(f"{res_type.title()}: ID {res['id']}")
                item.setData(Qt.ItemDataRole.UserRole, {'type': res_type, 'data': res})
                self.resource_list.addItem(item)
        
    def on_resource_selected(self, item):
        """Handle resource selection"""
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        content = self.swf_handler.get_resource_content(data['data']['id'])
        if content:
            if data['type'] == 'images':
                # Show image preview
                pixmap = QPixmap()
                pixmap.loadFromData(content)
                self.preview.setPixmap(pixmap.scaled(
                    self.preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                # Show info for non-image resources
                self.preview.setText(f"Resource Type: {data['type']}\nSize: {len(content)} bytes")
        
    def extract_resources(self):
        """Extract selected resources"""
        selected = self.resource_list.selectedItems()
        if not selected:
            self.status_label.setText("No resources selected")
            return
            
        save_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Save Resources"
        )
        if save_dir:
            self.progress.show()
            self.progress.setValue(0)
            
            total = len(selected)
            for i, item in enumerate(selected):
                data = item.data(Qt.ItemDataRole.UserRole)
                if data:
                    content = self.swf_handler.get_resource_content(data['data']['id'])
                    if content:
                        # Save content based on type
                        res_type = data['type']
                        res_id = data['data']['id']
                        ext = '.bin'
                        if res_type == 'images':
                            ext = '.png'
                        elif res_type == 'sounds':
                            ext = '.mp3'
                        elif res_type == 'fonts':
                            ext = '.ttf'
                            
                        filename = os.path.join(save_dir, f"{res_type}_{res_id}{ext}")
                        with open(filename, 'wb') as f:
                            f.write(content)
                            
                self.progress.setValue(int((i + 1) / total * 100))
            
            self.progress.hide()
            self.status_label.setText(f"Resources extracted to {save_dir}")
