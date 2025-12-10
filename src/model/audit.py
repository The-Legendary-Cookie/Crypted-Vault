import time
import getpass
import platform
from typing import List, Dict, Optional
from src.crypto import utils

class AuditEntry:
    def __init__(self, action: str, target: str, user: str, host: str, timestamp: float, prev_hash: str, signature: str = ""):
        self.action = action
        self.target = target
        self.user = user
        self.host = host
        self.timestamp = timestamp
        self.prev_hash = prev_hash
        self.signature = signature

    def to_dict(self) -> Dict:
        return {
            "action": self.action,
            "target": self.target,
            "user": self.user,
            "host": self.host,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "signature": self.signature
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'AuditEntry':
        return cls(
            action=data["action"],
            target=data["target"],
            user=data["user"],
            host=data["host"],
            timestamp=data["timestamp"],
            prev_hash=data["prev_hash"],
            signature=data.get("signature", "")
        )

    def calculate_hash_content(self) -> bytes:
        """Returns the content to be hashed/signed (excluding signature)."""
        # Deterministic string representation
        s = f"{self.timestamp}:{self.action}:{self.target}:{self.user}:{self.host}:{self.prev_hash}"
        return s.encode('utf-8')

class AuditLog:
    def __init__(self):
        self.entries: List[AuditEntry] = []

    def add_entry(self, action: str, target: str, key: bytes):
        """
        Add a new audit entry.
        key: The HMAC key (derived from vault master key).
        """
        user = getpass.getuser()
        host = platform.node()
        timestamp = time.time()
        
        if self.entries:
            prev_entry = self.entries[-1]
            prev_hash = utils.hash_data(prev_entry.calculate_hash_content())
        else:
            prev_hash = "0" * 64 # Genesis hash

        entry = AuditEntry(action, target, user, host, timestamp, prev_hash)
        
        # Sign the entry
        content = entry.calculate_hash_content()
        entry.signature = utils.hmac_sign(content, key)
        
        self.entries.append(entry)

    def verify_integrity(self, key: bytes) -> bool:
        """
        Verify the chain of hashes and signatures.
        """
        if not self.entries:
            return True

        for i, entry in enumerate(self.entries):
            # Verify signature
            content = entry.calculate_hash_content()
            expected_sig = utils.hmac_sign(content, key)
            if entry.signature != expected_sig:
                print(f"Signature mismatch at index {i}")
                return False

            # Verify chain
            if i > 0:
                prev_entry = self.entries[i-1]
                expected_prev_hash = utils.hash_data(prev_entry.calculate_hash_content())
                if entry.prev_hash != expected_prev_hash:
                    print(f"Chain break at index {i}")
                    return False
            else:
                if entry.prev_hash != "0" * 64:
                    print("Genesis hash mismatch")
                    return False
                    
        return True

    def to_list(self) -> List[Dict]:
        return [e.to_dict() for e in self.entries]

    @classmethod
    def from_list(cls, data: List[Dict]) -> 'AuditLog':
        log = cls()
        log.entries = [AuditEntry.from_dict(d) for d in data]
        return log
