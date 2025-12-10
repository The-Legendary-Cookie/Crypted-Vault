# 🔐 The Vault

**The Vault** is an open-source, secure, military-grade encrypted file storage application built with zero-knowledge architecture. Keep your most sensitive data safe with AES-256-GCM encryption, panic mode, and comprehensive audit logging.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

### 🛡️ **Security First**
- **AES-256-GCM Encryption**: Military-grade encryption for all your files.
- **Argon2id Key Derivation**: Memory-hard password hashing resistant to brute-force attacks.
- **Zero-Knowledge Architecture**: Your password never leaves your device.
- **Panic Mode**: Enter a distress password to open a fake, empty vault under coercion.
- **Tamper-Evident Audit Log**: Every action is cryptographically signed and chained to detect tampering.
- **Auto-Lock**: Automatically locks the vault after a configured period of inactivity.

### 📂 **File Management**
- **Multiple Vaults**: Create and manage separate encrypted vaults.
- **Drag & Drop Import**: Easily encrypt files by dragging them into the application.
- **File Versioning**: Automatically keeps the last 5 versions of every file.
- **Version Browser**: View and restore previous file versions with ease.
- **Folder Support**: Organize your encrypted files into folders.
- **Secure Preview**: Preview images and text files directly within the secure environment.

### 🎨 **Modern Interface**
- **Dark Cyberpunk Theme**: A premium, dark-mode UI with smooth animations.
- **Responsive Design**: Resizable panels and clean layout.
- **Context Menus**: Quick access to file operations like renaming, deleting, and exporting.

---

## 🚀 Installation

### Prerequisites
- **Python 3.8 or higher**
- **pip** (Python package manager)

### Step 1: Clone the Repository

```bash
git clone https://github.com/The-Legendary-Cookie/Crypted-Vault.git
cd Crypted-Vault
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run The Vault

```bash
python src/main.py
```

---

## 📖 Usage

### Creating Your First Vault
1. Launch the application: `python src/main.py`
2. Click **"✨ Create New Vault"**.
3. Choose a location to save your `.vault` file.
4. Set a strong **Master Password**.
5. (Optional) Set a **Panic Password** for plausible deniability.
6. Click **"Initialize Vault"**.

### Opening a Vault
1. Launch the application.
2. Click **"📂 Open Existing Vault"**.
3. Select your `.vault` file and enter your password.

### Panic Mode
If you are forced to unlock your vault under duress, enter your **Panic Password** instead of your Master Password. The application will unlock a **fake, empty vault**, keeping your real data hidden and secure.

---

## 🛠️ Development

### Project Structure

```
Crypted-Vault/
├── src/
│   ├── crypto/          # Encryption & key derivation
│   │   ├── core.py
│   │   └── utils.py
│   ├── model/           # Data models
│   │   ├── audit.py
│   │   ├── vault.py
│   │   └── vfs.py
│   ├── ui/              # User interface
│   │   ├── audit_window.py
│   │   ├── auth_dialog.py
│   │   ├── highlighter.py
│   │   ├── main_window.py
│   │   ├── settings_dialog.py
│   │   ├── styles.qss
│   │   ├── tree_widget.py
│   │   └── version_browser.py
│   └── main.py          # Entry point
├── create_demo_vault.py # Utility to create a test vault
├── requirements.txt
└── README.md
```

---

## 📜 License

This project is open source and available under the **MIT License**.

```
MIT License

Copyright (c) 2025 The Legendary Cookie

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
