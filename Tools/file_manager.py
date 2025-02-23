import os
from pathlib import Path
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QTreeView, QHeaderView, QMenu, QTabWidget,
                            QFileDialog, QInputDialog, QMessageBox)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex
import shutil
import send2trash

class FileManager(QWidget):
    """Robust file manager with modern features"""
    
    file_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = Path.home()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Create toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        layout.addWidget(self.tabs)
        
        # Add initial tab
        self.add_tab(self.current_path)
        
    def create_toolbar(self) -> QWidget:
        """Create the file manager toolbar"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation buttons
        self.back_btn = QPushButton("←")
        self.forward_btn = QPushButton("→")
        self.up_btn = QPushButton("↑")
        self.refresh_btn = QPushButton("⟳")
        
        self.back_btn.clicked.connect(self.go_back)
        self.forward_btn.clicked.connect(self.go_forward)
        self.up_btn.clicked.connect(self.go_up)
        self.refresh_btn.clicked.connect(self.refresh_current)
        
        # Add buttons to toolbar
        layout.addWidget(self.back_btn)
        layout.addWidget(self.forward_btn)
        layout.addWidget(self.up_btn)
        layout.addWidget(self.refresh_btn)
        
        # Add new tab button
        new_tab_btn = QPushButton("+")
        new_tab_btn.clicked.connect(lambda: self.add_tab(self.current_path))
        layout.addWidget(new_tab_btn)
        
        layout.addStretch()
        return toolbar
        
    def add_tab(self, path: Path):
        """Add a new file browser tab"""
        browser = FileBrowser()
        browser.file_selected.connect(self.file_selected.emit)
        browser.path_changed.connect(self.update_tab_title)
        
        index = self.tabs.addTab(browser, path.name)
        self.tabs.setCurrentIndex(index)
        
        browser.set_path(path)
        
    def close_tab(self, index: int):
        """Close a tab"""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
            
    def update_tab_title(self, path: Path):
        """Update the title of the current tab"""
        self.tabs.setTabText(self.tabs.currentIndex(), path.name)
        
    def go_back(self):
        """Navigate back in current tab"""
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.go_back()
            
    def go_forward(self):
        """Navigate forward in current tab"""
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.go_forward()
            
    def go_up(self):
        """Navigate up in current tab"""
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.go_up()
            
    def refresh_current(self):
        """Refresh current tab"""
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.refresh()

class FileBrowser(QWidget):
    """Individual file browser widget"""
    
    file_selected = pyqtSignal(str)
    path_changed = pyqtSignal(Path)
    
    def __init__(self):
        super().__init__()
        self.current_path = None
        self.history = []
        self.history_index = -1
        self.init_ui()
        
    def init_ui(self):
        """Initialize the browser UI"""
        layout = QVBoxLayout(self)
        
        # Create tree view
        self.tree = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Name', 'Size', 'Type', 'Modified'])
        
        self.tree.setModel(self.model)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.doubleClicked.connect(self.item_double_clicked)
        
        # Set up header
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.tree)
        
    def set_path(self, path: Path):
        """Set the current path and update view"""
        if self.current_path != path:
            if self.current_path:
                # Add to history
                if self.history_index < len(self.history) - 1:
                    self.history = self.history[:self.history_index + 1]
                self.history.append(self.current_path)
                self.history_index = len(self.history) - 1
            
            self.current_path = path
            self.refresh()
            self.path_changed.emit(path)
            
    def refresh(self):
        """Refresh the current view"""
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Name', 'Size', 'Type', 'Modified'])
        
        try:
            # Add parent directory
            if self.current_path.parent != self.current_path:
                parent_item = self._create_item("..", is_dir=True)
                self.model.appendRow(parent_item)
            
            # Add directories
            for path in sorted(self.current_path.iterdir()):
                try:
                    if path.is_dir():
                        item = self._create_item(path.name, path, is_dir=True)
                        self.model.appendRow(item)
                except PermissionError:
                    continue
            
            # Add files
            for path in sorted(self.current_path.iterdir()):
                try:
                    if path.is_file():
                        item = self._create_item(path.name, path, is_dir=False)
                        self.model.appendRow(item)
                except PermissionError:
                    continue
                    
        except PermissionError:
            QMessageBox.warning(self, "Error", "Permission denied")
            
    def _create_item(self, name: str, path: Optional[Path] = None, is_dir: bool = False) -> List[QStandardItem]:
        """Create a row of items for the model"""
        name_item = QStandardItem(name)
        name_item.setData(path, Qt.ItemDataRole.UserRole)
        
        if path:
            try:
                stats = path.stat()
                size_item = QStandardItem(self._format_size(stats.st_size) if not is_dir else "")
                type_item = QStandardItem("Directory" if is_dir else self._get_file_type(path))
                modified_item = QStandardItem(self._format_date(stats.st_mtime))
            except:
                size_item = QStandardItem("")
                type_item = QStandardItem("Directory" if is_dir else "File")
                modified_item = QStandardItem("")
        else:
            size_item = QStandardItem("")
            type_item = QStandardItem("Directory")
            modified_item = QStandardItem("")
        
        return [name_item, size_item, type_item, modified_item]
        
    def _format_size(self, size: int) -> str:
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
        
    def _format_date(self, timestamp: float) -> str:
        """Format date for display"""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
        
    def _get_file_type(self, path: Path) -> str:
        """Get file type description"""
        ext = path.suffix.lower()
        types = {
            '.txt': 'Text Document',
            '.pdf': 'PDF Document',
            '.doc': 'Word Document',
            '.docx': 'Word Document',
            '.xls': 'Excel Spreadsheet',
            '.xlsx': 'Excel Spreadsheet',
            '.png': 'PNG Image',
            '.jpg': 'JPEG Image',
            '.jpeg': 'JPEG Image',
            '.gif': 'GIF Image',
            '.mp3': 'MP3 Audio',
            '.wav': 'WAV Audio',
            '.mp4': 'MP4 Video',
            '.avi': 'AVI Video',
            '.zip': 'ZIP Archive',
            '.rar': 'RAR Archive',
            '.py': 'Python Script',
            '.js': 'JavaScript File',
            '.html': 'HTML Document',
            '.css': 'CSS Stylesheet',
            '.json': 'JSON File',
            '.xml': 'XML File',
            '.swf': 'Flash SWF File'
        }
        return types.get(ext, f"{ext[1:].upper()} File" if ext else "File")
        
    def show_context_menu(self, position):
        """Show context menu for selected item"""
        index = self.tree.indexAt(position)
        if not index.isValid():
            return
            
        item = self.model.itemFromIndex(index)
        path = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu(self)
        
        if path and path.exists():
            if path.is_dir():
                menu.addAction("Open in New Tab", lambda: self.open_in_new_tab(path))
            else:
                menu.addAction("Open", lambda: self.file_selected.emit(str(path)))
            
            menu.addSeparator()
            menu.addAction("Copy", lambda: self.copy_item(path))
            menu.addAction("Cut", lambda: self.cut_item(path))
            menu.addAction("Delete", lambda: self.delete_item(path))
            menu.addAction("Rename", lambda: self.rename_item(path))
            
        menu.exec(self.tree.viewport().mapToGlobal(position))
        
    def item_double_clicked(self, index: QModelIndex):
        """Handle double-click on item"""
        item = self.model.itemFromIndex(index)
        path = item.data(Qt.ItemDataRole.UserRole)
        
        if not path:
            # Parent directory
            self.go_up()
            return
            
        if path.is_dir():
            self.set_path(path)
        else:
            self.file_selected.emit(str(path))
            
    def go_back(self):
        """Navigate back in history"""
        if self.history_index > 0:
            self.history_index -= 1
            self.current_path = self.history[self.history_index]
            self.refresh()
            self.path_changed.emit(self.current_path)
            
    def go_forward(self):
        """Navigate forward in history"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_path = self.history[self.history_index]
            self.refresh()
            self.path_changed.emit(self.current_path)
            
    def go_up(self):
        """Navigate to parent directory"""
        if self.current_path.parent != self.current_path:
            self.set_path(self.current_path.parent)
            
    def open_in_new_tab(self, path: Path):
        """Signal parent to open path in new tab"""
        parent = self.parent()
        while parent and not isinstance(parent, FileManager):
            parent = parent.parent()
        if parent:
            parent.add_tab(path)
            
    def copy_item(self, path: Path):
        """Copy selected item to clipboard"""
        self._clipboard_path = path
        self._clipboard_operation = "copy"
        
    def cut_item(self, path: Path):
        """Cut selected item to clipboard"""
        self._clipboard_path = path
        self._clipboard_operation = "cut"
        
    def paste_item(self):
        """Paste item from clipboard"""
        if hasattr(self, '_clipboard_path') and self._clipboard_path.exists():
            try:
                if self._clipboard_operation == "copy":
                    if self._clipboard_path.is_dir():
                        shutil.copytree(self._clipboard_path, 
                                      self.current_path / self._clipboard_path.name)
                    else:
                        shutil.copy2(self._clipboard_path, 
                                   self.current_path / self._clipboard_path.name)
                else:  # cut
                    shutil.move(self._clipboard_path, 
                              self.current_path / self._clipboard_path.name)
                    delattr(self, '_clipboard_path')
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Operation failed: {str(e)}")
                
    def delete_item(self, path: Path):
        """Delete selected item"""
        try:
            if QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete {path.name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            ) == QMessageBox.StandardButton.Yes:
                send2trash.send2trash(str(path))
                self.refresh()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Delete failed: {str(e)}")
            
    def rename_item(self, path: Path):
        """Rename selected item"""
        new_name, ok = QInputDialog.getText(
            self, "Rename",
            "Enter new name:",
            text=path.name
        )
        
        if ok and new_name:
            try:
                path.rename(path.parent / new_name)
                self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Rename failed: {str(e)}")
