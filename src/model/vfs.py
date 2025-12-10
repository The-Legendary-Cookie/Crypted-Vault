import base64
import time
from typing import Dict, List, Optional, Union

class Node:
    def __init__(self, name: str, parent=None):
        self.name = name
        self.parent = parent
        self.created_at = time.time()
        self.modified_at = time.time()

    def get_path(self) -> str:
        if self.parent:
            return self.parent.get_path() + "/" + self.name
        return "" # Root has empty path or "/"

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "type": "node"
        }

class File(Node):
    def __init__(self, name: str, parent=None, content: bytes = b""):
        super().__init__(name, parent)
        self.content = content # In memory bytes for now. Large files might need chunking.

    def to_dict(self) -> Dict:
        d = super().to_dict()
        d["type"] = "file"
        d["content"] = base64.b64encode(self.content).decode('ascii')
        return d

    @classmethod
    def from_dict(cls, data: Dict, parent=None) -> 'File':
        f = cls(data["name"], parent)
        f.created_at = data["created_at"]
        f.modified_at = data["modified_at"]
        f.content = base64.b64decode(data["content"])
        return f

class Folder(Node):
    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.children: Dict[str, Union['Folder', 'File']] = {}

    def add_child(self, node: Node):
        node.parent = self
        self.children[node.name] = node
        self.modified_at = time.time()

    def remove_child(self, name: str):
        if name in self.children:
            del self.children[name]
            self.modified_at = time.time()

    def get_child(self, name: str) -> Optional[Node]:
        return self.children.get(name)

    def to_dict(self) -> Dict:
        d = super().to_dict()
        d["type"] = "folder"
        d["children"] = {name: child.to_dict() for name, child in self.children.items()}
        return d

    @classmethod
    def from_dict(cls, data: Dict, parent=None) -> 'Folder':
        folder = cls(data["name"], parent)
        folder.created_at = data["created_at"]
        folder.modified_at = data["modified_at"]
        for name, child_data in data["children"].items():
            if child_data["type"] == "folder":
                child = Folder.from_dict(child_data, folder)
            else:
                child = File.from_dict(child_data, folder)
            folder.children[name] = child
        return folder
