import json
import os
import tempfile
from typing import Optional
from src.crypto import core, utils
from src.model.vfs import Folder, File
from src.model.audit import AuditLog

class VaultError(Exception):
    pass

import json
import os
import tempfile
import time
from typing import Optional
from src.crypto import core, utils
from src.model.vfs import Folder, File
from src.model.audit import AuditLog

class VaultError(Exception):
    pass

class Vault:
    def __init__(self, path: str = None):
        self.path: str = path
        self.key: Optional[bytes] = None
        self.root: Folder = Folder("root")
        self.audit: AuditLog = AuditLog()
        self.salt: Optional[bytes] = None
        self.panic_mode: bool = False
        self.panic_hash: Optional[str] = None # Hash of the panic password

    def create(self, password: str, panic_password: Optional[str] = None):
        """Create a new vault."""
        self.salt = utils.generate_salt(16)
        self.key = core.derive_key(password, self.salt)
        self.root = Folder("root")
        self.audit = AuditLog()
        self.audit.add_entry("VAULT_CREATE", "root", self.key)
        
        if panic_password:
            # Store hash of panic password + salt
            self.panic_hash = utils.hash_data(panic_password.encode() + self.salt)
            
        self.save()

    def load(self, password: str):
        """Load the vault."""
        if not os.path.exists(self.path):
            raise VaultError("Vault file not found")

        with open(self.path, 'rb') as f:
            try:
                raw = f.read()
                
                # Check for magic bytes
                if len(raw) < 8:
                    raise VaultError("File too short")
                    
                magic = raw[:4]
                if magic == b'TVLT':
                    # New format with base64 encoded header
                    header_len = int.from_bytes(raw[4:8], 'big')
                    encoded_header = raw[8:8+header_len]
                    
                    import base64
                    header_bytes = base64.b64decode(encoded_header)
                    header = json.loads(header_bytes.decode('utf-8'))
                    encrypted_blob = raw[8+header_len:]
                else:
                    # Legacy format (fallback)
                    header_len = int.from_bytes(raw[:4], 'big')
                    header_bytes = raw[4:4+header_len]
                    header = json.loads(header_bytes.decode('utf-8'))
                    encrypted_blob = raw[4+header_len:]
                
            except Exception as e:
                raise VaultError(f"Invalid vault format: {e}")

        # Verify header
        if header.get("version") != 1:
            raise VaultError("Unsupported vault version")
        
        salt_hex = header.get("salt")
        if not salt_hex:
            raise VaultError("Missing salt in header")
            
        self.salt = bytes.fromhex(salt_hex)
        self.panic_hash = header.get("panic_hash")
        
        # Check for panic password
        derived_key = core.derive_key(password, self.salt)
        
        # Check if this is the panic password
        if self.panic_hash:
            input_hash = utils.hash_data(password.encode() + self.salt)
            if input_hash == self.panic_hash:
                self.panic_mode = True
                self.key = derived_key # Use this key for the session, but don't decrypt real data
                self.root = Folder("root") # Empty root
                self.audit = AuditLog() # Empty audit
                return

        # Try to decrypt real data
        try:
            decrypted_bytes = core.decrypt(encrypted_blob, derived_key)
            self.key = derived_key
            self.panic_mode = False
        except Exception:
            raise VaultError("Decryption failed. Wrong password.")
            
        data = json.loads(decrypted_bytes.decode('utf-8'))
        
        self.root = Folder.from_dict(data["root"])
        self.audit = AuditLog.from_list(data["audit"])
        
        # Verify audit integrity
        if not self.audit.verify_integrity(self.key):
            print("WARNING: Audit log integrity check failed!")
            
        self.log_action("VAULT_OPEN", "root")

    def save(self):
        """Save the vault atomically."""
        if not self.key:
            raise VaultError("Vault not initialized")
            
        if self.panic_mode:
            # Do NOT save in panic mode to prevent overwriting real data with empty data
            return

        data = {
            "root": self.root.to_dict(),
            "audit": self.audit.to_list(),
            "settings": {} 
        }
        
        json_bytes = json.dumps(data).encode('utf-8')
        encrypted_blob = core.encrypt(json_bytes, self.key)
        
        header = {
            "version": 1,
            "kdf": "argon2id",
            "salt": self.salt.hex(),
            "cipher": "aes-256-gcm",
            "panic_hash": self.panic_hash
        }
        header_bytes = json.dumps(header).encode('utf-8')
        
        # Base64 encode header for obscurity
        import base64
        encoded_header = base64.b64encode(header_bytes)
        header_len = len(encoded_header)
        
        # Prepend magic bytes for file identification
        magic = b'TVLT'  # "The VauLT"
        final_content = magic + header_len.to_bytes(4, 'big') + encoded_header + encrypted_blob
        
        dir_name = os.path.dirname(os.path.abspath(self.path))
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        with tempfile.NamedTemporaryFile(dir=dir_name, delete=False, mode='wb') as tmp:
            tmp.write(final_content)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = tmp.name
            
        try:
            if os.path.exists(self.path):
                os.replace(tmp_path, self.path)
            else:
                os.rename(tmp_path, self.path)
        except OSError:
            if os.path.exists(self.path):
                os.remove(self.path)
            os.rename(tmp_path, self.path)

    def log_action(self, action: str, target: str):
        if not self.panic_mode:
            self.audit.add_entry(action, target, self.key)

    def add_file(self, name: str, content: bytes, parent_path: str = ""):
        parent = self._resolve_path(parent_path)
        if not isinstance(parent, Folder):
            raise VaultError(f"Path '{parent_path}' is not a folder")
            
        if name in parent.children:
             raise VaultError(f"File '{name}' already exists in '{parent_path}'")
             
        new_file = File(name, parent, content)
        parent.add_child(new_file)
        
        self.log_action("FILE_CREATE", f"{parent_path}/{name}")
        self.save()

    def update_file(self, path: str, content: bytes):
        node = self._resolve_path(path)
        if not isinstance(node, File):
            raise VaultError(f"Path '{path}' is not a file")
            
        # Versioning
        self._create_version(node)
        
        node.content = content
        node.modified_at = time.time()
        
        self.log_action("FILE_EDIT", path)
        self.save()
        
    def _create_version(self, file_node: File):
        """Create a backup version of the file."""
        versions_dir = self.root.get_child(".versions")
        if not versions_dir:
            versions_dir = Folder(".versions", self.root)
            self.root.add_child(versions_dir)
            
        # Name: filename.timestamp.bak
        timestamp = int(time.time())
        version_name = f"{file_node.name}.{timestamp}.bak"
        
        # Create version file
        version_file = File(version_name, versions_dir, file_node.content)
        versions_dir.add_child(version_file)
        
        # Prune old versions
        # Filter versions for this file
        prefix = f"{file_node.name}."
        versions = [n for n in versions_dir.children.values() if n.name.startswith(prefix)]
        versions.sort(key=lambda x: x.created_at)
        
        while len(versions) > 5:
            oldest = versions.pop(0)
            versions_dir.remove_child(oldest.name)

    def create_folder(self, name: str, parent_path: str = ""):
        parent = self._resolve_path(parent_path)
        if not isinstance(parent, Folder):
            raise VaultError(f"Path '{parent_path}' is not a folder")
            
        if name in parent.children:
             raise VaultError(f"Folder '{name}' already exists in '{parent_path}'")
             
        new_folder = Folder(name, parent)
        parent.add_child(new_folder)
        
        self.log_action("FOLDER_CREATE", f"{parent_path}/{name}")
        self.save()

    def delete_node(self, path: str):
        if path == "" or path == "/":
            raise VaultError("Cannot delete root")
            
        parent_path = "/".join(path.split("/")[:-1])
        name = path.split("/")[-1]
        
        parent = self._resolve_path(parent_path)
        if not isinstance(parent, Folder):
            raise VaultError("Parent is not a folder")
            
        if name not in parent.children:
            raise VaultError("Node not found")
            
        parent.remove_child(name)
        self.log_action("DELETE", path)
        self.save()

    def rename_node(self, path: str, new_name: str):
        if path == "" or path == "/":
            raise VaultError("Cannot rename root")
            
        parent_path = "/".join(path.split("/")[:-1])
        old_name = path.split("/")[-1]
        
        if old_name == new_name:
            return
            
        parent = self._resolve_path(parent_path)
        if not isinstance(parent, Folder):
            raise VaultError("Parent is not a folder")
            
        if old_name not in parent.children:
            raise VaultError("Node not found")
            
        if new_name in parent.children:
            raise VaultError(f"Name '{new_name}' already exists")
            
        # Get the node
        node = parent.children[old_name]
        
        # Remove with old name
        del parent.children[old_name]
        
        # Update name
        node.name = new_name
        
        # Add with new name
        parent.children[new_name] = node
        
        self.log_action("RENAME", f"{path} -> {new_name}")
        self.save()

    def _resolve_path(self, path: str) -> Folder:
        if not path or path == "/":
            return self.root
        
        parts = [p for p in path.split("/") if p]
        current = self.root
        for part in parts:
            if isinstance(current, Folder):
                child = current.get_child(part)
                if child:
                    current = child
                else:
                    raise VaultError(f"Path not found: {path}")
            else:
                raise VaultError(f"Path not found (not a folder): {path}")
        return current
