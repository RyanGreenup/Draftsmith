from PyQt6.QtWidgets import QTextEdit, QToolBar
from PyQt6.QtGui import QAction, QIcon, QKeyEvent, QTextCursor, QKeySequence
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from vimkeys import VimTextEdit
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
        # These buttons are included only as an exemplar, probably
        # Use the toolbar instead as it deals with the actions
        # and Keyboard shortcuts
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
            markdown_content = Markdown(
                text=text, css_path=self.css_file, dark_mode=self.dark_mode
            )
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
                "pymdownx.superfences",
                "pymdownx.blocks.details",
                "admonition",
                "toc",
            ],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "linenums": False,
                    "guess_lang": False,
                }
            },
        )

        return html_body

    def build_css(self) -> str:
        css_styles = ""
        if self.css_path:
            with open(self.css_path, "r") as file:
                css_styles += file.read()

        # Add Pygments CSS for code highlighting
        formatter = HtmlFormatter(style="default" if not self.dark_mode else "monokai")
        pygments_css = formatter.get_style_defs(".highlight")

        # Modify Pygments CSS for dark mode
        if self.dark_mode:
            pygments_css = pygments_css.replace(
                "background: #f8f8f8", "background: #2d2d2d"
            )
            pygments_css += """
            .highlight {
                background-color: #2d2d2d;
            }
            .highlight pre {
                background-color: #2d2d2d;
            }
            .highlight .hll {
                background-color: #2d2d2d;
            }
            """

        css_styles += pygments_css

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


class PreviewAction(QAction):
    def __init__(self, markdown_editor):
        super().__init__(
            QIcon("icons/magnifier.png"), "Toggle Preview", markdown_editor
        )
        self.setStatusTip("Toggle Side by Side Preview")
        self.triggered.connect(markdown_editor.toggle_preview)
        self.setShortcut("Alt+G")
        self.setCheckable(True)


class DarkModeAction(QAction):
    def __init__(self, main_window):
        super().__init__(QIcon("icons/lightning.png"), "Dark Mode", main_window)
        self.setStatusTip("Toggle Side by Side Preview")
        self.triggered.connect(main_window.toggle_app_dark_mode)
        self.setShortcut("Alt+D")
        self.setCheckable(True)


class OverlayPreviewAction(QAction):
    def __init__(self, markdown_editor):
        super().__init__(QIcon("icons/acorn.png"), "Overlay Preview", markdown_editor)
        self.setStatusTip("Replace Editor with Preview")
        self.triggered.connect(markdown_editor.toggle_preview_overlay)
        self.setShortcut("Alt+O")
        self.setCheckable(True)


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

        # Create a Toolbar
        self.create_toolbar()

    def create_toolbar(self):
        # Create a Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))

        actions = {
            "view": {
                "darkmode": DarkModeAction(self),
                "preview": PreviewAction(self.markdown_editor),
                "overlay": OverlayPreviewAction(self.markdown_editor),
            },
        }
        # preview_button = PreviewAction(self.markdown_editor)
        # darkmode_action = DarkModeAction(self)
        # overlay_preview_action = OverlayPreviewAction(self.markdown_editor)

        for action in actions["view"].values():
            toolbar.addAction(action)

        # Fill the Toolbar
        self.addToolBar(toolbar)

        # Add a Menu
        menu = self.menuBar()
        if menu:
            file_menu = menu.addMenu("File")
            view_menu = menu.addMenu("View")
            if view_menu:
                for action in actions["view"].values():
                    view_menu.addAction(action)

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
        toggle_overlay_shortcut.activated.connect(
            self.markdown_editor.toggle_preview_overlay
        )

        # Toggle Dark Mode shortcut
        toggle_dark_mode_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        toggle_dark_mode_shortcut.activated.connect(
            self.dark_mode_button.toggle_dark_mode
        )


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
