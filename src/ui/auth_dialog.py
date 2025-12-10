from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QHBoxLayout, QFileDialog, QWidget, QStackedWidget)
from PyQt6.QtCore import Qt, QTimer
import os

class AuthDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Vault - Launcher")
        self.resize(825, 750)  # 1.5x larger
        self.setMinimumSize(550, 500)  # Allow resizing but with minimum
        
        # State
        self.vault_path = None
        self.password = None
        self.panic_password = None
        self.mode = None # "open" or "create"
        self.failed_attempts = 0
        
        # Main Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("THE VAULT")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            background-color: #1a1d2d; 
            color: #7aa2f7; 
            font-size: 24px; 
            font-weight: bold; 
            padding: 20px;
            border-bottom: 1px solid #292e42;
        """)
        layout.addWidget(header)
        
        # Stack for different screens
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Screen 1: Welcome / Choice
        self.setup_welcome_screen()
        
        # Screen 2: Login
        self.setup_login_screen()
        
        # Screen 3: Create
        self.setup_create_screen()
        
        self.setLayout(layout)
        
    def setup_welcome_screen(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(15)
        layout.setContentsMargins(40, 20, 40, 40)
        
        lbl = QLabel("Welcome back.\nChoose an action to proceed.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #a9b1d6; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(lbl)
        
        open_btn = QPushButton("📂 Open Existing Vault")
        open_btn.setMinimumHeight(50)
        open_btn.setStyleSheet("font-size: 16px;")
        open_btn.clicked.connect(self.show_open_dialog)
        layout.addWidget(open_btn)
        
        create_btn = QPushButton("✨ Create New Vault")
        create_btn.setMinimumHeight(50)
        create_btn.setStyleSheet("font-size: 16px; background-color: #292e42; color: #c0caf5;")
        create_btn.clicked.connect(self.show_create_dialog)
        layout.addWidget(create_btn)
        
        layout.addStretch()
        self.stack.addWidget(page)

    def setup_login_screen(self):
        self.login_page = QWidget()
        layout = QVBoxLayout(self.login_page)
        layout.setContentsMargins(40, 20, 40, 40)
        
        self.login_path_lbl = QLabel()
        self.login_path_lbl.setWordWrap(True)
        self.login_path_lbl.setStyleSheet("color: #7aa2f7; font-weight: bold; margin-bottom: 10px;")
        self.login_path_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.login_path_lbl)
        
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_edit.setPlaceholderText("Enter Master Password")
        self.pass_edit.returnPressed.connect(self.do_login)
        layout.addWidget(self.pass_edit)
        
        self.login_btn = QPushButton("Unlock Vault")
        self.login_btn.clicked.connect(self.do_login)
        layout.addWidget(self.login_btn)
        
        back_btn = QPushButton("Back")
        back_btn.setStyleSheet("background-color: transparent; color: #565f89;")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(back_btn)
        
        layout.addStretch()
        self.stack.addWidget(self.login_page)

    def setup_create_screen(self):
        self.create_page = QWidget()
        layout = QVBoxLayout(self.create_page)
        layout.setContentsMargins(40, 10, 40, 20)
        
        self.create_path_lbl = QLabel()
        self.create_path_lbl.setWordWrap(True)
        self.create_path_lbl.setStyleSheet("color: #7aa2f7; font-weight: bold; margin-bottom: 5px;")
        self.create_path_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.create_path_lbl)
        
        self.create_pass = QLineEdit()
        self.create_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.create_pass.setPlaceholderText("Master Password")
        layout.addWidget(self.create_pass)
        
        self.create_confirm = QLineEdit()
        self.create_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.create_confirm.setPlaceholderText("Confirm Password")
        layout.addWidget(self.create_confirm)
        
        # Panic Password
        panic_lbl = QLabel("Optional: Panic Password (for Duress)")
        panic_lbl.setStyleSheet("margin-top: 5px; color: #565f89; font-size: 12px;")
        layout.addWidget(panic_lbl)
        
        self.panic_pass = QLineEdit()
        self.panic_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.panic_pass.setPlaceholderText("Panic Password (Optional)")
        self.panic_pass.setMinimumHeight(35)
        layout.addWidget(self.panic_pass)
        
        self.panic_confirm = QLineEdit()
        self.panic_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.panic_confirm.setPlaceholderText("Confirm Panic Password")
        self.panic_confirm.setMinimumHeight(35)
        layout.addWidget(self.panic_confirm)
        
        create_btn = QPushButton("Initialize Vault")
        create_btn.clicked.connect(self.do_create)
        layout.addWidget(create_btn)
        
        back_btn = QPushButton("Back")
        back_btn.setStyleSheet("background-color: transparent; color: #565f89;")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        layout.addWidget(back_btn)
        
        layout.addStretch()
        self.stack.addWidget(self.create_page)

    def show_open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Vault File", "", "Vault Files (*.vault);;All Files (*)")
        if path:
            self.vault_path = path
            self.mode = "open"
            self.login_path_lbl.setText(f"Opening: {os.path.basename(path)}")
            self.pass_edit.clear()
            self.pass_edit.setFocus()
            self.stack.setCurrentWidget(self.login_page)

    def show_create_dialog(self):
        path, _ = QFileDialog.getSaveFileName(self, "Create New Vault", "MyVault.vault", "Vault Files (*.vault)")
        if path:
            self.vault_path = path
            self.mode = "create"
            self.create_path_lbl.setText(f"Creating: {os.path.basename(path)}")
            self.create_pass.clear()
            self.create_confirm.clear()
            self.panic_pass.clear()
            self.create_pass.setFocus()
            self.stack.setCurrentWidget(self.create_page)

    def do_login(self):
        pwd = self.pass_edit.text()
        if not pwd:
            return
            
        # Brute force delay
        if self.failed_attempts >= 3:
            delay = 2000 if self.failed_attempts < 5 else 10000
            self.login_btn.setEnabled(False)
            self.login_btn.setText(f"Wait {delay//1000}s...")
            QTimer.singleShot(delay, lambda: self.reset_login_btn())
            return
            
        self.password = pwd
        self.accept()

    def reset_login_btn(self):
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Unlock Vault")

    def do_create(self):
        p1 = self.create_pass.text()
        p2 = self.create_confirm.text()
        panic = self.panic_pass.text()
        panic_conf = self.panic_confirm.text()
        
        if not p1:
            QMessageBox.warning(self, "Error", "Password required")
            return
        if p1 != p2:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return
        if panic and panic != panic_conf:
            QMessageBox.warning(self, "Error", "Panic passwords do not match")
            return
        if panic and panic == p1:
            QMessageBox.warning(self, "Error", "Panic password cannot be same as Master password")
            return
            
        self.password = p1
        self.panic_password = panic if panic else None
        self.accept()
