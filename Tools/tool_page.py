from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QFrame, QStackedWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

class ToolPage(QWidget):
    """Base class for tool pages with common styling and functionality"""
    
    # Signals
    go_home = pyqtSignal()  # Signal to return to main interface
    switch_tool = pyqtSignal(str)  # Signal to switch to another tool
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_base_ui()
        
    def init_base_ui(self):
        """Initialize base UI elements common to all tools"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header bar
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: #1D2B3A;
                border-bottom: 2px solid #4A90E2;
            }
        """)
        self.header_layout = QHBoxLayout(header)  # Store as instance variable
        self.header_layout.setContentsMargins(8, 8, 8, 8)
        
        # Home button
        home_btn = QPushButton("🏠")
        home_btn.setStyleSheet("""
            QPushButton {
                background: #4A90E2;
                color: black;
                border: none;
                border-radius: 2px;
                padding: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #5BA1E2;
            }
        """)
        home_btn.clicked.connect(self.go_home.emit)
        self.header_layout.addWidget(home_btn)
        
        # Tool title
        self.title_label = QLabel()
        self.title_label.setStyleSheet("""
            QLabel {
                color: #E6E6E6;
                font-size: 18px;
                font-weight: bold;
                margin-left: 10px;
            }
        """)
        self.header_layout.addWidget(self.title_label)
        
        # Quick access buttons
        self.quick_access = QHBoxLayout()
        self.quick_access.setSpacing(5)
        self.header_layout.addLayout(self.quick_access)
        
        self.header_layout.addStretch()
        
        # Settings button
        settings_btn = QPushButton("⚙️")
        settings_btn.setStyleSheet("""
            QPushButton {
                background: #4A90E2;
                color: black;
                border: none;
                border-radius: 2px;
                padding: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #5BA1E2;
            }
        """)
        self.header_layout.addWidget(settings_btn)
        
        layout.addWidget(header)
        
        # Content area
        self.content = QFrame()
        self.content.setStyleSheet("""
            QFrame {
                background: #1B2838;
            }
        """)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.content)
        
    def set_title(self, title: str):
        """Set the tool page title"""
        self.title_label.setText(title)
        
    def add_quick_access_button(self, text: str, callback):
        """Add a quick access button to the header"""
        btn = QPushButton(text)
        btn.setStyleSheet("""
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
        btn.clicked.connect(callback)
        self.quick_access.addWidget(btn)
        
    def add_content_widget(self, widget):
        """Add a widget to the content area"""
        self.content_layout.addWidget(widget)
