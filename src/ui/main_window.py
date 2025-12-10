from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator, QTextEdit, 
                             QSplitter, QToolBar, QInputDialog, QMenu,
                             QMessageBox, QFileDialog, QLabel, QStackedWidget, QLineEdit, QApplication)
from PyQt6.QtGui import QAction, QIcon, QFont, QTextCursor, QPixmap, QCursor
from PyQt6.QtCore import Qt, QTimer, QPoint
from src.model.vault import Vault, VaultError
from src.model.vfs import Folder, File
from src.crypto import core
from src.ui.settings_dialog import SettingsDialog
from src.ui.audit_window import AuditLogWindow
from src.ui.version_browser import VersionBrowserDialog
from src.ui.tree_widget import VaultTreeWidget
from src.ui.highlighter import MarkdownHighlighter
import os
import time

class MainWindow(QMainWindow):
    def __init__(self, vault: Vault):
        super().__init__()
        self.vault = vault
        self.current_node = None
        self.setWindowTitle("The Vault")
        self.resize(1750, 1125)  # 1.25x larger for more space
        self.setMinimumSize(1000, 700)  # Minimum size
        
        # Auto-lock
        self.last_interaction = time.time()
        self.lock_timer = QTimer(self)
        self.lock_timer.timeout.connect(self.check_auto_lock)
        self.lock_timer.start(10000) # Check every 10s
        
        # Secure clipboard timer
        self.clipboard_timer = QTimer(self)
        self.clipboard_timer.timeout.connect(self.clear_clipboard)
        self.clipboard_timer.setSingleShot(True)
        
        # Track last saved content for change detection
        self.last_saved_content = ""
        self.unsaved_changes = False
        
        self.setup_ui()
        self.refresh_tree()

    def check_auto_lock(self):
        # 5 minutes timeout
        if time.time() - self.last_interaction > 300:
            self.close()
            QApplication.quit()

    def event(self, event):
        # Reset timer on interaction
        self.last_interaction = time.time()
        return super().event(event)

    def setup_ui(self):
        # Window Setup
        vault_name = os.path.basename(self.vault.path) if self.vault.path else "The Vault"
        self.setWindowTitle(f"THE VAULT - {vault_name}")
        self.setStyleSheet("QMainWindow { border-radius: 10px; }")
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        
        # File Operations
        new_note_act = QAction("📝 New Note", self)
        new_note_act.triggered.connect(self.create_note)
        toolbar.addAction(new_note_act)
        
        add_folder_act = QAction("📁 New Folder", self)
        add_folder_act.triggered.connect(self.add_folder)
        toolbar.addAction(add_folder_act)
        
        add_file_act = QAction("📥 Import File", self)
        add_file_act.triggered.connect(self.add_file)
        toolbar.addAction(add_file_act)
        
        import_folder_act = QAction("📂 Import Folder", self)
        import_folder_act.triggered.connect(self.import_folder)
        toolbar.addAction(import_folder_act)
        
        toolbar.addSeparator()
        
        # Edit Operations
        save_act = QAction("💾 Save", self)
        save_act.triggered.connect(self.save_vault)
        save_act.setShortcut("Ctrl+S")
        toolbar.addAction(save_act)
        
        delete_act = QAction("🗑️ Delete", self)
        delete_act.triggered.connect(self.delete_item)
        toolbar.addAction(delete_act)
        
        export_act = QAction("📤 Export", self)
        export_act.triggered.connect(self.export_file)
        toolbar.addAction(export_act)
        
        export_folder_act = QAction("📁 Export Folder", self)
        export_folder_act.triggered.connect(self.export_folder)
        toolbar.addAction(export_folder_act)
        
        toolbar.addSeparator()
        
        # History & Logs
        version_act = QAction("🕐 Versions", self)
        version_act.triggered.connect(self.show_version_history)
        toolbar.addAction(version_act)
        
        audit_act = QAction("📋 Audit Log", self)
        audit_act.triggered.connect(self.show_audit_window)
        toolbar.addAction(audit_act)
        
        toolbar.addSeparator()
        
        # Vault Management
        backup_act = QAction("💼 Backup", self)
        backup_act.triggered.connect(self.backup_vault)
        toolbar.addAction(backup_act)
        
        settings_act = QAction("⚙️ Settings", self)
        settings_act.triggered.connect(self.show_settings)
        toolbar.addAction(settings_act)
        
        toolbar.addSeparator()
        
        logout_act = QAction("🚪 Logout", self)
        logout_act.triggered.connect(self.logout)
        toolbar.addAction(logout_act)

        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sidebar Layout
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(5, 5, 5, 5)
        
        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_tree)
        sidebar_layout.addWidget(self.search_bar)
        
        # Tree (Custom VaultTreeWidget)
        self.tree = VaultTreeWidget()
        self.tree.main_window = self # Link back for D&D
        self.tree.setHeaderLabel("Vault Content")
        self.tree.itemClicked.connect(self.on_tree_click)
        self.tree.itemExpanded.connect(self.on_item_expanded)
        self.tree.itemCollapsed.connect(self.on_item_collapsed)
        
        # Make arrows visible
        self.tree.setIndentation(20)
        
        # Context Menu
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        sidebar_layout.addWidget(self.tree)
        
        splitter.addWidget(sidebar_widget)
        
        # Editor / Viewer
        self.stack = QStackedWidget()
        
        # Markdown Editor
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.textChanged.connect(self.on_editor_change)
        
        # Enable Ctrl+Scroll zoom
        self.editor.wheelEvent = self.editor_wheel_event
        
        # Apply Syntax Highlighter
        self.highlighter = MarkdownHighlighter(self.editor.document())
        
        self.stack.addWidget(self.editor)
        
        # Viewer Label
        self.viewer_label = QLabel("Select a file to view")
        self.viewer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(self.viewer_label)
        
        # Image Viewer
        self.image_viewer = QLabel()
        self.image_viewer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_viewer.setScaledContents(False)
        self.stack.addWidget(self.image_viewer)
        
        splitter.addWidget(self.stack)
        
        splitter.setSizes([300, 800])
        layout.addWidget(splitter)

    def refresh_tree(self):
        self.tree.clear()
        root_item = QTreeWidgetItem(self.tree, ["/"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.vault.root)
        self.populate_tree(root_item, self.vault.root)
        self.tree.expandAll()

    def populate_tree(self, parent_item, folder: Folder):
        for name, node in folder.children.items():
            # Skip hidden files/folders (starting with .)
            if name.startswith('.'):
                continue
            
            # Add arrow prefix for folders
            display_name = name
            if isinstance(node, Folder):
                display_name = f"▶ {name}"
                
            item = QTreeWidgetItem(parent_item, [display_name])
            item.setData(0, Qt.ItemDataRole.UserRole, node)
            
            if isinstance(node, Folder):
                self.populate_tree(item, node)
                # Update arrow when expanded/collapsed
                item.setExpanded(False)

    def filter_tree(self):
        text = self.search_bar.text().lower()
        it = QTreeWidgetItemIterator(self.tree)
        while it.value():
            item = it.value()
            if text in item.text(0).lower():
                item.setHidden(False)
                p = item.parent()
                while p:
                    p.setHidden(False)
                    p = p.parent()
            else:
                item.setHidden(True)
            it += 1
    
    def on_item_expanded(self, item):
        """Update arrow when folder is expanded"""
        node = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(node, Folder):
            text = item.text(0)
            if text.startswith("▶ "):
                item.setText(0, text.replace("▶", "▼"))
    
    def on_item_collapsed(self, item):
        """Update arrow when folder is collapsed"""
        node = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(node, Folder):
            text = item.text(0)
            if text.startswith("▼ "):
                item.setText(0, text.replace("▼", "▶"))

    def on_tree_click(self, item, column):
        node = item.data(0, Qt.ItemDataRole.UserRole)
        self.current_node = node
        
        if isinstance(node, File):
            if node.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                try:
                    pixmap = QPixmap()
                    pixmap.loadFromData(node.content)
                    scaled = pixmap.scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio, 
                                          Qt.TransformationMode.SmoothTransformation)
                    self.image_viewer.setPixmap(scaled)
                    self.stack.setCurrentWidget(self.image_viewer)
                    self.vault.log_action("FILE_VIEW", node.get_path())
                except Exception as e:
                    self.viewer_label.setText(f"Failed to load image: {e}")
                    self.stack.setCurrentWidget(self.viewer_label)
            else:
                try:
                    text = node.content.decode('utf-8')
                    self.editor.setPlainText(text)
                    self.last_saved_content = text
                    self.unsaved_changes = False
                    self.stack.setCurrentWidget(self.editor)
                    self.vault.log_action("FILE_VIEW", node.get_path())
                except UnicodeDecodeError:
                    self.viewer_label.setText(f"Binary file: {node.name} ({len(node.content)} bytes)")
                    self.stack.setCurrentWidget(self.viewer_label)
        else:
            self.stack.setCurrentWidget(self.viewer_label)
            self.viewer_label.setText("Folder selected")

    def on_editor_change(self):
        if self.current_node and isinstance(self.current_node, File):
            content = self.editor.toPlainText()
            if content != self.last_saved_content:
                if not self.unsaved_changes:
                    self.unsaved_changes = True
                    self.setWindowTitle("The Vault *")
                
                self.current_node.content = content.encode('utf-8')
                self.current_node.modified_at = time.time()
                
                if abs(len(content) - len(self.last_saved_content)) > 10:
                    self.vault.log_action(f"FILE_EDIT_DRAFT", self.current_node.get_path())

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return
            
        node = item.data(0, Qt.ItemDataRole.UserRole)
        if node == self.vault.root:
            return
            
        menu = QMenu()
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(self.rename_item)
        menu.addAction(rename_action)
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_item)
        menu.addAction(delete_action)
        
        if isinstance(node, File):
            export_action = QAction("Export", self)
            export_action.triggered.connect(self.export_file)
            menu.addAction(export_action)
            
            history_action = QAction("Version History", self)
            history_action.triggered.connect(self.show_version_history)
            menu.addAction(history_action)
            
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def rename_item(self):
        if not self.current_node or self.current_node == self.vault.root:
            return
            
        old_name = self.current_node.name
        new_name, ok = QInputDialog.getText(self, "Rename", "New Name:", text=old_name)
        
        if ok and new_name and new_name != old_name:
            try:
                self.vault.rename_node(self.current_node.get_path(), new_name)
                self.refresh_tree()
                self.statusBar().showMessage(f"Renamed to {new_name}", 3000)
            except VaultError as e:
                QMessageBox.critical(self, "Error", str(e))

    def create_note(self):
        name, ok = QInputDialog.getText(self, "New Note", "Note Name (e.g. diary.txt):")
        if ok and name:
            parent_path = self._get_current_parent_path()
            try:
                self.vault.add_file(name, b"", parent_path)
                self.refresh_tree()
            except VaultError as e:
                QMessageBox.critical(self, "Error", str(e))

    def add_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import File")
        if path:
            self.import_file_path(path)

    def import_file_path(self, path):
        """Import a file from a local path"""
        self.import_file_to_folder(path, None)
    
    def import_file_to_folder(self, path, target_folder=None):
        """Import a file from a local path to a specific folder"""
        name = os.path.basename(path)
        try:
            with open(path, 'rb') as f:
                content = f.read()
            
            # Determine parent path
            if target_folder:
                parent_path = target_folder.get_path()
            else:
                parent_path = self._get_current_parent_path()
                
            self.vault.add_file(name, content, parent_path)
            self.refresh_tree()
            self.statusBar().showMessage(f"Imported {name}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {e}")

    def add_folder(self):
        name, ok = QInputDialog.getText(self, "New Folder", "Folder Name:")
        if ok and name:
            parent_path = self._get_current_parent_path()
            try:
                self.vault.create_folder(name, parent_path)
                self.refresh_tree()
            except VaultError as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def import_folder(self):
        """Import an entire folder from the file system"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Import")
        if folder_path:
            folder_name = os.path.basename(folder_path)
            parent_path = self._get_current_parent_path()
            
            try:
                # Create the folder in vault
                new_folder_path = f"{parent_path}/{folder_name}" if parent_path else folder_name
                self.vault.create_folder(folder_name, parent_path)
                
                # Import all files recursively
                self._import_folder_recursive(folder_path, new_folder_path)
                
                self.refresh_tree()
                self.statusBar().showMessage(f"Imported folder: {folder_name}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import folder: {e}")
    
    def _import_folder_recursive(self, source_path, vault_path):
        """Recursively import folder contents"""
        for item in os.listdir(source_path):
            item_path = os.path.join(source_path, item)
            
            if os.path.isfile(item_path):
                # Import file
                with open(item_path, 'rb') as f:
                    content = f.read()
                self.vault.add_file(item, content, vault_path)
            elif os.path.isdir(item_path):
                # Create subfolder and recurse
                new_vault_path = f"{vault_path}/{item}"
                self.vault.create_folder(item, vault_path)
                self._import_folder_recursive(item_path, new_vault_path)

    def delete_item(self):
        if not self.current_node or self.current_node == self.vault.root:
            return
            
        confirm = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete '{self.current_node.name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self.vault.delete_node(self.current_node.get_path())
                self.current_node = None
                self.stack.setCurrentWidget(self.viewer_label)
                self.refresh_tree()
            except VaultError as e:
                QMessageBox.critical(self, "Error", str(e))

    def export_file(self):
        if not self.current_node or not isinstance(self.current_node, File):
            QMessageBox.warning(self, "Warning", "Select a file to export")
            return
            
        pwd, ok = QInputDialog.getText(self, "Authentication", "Confirm Password:", QLineEdit.EchoMode.Password)
        if not ok or not pwd:
            return
            
        derived = core.derive_key(pwd, self.vault.salt)
        if derived != self.vault.key:
            QMessageBox.critical(self, "Error", "Invalid password")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Export File", self.current_node.name)
        if save_path:
            with open(save_path, 'wb') as f:
                f.write(self.current_node.content)
            self.vault.log_action("FILE_EXPORT", self.current_node.get_path())
            QMessageBox.information(self, "Success", "File exported decrypted.")
    
    def export_folder(self):
        """Export an entire folder to the file system"""
        if not self.current_node or not isinstance(self.current_node, Folder):
            QMessageBox.warning(self, "Warning", "Select a folder to export")
            return
        
        # Password confirmation
        pwd, ok = QInputDialog.getText(self, "Authentication", "Confirm Password:", QLineEdit.EchoMode.Password)
        if not ok or not pwd:
            return
            
        derived = core.derive_key(pwd, self.vault.salt)
        if derived != self.vault.key:
            QMessageBox.critical(self, "Error", "Invalid password")
            return
        
        # Select destination
        dest_path = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if dest_path:
            try:
                folder_name = self.current_node.name
                export_path = os.path.join(dest_path, folder_name)
                
                # Create folder
                os.makedirs(export_path, exist_ok=True)
                
                # Export recursively
                self._export_folder_recursive(self.current_node, export_path)
                
                self.vault.log_action("FOLDER_EXPORT", self.current_node.get_path())
                QMessageBox.information(self, "Success", f"Folder exported to {export_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export folder: {e}")
    
    def _export_folder_recursive(self, folder_node, dest_path):
        """Recursively export folder contents"""
        for name, node in folder_node.children.items():
            if name.startswith('.'):  # Skip hidden
                continue
                
            if isinstance(node, File):
                # Export file
                file_path = os.path.join(dest_path, name)
                with open(file_path, 'wb') as f:
                    f.write(node.content)
            elif isinstance(node, Folder):
                # Create subfolder and recurse
                subfolder_path = os.path.join(dest_path, name)
                os.makedirs(subfolder_path, exist_ok=True)
                self._export_folder_recursive(node, subfolder_path)

    def backup_vault(self):
        save_path, _ = QFileDialog.getSaveFileName(self, "Backup Vault", "backup.vault")
        if save_path:
            try:
                with open(self.vault.path, 'rb') as src, open(save_path, 'wb') as dst:
                    dst.write(src.read())
                QMessageBox.information(self, "Success", "Vault backup created.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Backup failed: {e}")

    def _get_current_parent_path(self):
        if self.current_node:
            if isinstance(self.current_node, Folder):
                return self.current_node.get_path()
            elif self.current_node.parent:
                return self.current_node.parent.get_path()
        return ""
    
    def clear_clipboard(self):
        QApplication.clipboard().clear()
        print("Clipboard cleared for security")
    
    def show_settings(self):
        dialog = SettingsDialog(self.vault, self)
        if dialog.exec():
            # Update font size if changed
            if hasattr(dialog, 'font_spin'):
                font_size = dialog.font_spin.value()
                font = self.editor.font()
                font.setPointSize(font_size)
                self.editor.setFont(font)
    
    def save_vault(self):
        try:
            if self.unsaved_changes and self.current_node and isinstance(self.current_node, File):
                self.vault.update_file(self.current_node.get_path(), self.current_node.content)
                self.last_saved_content = self.current_node.content.decode('utf-8')
                self.unsaved_changes = False
                self.setWindowTitle("The Vault")
            else:
                self.vault.save()
            
            self.statusBar().showMessage("✓ Vault saved successfully", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")
    
    def show_version_history(self):
        if not self.current_node or not isinstance(self.current_node, File):
            QMessageBox.warning(self, "Warning", "Select a file to view its version history")
            return
        
        dialog = VersionBrowserDialog(self.current_node, self.vault, self)
        if dialog.exec():
            self.refresh_tree()
            text = self.current_node.content.decode('utf-8')
            self.editor.setPlainText(text)
            self.last_saved_content = text
            self.unsaved_changes = False
    
    def show_audit_window(self):
        dialog = AuditLogWindow(self.vault, self)
        dialog.exec()
    
    def editor_wheel_event(self, event):
        """Handle Ctrl+Scroll to zoom in/out"""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            current_font = self.editor.font()
            current_size = current_font.pointSize()
            
            if delta > 0:  # Scroll up - zoom in
                new_size = min(current_size + 1, 32)
            else:  # Scroll down - zoom out
                new_size = max(current_size - 1, 8)
            
            current_font.setPointSize(new_size)
            self.editor.setFont(current_font)
            event.accept()
        else:
            # Default scroll behavior
            QTextEdit.wheelEvent(self.editor, event)
    
    def logout(self):
        """Close vault and return to login screen"""
        confirm = QMessageBox.question(self, "Logout", 
                                      "Are you sure you want to logout and close this vault?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.close()
    
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.clipboard_timer.start(30000)
