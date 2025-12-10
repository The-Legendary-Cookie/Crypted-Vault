from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QFormLayout, QSpinBox, QGroupBox,
                             QTabWidget, QWidget, QHBoxLayout, QComboBox)
from PyQt6.QtCore import Qt
from src.crypto import core

class SettingsDialog(QDialog):
    def __init__(self, vault, parent=None):
        super().__init__(parent)
        self.vault = vault
        self.setWindowTitle("Vault Settings")
        self.resize(600, 550)
        self.setMinimumSize(500, 450)
        
        layout = QVBoxLayout()
        
        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # General Tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Auto-Lock
        lock_layout = QHBoxLayout()
        lock_layout.addWidget(QLabel("Auto-Lock Timeout (minutes):"))
        self.lock_spin = QSpinBox()
        self.lock_spin.setRange(1, 60)
        self.lock_spin.setValue(5) # Default
        lock_layout.addWidget(self.lock_spin)
        general_layout.addLayout(lock_layout)
        
        # Change Password
        pass_group = QGroupBox("Change Master Password")
        pass_layout = QVBoxLayout()
        
        self.curr_pass = QLineEdit()
        self.curr_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.curr_pass.setPlaceholderText("Current Password")
        pass_layout.addWidget(self.curr_pass)
        
        self.new_pass = QLineEdit()
        self.new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pass.setPlaceholderText("New Password")
        pass_layout.addWidget(self.new_pass)
        
        self.confirm_pass = QLineEdit()
        self.confirm_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pass.setPlaceholderText("Confirm New Password")
        pass_layout.addWidget(self.confirm_pass)
        
        change_btn = QPushButton("Update Password")
        change_btn.clicked.connect(self.change_password)
        pass_layout.addWidget(change_btn)
        
        pass_group.setLayout(pass_layout)
        general_layout.addWidget(pass_group)
        general_layout.addStretch()
        
        tabs.addTab(general_tab, "General")
        
        # Appearance Tab
        app_tab = QWidget()
        app_layout = QVBoxLayout(app_tab)
        
        app_layout.addWidget(QLabel("Theme:"))
        theme_combo = QComboBox()
        theme_combo.addItems(["Cyberpunk (Default)", "Dark Nord", "High Contrast"])
        app_layout.addWidget(theme_combo)
        
        app_layout.addWidget(QLabel("Editor Font Size:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 32)
        self.font_spin.setValue(11)
        app_layout.addWidget(self.font_spin)
        
        app_layout.addStretch()
        tabs.addTab(app_tab, "Appearance")
        
        # Info Tab
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        info_layout.addWidget(QLabel(f"Vault File: {self.vault.path}"))
        info_layout.addWidget(QLabel(f"Panic Mode: {'Active' if self.vault.panic_mode else 'Inactive'}"))
        info_layout.addWidget(QLabel(f"Audit Entries: {len(self.vault.audit.entries)}"))
        info_layout.addStretch()
        tabs.addTab(info_tab, "Info")
        
        # Close Button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def change_password(self):
        current = self.curr_pass.text()
        new = self.new_pass.text()
        confirm = self.confirm_pass.text()
        
        if not current or not new:
            QMessageBox.warning(self, "Error", "All fields required")
            return
            
        if new != confirm:
            QMessageBox.warning(self, "Error", "New passwords don't match")
            return
            
        # Verify current password
        derived = core.derive_key(current, self.vault.salt)
        if derived != self.vault.key:
            QMessageBox.critical(self, "Error", "Current password incorrect")
            return
        
        # Re-encrypt vault with new password
        try:
            # Generate new key
            new_key = core.derive_key(new, self.vault.salt)
            
            # Update vault key
            old_key = self.vault.key
            self.vault.key = new_key
            
            # Update panic hash if exists
            if self.vault.panic_hash:
                # We can't change panic password here, just warn user
                QMessageBox.information(self, "Note", 
                    "Panic password remains unchanged. To update it, you must recreate the vault.")
            
            # Save with new key
            self.vault.log_action("PASSWORD_CHANGE", "vault")
            self.vault.save()
            
            QMessageBox.information(self, "Success", "Password changed successfully!")
            
            # Clear fields
            self.curr_pass.clear()
            self.new_pass.clear()
            self.confirm_pass.clear()
            
        except Exception as e:
            # Rollback
            self.vault.key = old_key
            QMessageBox.critical(self, "Error", f"Failed to change password: {e}")
    
    def get_lock_timeout(self):
        return self.lock_spin.value() * 60  # Convert to seconds
