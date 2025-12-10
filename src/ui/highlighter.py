from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import QRegularExpression

class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Headers (# Header)
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#7aa2f7")) # Blue
        header_format.setFontWeight(QFont.Weight.Bold)
        header_format.setFontPointSize(16) # Make headers bigger
        self.highlighting_rules.append((QRegularExpression(r"^#+ .*"), header_format))

        # Bold (**bold**)
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Weight.Bold)
        bold_format.setForeground(QColor("#bb9af7")) # Purple
        self.highlighting_rules.append((QRegularExpression(r"\*\*.*?\*\*"), bold_format))
        self.highlighting_rules.append((QRegularExpression(r"__.*?__"), bold_format))

        # Italic (*italic*)
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        italic_format.setForeground(QColor("#e0af68")) # Orange
        self.highlighting_rules.append((QRegularExpression(r"\*.*?\*"), italic_format))
        self.highlighting_rules.append((QRegularExpression(r"_.*?_"), italic_format))

        # Code (`code`)
        code_format = QTextCharFormat()
        code_format.setForeground(QColor("#9ece6a")) # Green
        code_format.setFontFamily("Consolas")
        self.highlighting_rules.append((QRegularExpression(r"`.*?`"), code_format))

        # Links ([text](url))
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#7dcfff")) # Cyan
        link_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
        self.highlighting_rules.append((QRegularExpression(r"\[.*?\]\(.*?\)"), link_format))
        
        # Lists (- item)
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#f7768e")) # Red/Pink
        self.highlighting_rules.append((QRegularExpression(r"^\s*[-*+] .*"), list_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
