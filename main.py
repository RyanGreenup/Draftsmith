from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QKeyEvent, QTextCursor, QKeySequence
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
    QShortcut,
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
        super().__init__("Toggle Dark Mode (Ctrl+D)")
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
        self.insert_mode = False
        self.visual_mode = False
        self.visual_anchor = None
        self.yanked_text = ""

    def keyPressEvent(self, e: QKeyEvent):
        if not self.vim_mode:
            if e.key() == Qt.Key.Key_Escape:
                self.vim_mode = True
                self.insert_mode = False
                self.visual_mode = False
            else:
                super().keyPressEvent(e)
        elif self.insert_mode:
            if e.key() == Qt.Key.Key_Escape:
                self.insert_mode = False
            else:
                super().keyPressEvent(e)
        elif self.visual_mode:
            self.handle_visual_mode(e)
        else:
            self.handle_normal_mode(e)

    def handle_normal_mode(self, e: QKeyEvent):
        cursor = self.textCursor()
        if e.key() == Qt.Key.Key_H:
            cursor.movePosition(QTextCursor.MoveOperation.Left)
        elif e.key() == Qt.Key.Key_J:
            cursor.movePosition(QTextCursor.MoveOperation.Down)
        elif e.key() == Qt.Key.Key_K:
            cursor.movePosition(QTextCursor.MoveOperation.Up)
        elif e.key() == Qt.Key.Key_L:
            cursor.movePosition(QTextCursor.MoveOperation.Right)
        elif e.key() == Qt.Key.Key_I:
            self.insert_mode = True
        elif e.key() == Qt.Key.Key_V:
            self.visual_mode = True
            self.visual_anchor = cursor.position()
        elif e.key() == Qt.Key.Key_P:
            self.put_text(cursor)
        self.setTextCursor(cursor)

    def handle_visual_mode(self, e: QKeyEvent):
        cursor = self.textCursor()
        if e.key() == Qt.Key.Key_Escape:
            self.exit_visual_mode(cursor)
        elif e.key() == Qt.Key.Key_J:
            cursor.movePosition(
                QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor
            )
        elif e.key() == Qt.Key.Key_K:
            cursor.movePosition(
                QTextCursor.MoveOperation.Up, QTextCursor.MoveMode.KeepAnchor
            )
        elif e.key() == Qt.Key.Key_Y:
            self.yank_text(cursor)
        self.setTextCursor(cursor)

    def exit_visual_mode(self, cursor):
        self.visual_mode = False
        cursor.clearSelection()
        self.setTextCursor(cursor)

    def yank_text(self, cursor):
        self.yanked_text = cursor.selectedText()
        self.exit_visual_mode(cursor)

    def put_text(self, cursor):
        if self.yanked_text:
            cursor.insertText(self.yanked_text)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.vim_mode = False
        self.insert_mode = False
        self.visual_mode = False


class MarkdownEditor(QWidget):
    """A QWidget containing a Markdown editor with toggleable live preview."""

    def __init__(self, css_file=None):
        super().__init__()
        self.css_file = css_file
        self.dark_mode = False
        self.preview_visible = True
        self.preview_overlay = False
        self.setup_ui()

    def setup_ui(self):
        # Create the editor and preview widgets
        self.editor = VimTextEdit()
        self.preview = QWebEngineView()
        self.button = QPushButton("Hide Preview (Ctrl+P)")
        self.button.clicked.connect(self.toggle_preview)

        self.overlay_button = QPushButton("Overlay Preview (Ctrl+O)")
        self.overlay_button.setCheckable(True)
        self.overlay_button.clicked.connect(self.toggle_preview_overlay)

        # Create a splitter to divide editor and preview
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([300, 300])

        # Setup the layout
        self.main_layout = QVBoxLayout()

        # Build the layout
        self.build_layout()

        # Apply syntax highlighting to the editor
        self.highlighter = MarkdownHighlighter(self.editor.document())

        # Connect the Editor with the Preview
        self.editor.textChanged.connect(self.update_preview)

    def build_layout(self):
        # Todo put these side by side
        self.main_layout.addWidget(self.overlay_button)
        self.main_layout.addWidget(self.button)
        self.main_layout.addWidget(self.splitter)
        self.setLayout(self.main_layout)

    def toggle_preview(self):
        self.preview_visible = not self.preview_visible
        if self.preview_visible:
            self.preview.show()
            self.button.setText("Hide Preview (Ctrl+P)")
            self.splitter.setSizes([300, 300])
            self.update_preview()
        else:
            self.preview.hide()
            self.button.setText("Show Preview (Ctrl+P)")
            self.splitter.setSizes([600, 0])

    def toggle_preview_overlay(self):
        # TODO, the preview needs to be initialized or something because of the flickering issue
        if self.preview_overlay:
            self.editor.hide()
            self.update_preview()
            self.preview.show()
        else:
            self.editor.show()
            if self.preview_visible:
                self.preview.show()

        self.preview_overlay = not self.preview_overlay
        self.overlay_button.setChecked(self.preview_overlay)

    def update_preview(self):
        """Update the Markdown preview."""
        if self.preview_visible or self.preview_overlay:
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

        # Setup shortcuts
        self.setup_shortcuts()

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

    def setup_shortcuts(self):
        # Toggle Preview shortcut
        toggle_preview_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        toggle_preview_shortcut.activated.connect(self.markdown_editor.toggle_preview)

        # Toggle Overlay Preview shortcut
        toggle_overlay_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        toggle_overlay_shortcut.activated.connect(self.markdown_editor.toggle_preview_overlay)

        # Toggle Dark Mode shortcut
        toggle_dark_mode_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        toggle_dark_mode_shortcut.activated.connect(self.dark_mode_button.toggle_dark_mode)


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
