from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QWidget,
                             QPushButton, QHBoxLayout, QLabel, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt
import time

class VersionBrowserDialog(QDialog):
    def __init__(self, file_node, vault, parent=None):
        super().__init__(parent)
        self.file_node = file_node
        self.vault = vault
        self.setWindowTitle(f"Version History - {file_node.name}")
        self.resize(800, 600)
        
        layout = QHBoxLayout()
        
        # Left: Version list
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Available Versions:"))
        
        self.version_list = QListWidget()
        self.version_list.itemClicked.connect(self.show_version)
        left_layout.addWidget(self.version_list)
        
        # Restore button
        self.restore_btn = QPushButton("Restore Selected Version")
        self.restore_btn.clicked.connect(self.restore_version)
        self.restore_btn.setEnabled(False)
        left_layout.addWidget(self.restore_btn)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(250)
        layout.addWidget(left_widget)
        
        # Right: Content preview
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Content Preview:"))
        
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        right_layout.addWidget(self.preview)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        right_layout.addWidget(close_btn)
        
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        layout.addWidget(right_widget)
        
        self.setLayout(layout)
        self.load_versions()
    
    def load_versions(self):
        self.version_list.clear()
        
        # Add current version
        current_item = QListWidgetItem("📄 Current Version")
        current_item.setData(Qt.ItemDataRole.UserRole, self.file_node)
        self.version_list.addItem(current_item)
        
        # Find .versions folder
        versions_dir = self.vault.root.get_child(".versions")
        if not versions_dir:
            return
        
        # Find versions for this file
        prefix = f"{self.file_node.name}."
        versions = [(name, node) for name, node in versions_dir.children.items() 
                   if name.startswith(prefix)]
        
        # Sort by timestamp (newest first)
        versions.sort(key=lambda x: x[1].created_at, reverse=True)
        
        for name, version_node in versions:
            # Extract timestamp from name
            try:
                ts_str = name.split('.')[-2]
                ts = int(ts_str)
                time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
                item = QListWidgetItem(f"🕐 {time_str}")
                item.setData(Qt.ItemDataRole.UserRole, version_node)
                self.version_list.addItem(item)
            except:
                pass
    
    def show_version(self, item):
        node = item.data(Qt.ItemDataRole.UserRole)
        try:
            content = node.content.decode('utf-8')
            self.preview.setPlainText(content)
            self.restore_btn.setEnabled(item.text() != "📄 Current Version")
        except:
            self.preview.setPlainText("[Binary content - cannot preview]")
            self.restore_btn.setEnabled(False)
    
    def restore_version(self):
        selected = self.version_list.currentItem()
        if not selected or selected.text() == "📄 Current Version":
            return
        
        confirm = QMessageBox.question(self, "Confirm Restore",
            "Are you sure you want to restore this version? Current content will be backed up.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            version_node = selected.data(Qt.ItemDataRole.UserRole)
            
            # Update file content
            self.vault.update_file(self.file_node.get_path(), version_node.content)
            
            QMessageBox.information(self, "Success", "Version restored successfully!")
            self.accept()
