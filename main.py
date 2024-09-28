import sys
import argparse
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QSplitter,
    QDialog,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QFont,
    QColor,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

import markdown
from pygments.formatters import HtmlFormatter


class MarkdownHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Markdown code in QTextEdit."""

    def __init__(self, document):
        super().__init__(document)
        # Define the highlighting rules
        self.highlightingRules = []

        # Heading format
        headingFormat = QTextCharFormat()
        headingFormat.setFontWeight(QFont.Weight.Bold)
        headingFormat.setForeground(QColor("blue"))
        # Headings: lines starting with one or more '#' characters
        self.highlightingRules.append((QRegularExpression("^#{1,6} .+"), headingFormat))

        # Bold format
        boldFormat = QTextCharFormat()
        boldFormat.setFontWeight(QFont.Weight.Bold)
        self.highlightingRules.append(
            (QRegularExpression("\\*\\*(.*?)\\*\\*"), boldFormat)
        )
        self.highlightingRules.append((QRegularExpression("__(.*?)__"), boldFormat))

        # Italic format
        italicFormat = QTextCharFormat()
        italicFormat.setFontItalic(True)
        self.highlightingRules.append((QRegularExpression("\\*(.*?)\\*"), italicFormat))
        self.highlightingRules.append((QRegularExpression("_(.*?)_"), italicFormat))

        # Code format
        codeFormat = QTextCharFormat()
        codeFormat.setFontFamily("Courier")
        codeFormat.setForeground(QColor("darkGreen"))
        self.highlightingRules.append((QRegularExpression("`[^`]+`"), codeFormat))
        self.highlightingRules.append((QRegularExpression("^```.*"), codeFormat))

        # Link format
        linkFormat = QTextCharFormat()
        linkFormat.setForeground(QColor("darkBlue"))
        self.highlightingRules.append(
            (QRegularExpression("\\[.*?\\]\\(.*?\\)"), linkFormat)
        )

        # Image format
        imageFormat = QTextCharFormat()
        imageFormat.setForeground(QColor("darkMagenta"))
        self.highlightingRules.append(
            (QRegularExpression("!\\[.*?\\]\\(.*?\\)"), imageFormat)
        )

        # List format
        listFormat = QTextCharFormat()
        listFormat.setForeground(QColor("brown"))
        self.highlightingRules.append(
            (QRegularExpression("^\\s*([-+*])\\s+.*"), listFormat)
        )
        self.highlightingRules.append(
            (QRegularExpression("^\\s*\\d+\\.\\s+.*"), listFormat)
        )

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                index = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(index, length, format)


class MarkdownEditor(QWidget):
    """A QWidget containing a Markdown editor with live preview."""

    def __init__(self, css_file=None):
        super().__init__()
        self.css_file = css_file
    """A QWidget containing a Markdown editor with live preview."""

    def __init__(self, css_file=None):
        super().__init__()
        self.css_file = css_file

        # Create the editor and preview widgets
        self.editor = QTextEdit()
        self.preview = QWebEngineView()

        # Apply syntax highlighting to the editor
        self.highlighter = MarkdownHighlighter(self.editor.document())

        # Create a splitter to divide editor and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setSizes([300, 300])

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        # Connect signals
        self.editor.textChanged.connect(self.update_preview)

    def update_preview(self):
        """Update the Markdown preview."""
        text = self.editor.toPlainText()

        # Generate the markdown with extensions
        html_body = markdown.markdown(
            text, extensions=["markdown_katex", "codehilite", "fenced_code"]
        )

        # Get the CSS styles for code highlighting and additional CSS if provided
        css_styles = ""
        if self.css_file:
            with open(self.css_file, 'r') as file:
                css_styles += file.read()
        formatter = HtmlFormatter()
        css_styles += formatter.get_style_defs(".codehilite")

        # Build the full HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
            {css_styles}
            </style>
            <!-- KaTeX CSS -->
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.15.1/dist/katex.min.css" crossorigin="anonymous">
        </head>
        <body>
            {html_body}
            <!-- KaTeX JS -->
            <script defer src="https://cdn.jsdelivr.net/npm/katex@0.15.1/dist/katex.min.js" crossorigin="anonymous"></script>
            <script defer src="https://cdn.jsdelivr.net/npm/katex@0.15.1/dist/contrib/auto-render.min.js" crossorigin="anonymous"></script>
            <script>
            document.addEventListener("DOMContentLoaded", function() {{
                renderMathInElement(document.body, {{
                    delimiters: [
                      {{left: "$$", right: "$$", display: true}},
                      {{left: "$", right: "$", display: false}}
                    ]
                }});
            }});
            </script>
        </body>
        </html>
        """
        self.preview.setHtml(html)


class MainWindow(QMainWindow):
    """Main window containing the Markdown editor."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown Editor with Preview")
        self.resize(800, 600)

        # Initialize the Markdown editor
        self.markdown_editor = MarkdownEditor(css_file=args.css)
        self.setCentralWidget(self.markdown_editor)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Markdown Editor with Preview")
    parser.add_argument("--css", type=str, help="Path to a CSS file for the markdown preview")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


