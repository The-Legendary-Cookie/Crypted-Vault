from PyQt6.QtWidgets import QTreeWidget, QAbstractItemView
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
import os

class VaultTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(False)  # Disable internal drag to prevent duplicates
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)  # Only accept external drops
        self.main_window = None # Will be set by MainWindow

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            # Handle file import from OS
            urls = event.mimeData().urls()
            
            # Determine target folder
            drop_item = self.itemAt(event.position().toPoint())
            target_folder = None
            
            if drop_item and self.main_window:
                node = drop_item.data(0, Qt.ItemDataRole.UserRole)
                from src.model.vfs import Folder
                
                if isinstance(node, Folder):
                    target_folder = node
                elif node and node.parent:
                    target_folder = node.parent
            
            # Import files
            for url in urls:
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    if self.main_window:
                        self.main_window.import_file_to_folder(file_path, target_folder)
                        
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
