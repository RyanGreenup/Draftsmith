import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QSplitter
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from PyQt6.QtCore import QRegularExpression, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
import markdown
from pygments.formatters import HtmlFormatter
from markdown.extensions.codehilite import CodeHiliteExtension

# Import the needed extensions for markdown
from markdown.extensions.toc import TocExtension
from markdown_katex import KatexExtension


class MarkdownHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Markdown in QTextEdit."""

    def __init__(self, document):
        super().__init__(document)
        self.highlightingRules = []

        # Heading format
        headingFormat = QTextCharFormat()
        headingFormat.setFontWeight(QFont.Weight.Bold)
        headingFormat.setForeground(QColor("blue"))
        self.highlightingRules.append((QRegularExpression("^#{1,6} .+"), headingFormat))

        # Bold format
        boldFormat = QTextCharFormat()
        boldFormat.setFontWeight(QFont.Weight.Bold)
        self.highlightingRules.append((QRegularExpression("\\*\\*(.*?)\\*\\*"), boldFormat))
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
        self.highlightingRules.append((QRegularExpression("\\[.*?]\\(.*?\\)"), linkFormat))

        # Image format
        imageFormat = QTextCharFormat()
        imageFormat.setForeground(QColor("darkMagenta"))
        self.highlightingRules.append((QRegularExpression("!\\[.*?]\\(.*?\\)"), imageFormat))

        # List format
        listFormat = QTextCharFormat()
        listFormat.setForeground(QColor("brown"))
        self.highlightingRules.append((QRegularExpression("^\\s*([-+*])\\s+.*"), listFormat))
        self.highlightingRules.append((QRegularExpression("^\\s*\\d+\\.\\s+.*"), listFormat))

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                index = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(index, length, format)


class MarkdownEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(self.splitter)

        self.editor = QTextEdit()
        self.highlighter = MarkdownHighlighter(self.editor.document())
        self.splitter.addWidget(self.editor)

        self.preview = QWebEngineView()
        self.splitter.addWidget(self.preview)

        self.editor.textChanged.connect(self.updatePreview)
        self.splitter.setSizes([300, 300])

    def updatePreview(self):
        text = self.editor.toPlainText()

        # Convert markdown text to HTML with syntax highlighting and KaTeX math rendering
        html_body = markdown.markdown(text, extensions=[CodeHiliteExtension(linenums=False), KatexExtension()])

        # Get Pygments CSS styles for syntax highlighting
        formatter = HtmlFormatter()
        css_styles = formatter.get_style_defs('.codehilite')

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
            {css_styles}
            </style>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.11.1/dist/katex.min.css" />
        </head>
        <body>
            {html_body}
            <script src="https://cdn.jsdelivr.net/npm/katex@0.11.1/dist/katex.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/katex@0.11.1/dist/contrib/auto-render.min.js"></script>
            <script>
                renderMathInElement(document.body, {{
                    delimiters: [
                        {{left: '$$', right: '$$', display: true}},
                        {{left: '$', right: '$', display: false}}
                    ]
                }});
            </script>
        </body>
        </html>
        """
        self.preview.setHtml(html)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Markdown Editor with Preview')
        self.resize(800, 600)

        self.editor = MarkdownEditor()
        self.setCentralWidget(self.editor)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())

