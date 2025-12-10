from src.model.vault import Vault
import os
import getpass

def create_demo():
    path = "demo.vault"
    
    if os.path.exists(path):
        os.remove(path)
        
    print("=== Creating Demo Vault ===\n")
    
    # Get passwords securely
    print("Enter Master Password (or press Enter for 'demo123'):")
    password = getpass.getpass("Master Password: ") or "demo123"
    
    print("\nEnter Panic Password (or press Enter for 'panic456', leave blank to skip):")
    panic_password = getpass.getpass("Panic Password: ") or "panic456"
    
    print(f"\nCreating vault at {path}...")
    v = Vault(path)
    v.create(password, panic_password if panic_password else None)
    
    print("Adding folders...")
    v.create_folder("Personal")
    v.create_folder("Work")
    v.create_folder("Secrets")
    
    print("Adding sample files...")
    v.add_file("Welcome.txt", b"Welcome to The Vault!\n\nEverything here is encrypted with AES-256-GCM.", "Personal")
    v.add_file("TODO.txt", b"- Finish project\n- Review security audit\n- Update documentation", "Work")
    v.add_file("passwords.txt", b"GitHub: mypassword123\nEmail: secret@example.com", "Secrets")
    
    print("\n=== Demo Vault Created Successfully ===")
    print("\nYour vault is ready. Run 'python src/main.py' to access it.")
    if panic_password:
        print("\nRemember: Use your panic password if under duress to show an empty vault.")

if __name__ == "__main__":
    create_demo()
