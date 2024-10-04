from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QKeyEvent, QTextCursor
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from pygments.formatters import HtmlFormatter
import markdown
from pathlib import Path
import sys
import argparse
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QSplitter,
    QPushButton,
    QTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QFont,
    QColor,
    QPalette,
    QKeyEvent,
)


def get_dark_palette():
    """
    Return a QPalette with a dark color scheme.
    """
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    return dark_palette


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
        self.highlightingRules.append((QRegularExpression("^\\s*```.*"), codeFormat))

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


class DarkModeButton(QPushButton):
    dark_mode_toggled = pyqtSignal(bool)

    def __init__(self):
        super().__init__("Toggle Dark Mode")
        self.setCheckable(True)
        self.clicked.connect(self.toggle_dark_mode)
        self.dark_mode = False

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.dark_mode_toggled.emit(self.dark_mode)


class VimTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vim_mode = False

    def keyPressEvent(self, e: QKeyEvent):
        if self.vim_mode:
            if e.key() == Qt.Key.Key_Escape:
                self.vim_mode = False
            elif e.key() == Qt.Key.Key_H:
                self.moveCursor(QTextCursor.MoveOperation.Left)
            elif e.key() == Qt.Key.Key_J:
                self.moveCursor(QTextCursor.MoveOperation.Down)
            elif e.key() == Qt.Key.Key_K:
                self.moveCursor(QTextCursor.MoveOperation.Up)
            elif e.key() == Qt.Key.Key_L:
                self.moveCursor(QTextCursor.MoveOperation.Right)
            elif e.key() == Qt.Key.Key_I:
                self.vim_mode = False
            # Add more Vim-like behaviors here.
        else:
            if e.key() == Qt.Key.Key_Escape:
                self.vim_mode = True
            else:
                super().keyPressEvent(e)


class MarkdownEditor(QWidget):
    """A QWidget containing a Markdown editor with live preview."""

    def __init__(self, css_file=None):
        super().__init__()
        self.css_file = css_file
        self.dark_mode = False

        # Create the editor and preview widgets
        self.editor = VimTextEdit()
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

        markdown_content = Markdown(text=text, dark_mode=self.dark_mode)
        self.preview.setHtml(markdown_content.build_html())


class Markdown:
    def __init__(
        self, text: str, css_path: Path | None = None, dark_mode: bool = False
    ):
        self.css_path = css_path
        self.text = text
        self.dark_mode = dark_mode

    def make_html(self) -> str:
        # Generate the markdown with extensions
        html_body = markdown.markdown(
            self.text,
            extensions=[
                "markdown_katex",
                "codehilite",
                "fenced_code",
                "tables",
                # [^2] This extension is needed for indented code blocks, like under lists
                "pymdownx.superfences",
                # Admonition blocks [^1]
                "pymdownx.blocks.details",
                "admonition",
                "toc",
            ],
        )

        return html_body

    def build_css(self, css_file: Path | None = None) -> str:
        css_styles = ""
        if css_file:
            with open(css_file, "r") as file:
                css_styles += file.read()
        formatter = HtmlFormatter()
        css_styles += formatter.get_style_defs(".codehilite")

        # Add dark mode styles if enabled
        if self.dark_mode:
            dark_mode_styles = """
            body {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            a {
                color: #3794ff;
            }
            code {
                background-color: #2d2d2d;
            }
            """
            css_styles += dark_mode_styles
        return css_styles

    def build_html(self) -> str:
        html_body = self.make_html()
        css_styles = self.build_css()
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
        return html


class MainWindow(QMainWindow):
    """Main window containing the Markdown editor."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown Editor with Preview")
        self.resize(800, 600)

        # Initialize the Markdown editor
        self.markdown_editor = MarkdownEditor(css_file=args.css)
        # Initialize the dark mode button
        self.dark_mode_button = DarkModeButton()

        # Set the Central Widget and Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.addWidget(self.dark_mode_button)
        self.main_layout.addWidget(self.markdown_editor)

        # Connect dark mode toggle signal
        self.dark_mode_button.dark_mode_toggled.connect(self.toggle_app_dark_mode)

    def toggle_app_dark_mode(self, is_dark):
        """
        Toggle the dark mode of the application.
        """
        app = QApplication.instance()
        if is_dark:
            app.setStyle("Fusion")
            app.setPalette(get_dark_palette())
        else:
            app.setStyle("Fusion")
            app.setPalette(app.style().standardPalette())

        # Update the markdown editor's dark mode
        self.markdown_editor.dark_mode = is_dark
        self.markdown_editor.update_preview()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Markdown Editor with Preview")
    parser.add_argument(
        "--css", type=str, help="Path to a CSS file for the markdown preview"
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


# Footnotes
# [^1]: https://facelessuser.github.io/pymdown-extensions/extensions/blocks/plugins/details/
# [^2]: https://github.com/mkdocs/mkdocs/issues/282
