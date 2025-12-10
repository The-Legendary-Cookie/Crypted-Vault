from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QHBoxLayout, QLabel, QTextEdit, QSplitter)
from PyQt6.QtCore import Qt
import time

class AuditLogWindow(QDialog):
    def __init__(self, vault, parent=None):
        super().__init__(parent)
        self.vault = vault
        self.setWindowTitle("Audit Log - Complete History")
        self.resize(1000, 600)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel(f"Total Entries: {len(self.vault.audit.entries)}")
        header.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)
        
        # Splitter for table and details
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Audit table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Time", "Action", "Target", "User", "Host"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.show_details)
        splitter.addWidget(self.table)
        
        # Details view
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("Select an entry to view details...")
        splitter.addWidget(self.details)
        
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        self.refresh()
    
    def refresh(self):
        self.table.setRowCount(0)
        # Show newest first
        for entry in reversed(self.vault.audit.entries):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry.timestamp))
            
            self.table.setItem(row, 0, QTableWidgetItem(ts))
            self.table.setItem(row, 1, QTableWidgetItem(entry.action))
            self.table.setItem(row, 2, QTableWidgetItem(entry.target))
            self.table.setItem(row, 3, QTableWidgetItem(entry.user))
            self.table.setItem(row, 4, QTableWidgetItem(entry.host))
            
            # Store entry object in first column
            self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, entry)
        
        self.table.resizeColumnsToContents()
    
    def show_details(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        
        entry = self.table.item(selected[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        
        details = f"""
=== Audit Entry Details ===

Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(entry.timestamp))}
Action: {entry.action}
Target: {entry.target}
User: {entry.user}
Host: {entry.host}

Previous Hash: {entry.prev_hash}
Signature: {entry.signature}

Chain Position: {self.vault.audit.entries.index(entry) + 1} of {len(self.vault.audit.entries)}
"""
        self.details.setPlainText(details)
