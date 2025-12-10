import sys
import os

# Ensure src is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication, QMessageBox
from src.model.vault import Vault, VaultError
from src.ui.main_window import MainWindow
from src.ui.auth_dialog import AuthDialog

def main():
    app = QApplication(sys.argv)
    
    # Load Styles
    style_path = os.path.join(os.path.dirname(__file__), "ui", "styles.qss")
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    
    # Main Loop - allows returning to launcher after logout
    while True:
        # Authentication / Launcher Loop
        vault = None
        while vault is None:
            auth = AuthDialog()
            if auth.exec() != AuthDialog.DialogCode.Accepted:
                sys.exit(0)
                
            # Initialize Vault
            vault = Vault(auth.vault_path)
            
            try:
                if auth.mode == "create":
                    vault.create(auth.password, auth.panic_password)
                else:
                    vault.load(auth.password)
                    
                # If successful, break auth loop
                break
                
            except VaultError as e:
                auth.failed_attempts += 1
                QMessageBox.critical(None, "Error", str(e))
                vault = None  # Reset to loop again
                continue
        
        # Main Window
        window = MainWindow(vault)
        window.show()
        
        # Run the app and wait for window to close
        app.exec()
        
        # If we get here, the window was closed (logout)
        # Loop back to show launcher again
        
if __name__ == "__main__":
    main()
