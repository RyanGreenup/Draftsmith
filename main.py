import os
from PyQt6.QtWidgets import QTextEdit, QToolBar
from PyQt6.QtGui import QAction, QIcon, QKeyEvent, QTextCursor, QKeySequence
from markdown_utils import Markdown
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
    QFileDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression, QFile, QTextStream, QTimer
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
        for i in range(1, 7):
            headingFormat = QTextCharFormat()
            headingFormat.setFontWeight(QFont.Weight.Bold)
            headingFormat.setForeground(QColor("blue"))
            headingFormat.setFontPointSize(24 - i * 2)
            hashes = "#" * i
            self.highlightingRules.append(
                (QRegularExpression(f"^{hashes} .+"), headingFormat)
            )

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


class OpenAction(QAction):
    def __init__(self, main_window):
        super().__init__(QIcon("icons/folder-open.png"), "Open", main_window)
        self.setStatusTip("Open a markdown file")
        self.triggered.connect(lambda: main_window.open_file(None))
        self.setShortcut("Ctrl+O")

class SaveAction(QAction):
    def __init__(self, main_window):
        super().__init__(QIcon("icons/disk.png"), "Save", main_window)
        self.setStatusTip("Save the current file")
        self.triggered.connect(main_window.save_file)
        self.setShortcut("Ctrl+S")

class AutoSaveAction(QAction):
    def __init__(self, main_window):
        super().__init__(QIcon("icons/clock-arrow.png"), "Toggle AutoSave", main_window)
        self.setStatusTip("Toggle automatic saving")
        self.triggered.connect(main_window.toggle_autosave)
        self.setShortcut("Ctrl+Shift+A")
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

        # Initialize autosave
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_interval = 500  # 1 second in milliseconds
        self.autosave_enabled = False
        self.autosave_action = None  # We'll set this in create_toolbar

    def open_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Markdown Files (*.md);;All Files (*)")

        if file_path:
            file = QFile(file_path)
            if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
                stream = QTextStream(file)
                self.markdown_editor.editor.setPlainText(stream.readAll())
                file.close()
                self.current_file = file_path
                self.setWindowTitle(f"Markdown Editor - {os.path.basename(file_path)}")

    def save_file(self):
        if not hasattr(self, 'current_file'):
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Markdown Files (*.md);;All Files (*)")
            if not file_path:
                return  # User cancelled the save dialog
            self.current_file = file_path

        with open(self.current_file, 'w', encoding='utf-8') as file:
            file.write(self.markdown_editor.editor.toPlainText())

        self.setWindowTitle(f"Markdown Editor - {os.path.basename(self.current_file)}")

    def toggle_autosave(self):
        self.autosave_enabled = not self.autosave_enabled
        if self.autosave_enabled:
            self.autosave_timer.start(self.autosave_interval)
        else:
            self.autosave_timer.stop()
        
        # Update the AutoSave action state
        if self.autosave_action:
            self.autosave_action.setChecked(self.autosave_enabled)

    def autosave(self):
        if hasattr(self, 'current_file'):
            self.save_file()
        else:
            print("No file to autosave")  # You might want to handle this case differently

    def create_toolbar(self):
        # Create a Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))

        actions = {
            "file": {
                "open": OpenAction(self),
                "save": SaveAction(self),
            },
            "edit": {
                "autosave": AutoSaveAction(self),
            },
            "view": {
                "darkmode": DarkModeAction(self),
                "preview": PreviewAction(self.markdown_editor),
                "overlay": OverlayPreviewAction(self.markdown_editor),
            },
        }

        # Add File actions to toolbar
        for action in actions["file"].values():
            toolbar.addAction(action)

        # Add a separator
        toolbar.addSeparator()

        # Add View actions to toolbar
        for action in actions["view"].values():
            toolbar.addAction(action)

        # Fill the Toolbar
        self.addToolBar(toolbar)

        # Add a Menu
        menu = self.menuBar()
        if menu:
            file_menu = menu.addMenu("File")
            for action in actions["file"].values():
                file_menu.addAction(action)
            edit_menu = menu.addMenu("Edit")
            for action in actions["edit"].values():
                edit_menu.addAction(action)
            view_menu = menu.addMenu("View")
            for action in actions["view"].values():
                view_menu.addAction(action)

        # Store the AutoSave action for later use
        self.autosave_action = actions["edit"]["autosave"]

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
        self.markdown_editor.editor.set_dark_mode(is_dark)
        self.markdown_editor.update_preview()

    def setup_shortcuts(self):
        # Toggle Preview shortcut
        toggle_preview_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        toggle_preview_shortcut.activated.connect(self.markdown_editor.toggle_preview)

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
    parser.add_argument(
        "input_file", nargs="?", help="Path to the markdown file to open"
    )
    parser.add_argument(
        "--autosave", action="store_true", help="Start with autosave enabled"
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = MainWindow()

    if args.input_file:
        window.open_file(args.input_file)

    if args.autosave:
        window.toggle_autosave()

    window.show()
    sys.exit(app.exec())


# Footnotes
# [^1]: https://facelessuser.github.io/pymdown-extensions/extensions/blocks/plugins/details/
# [^2]: https://github.com/mkdocs/mkdocs/issues/282
