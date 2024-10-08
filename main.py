from enum import Enum
import os
from typing import Callable
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
    QMessageBox,
    QTabWidget,
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
    """A QWidget containing a Markdown editor with toggleable live preview.

    Slots:
        - Connect to an Action
            - toggle_preview: Toggle the Markdown preview.
            - toggle_preview_overlay: Toggle the Markdown preview overlay.
            - update_preview: Update the Markdown preview
        - General
            - update_preview: Update the Markdown preview
            - toggle_dark_mode: Toggle the dark mode of the Markdown preview.
              - Connect it to the app dark mode
    """

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
        self.main_layout.addWidget(self.splitter)
        self.setLayout(self.main_layout)

    def toggle_preview(self):
        self.preview_visible = not self.preview_visible
        if self.preview_visible:
            self.preview.show()
            self.splitter.setSizes([300, 300])
            self.update_preview()
        else:
            self.preview.hide()
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


class Icon(Enum):
    PREVIEW = "icons/magnifier.png"
    OVERLAY = "icons/switch.png"
    NEW_TAB = "icons/plus-octagon.png"
    CLOSE_TAB = "icons/cross-octagon.png"
    OPEN = "icons/folder-open.png"
    SAVE = "icons/disk.png"
    REVERT = "icons/arrow-circle-315.png"
    AUTOSAVE = "icons/clock-moon-phase.png"
    AUTOREVERT = "icons/arrow-circle-315-frame.png"
    PREVIOUS_TAB = "icons/arrow-180.png"
    NEXT_TAB = "icons/arrow.png"
    DARK_MODE = "icons/light-bulb.png"


class OverlayPreviewAction(QAction):
    def __init__(self, markdown_editor, parent):
        super().__init__(QIcon(Icon.OVERLAY.value), "Overlay Preview", markdown_editor)
        self.setStatusTip("Replace Editor with Preview")
        self.triggered.connect(markdown_editor.toggle_preview_overlay)
        self.setShortcut("Ctrl+E")
        self.setCheckable(True)



class MainWindow(QMainWindow):
    """Main window containing the Markdown editor."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown Editor with Preview")
        self.resize(800, 600)

        # Create a QTabWidget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Create the first tab
        self.new_tab()

        # Initialize the dark mode button
        self.dark_mode_button = DarkModeButton()

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

        # Initialize autorevert
        self.autorevert_timer = QTimer(self)
        self.autorevert_timer.timeout.connect(self.autorevert)
        self.autorevert_enabled = False
        self.autorevert_action = None  # We'll set this in create_toolbar

    def previous_tab(self):
        current_index = self.tab_widget.currentIndex()
        if current_index > 0:
            self.tab_widget.setCurrentIndex(current_index - 1)
        else:
            self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

    def next_tab(self):
        current_index = self.tab_widget.currentIndex()
        if current_index < self.tab_widget.count() - 1:
            self.tab_widget.setCurrentIndex(current_index + 1)
        else:
            self.tab_widget.setCurrentIndex(0)

    def close_tab(self):
        current_tab = self.tab_widget.currentWidget()
        if current_tab:
            self.tab_widget.removeTab(self.tab_widget.currentIndex())
            current_tab.deleteLater()

    def new_tab(self):
        # Create a new MarkdownEditor
        markdown_editor = MarkdownEditor(css_file=args.css)

        # Add the new MarkdownEditor to a new tab
        tab_title = f"Untitled {self.tab_widget.count() + 1}"
        self.tab_widget.addTab(markdown_editor, tab_title)

        # Set the new tab as the current tab
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

    def open_file(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open File", "", "Markdown Files (*.md);;All Files (*)"
            )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()

                # Get the current tab's MarkdownEditor
                current_editor = self.tab_widget.currentWidget()

                # If there's no current tab or the current tab is not empty, create a new tab
                if not current_editor or current_editor.editor.toPlainText().strip():
                    self.new_tab()
                    current_editor = self.tab_widget.currentWidget()

                current_editor.editor.setPlainText(content)
                self.tab_widget.setTabText(
                    self.tab_widget.currentIndex(), os.path.basename(file_path)
                )
                self.current_file = file_path
                self.setWindowTitle(f"Markdown Editor - {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open file: {str(e)}")

    def open_multiple_files(self, file_paths):
        for file_path in file_paths:
            self.open_file(file_path)

    def toggle_autorevert(self):
        self.autorevert_enabled = not self.autorevert_enabled
        if self.autorevert_enabled:
            self.autorevert_timer.start(self.autosave_interval)
        else:
            self.autorevert_timer.stop()

        # Update the AutoRevert action state
        if self.autorevert_action:
            self.autorevert_action.setChecked(self.autorevert_enabled)

    def autorevert(self):
        if hasattr(self, "current_file"):
            self.open_file(self.current_file)
        else:
            print(
                "No file to autorevert"
            )  # You might want to handle this case differently

    def save_file(self):
        current_editor = self.tab_widget.currentWidget()
        if not current_editor:
            return

        if not hasattr(self, "current_file"):
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save File", "", "Markdown Files (*.md);;All Files (*)"
            )
            if not file_path:
                return  # User cancelled the save dialog
            self.current_file = file_path

        with open(self.current_file, "w", encoding="utf-8") as file:
            file.write(current_editor.editor.toPlainText())

        self.tab_widget.setTabText(
            self.tab_widget.currentIndex(), os.path.basename(self.current_file)
        )
        self.setWindowTitle(f"Markdown Editor - {os.path.basename(self.current_file)}")

    def revert_to_disk(self):
        if hasattr(self, "current_file"):
            reply = QMessageBox.question(
                self,
                "Revert to Disk",
                "Are you sure you want to revert to the saved version? All unsaved changes will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.open_file(self.current_file)
        else:
            QMessageBox.warning(self, "Revert to Disk", "No file is currently open.")

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
        if hasattr(self, "current_file"):
            self.save_file()
        else:
            print(
                "No file to autosave"
            )  # You might want to handle this case differently

    def create_toolbar(self):
        # Create a Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))

        actions = {
            "File": {
                "new_tab": self.build_action(
                    Icon.NEW_TAB.value,
                    "New Tab",
                    "Open a new tab",
                    self.new_tab,
                    "Ctrl+T",
                ),
                "close_tab": self.build_action(
                    Icon.CLOSE_TAB.value,
                    "Close Tab",
                    "Close the current tab",
                    self.close_tab,
                    "Ctrl+W",
                ),
                "open": self.build_action(
                    Icon.OPEN.value,
                    "Open",
                    "Open a markdown file",
                    lambda: self.open_file(None),
                    "Ctrl+O",
                ),
                "save": self.build_action(
                    Icon.SAVE.value,
                    "Save",
                    "Save the current file",
                    self.save_file,
                    "Ctrl+S",
                ),
                "revert": self.build_action(
                    Icon.REVERT.value,
                    "Revert to Disk",
                    "Reload the current file from disk",
                    self.revert_to_disk,
                    "Ctrl+R",
                ),
            },
            "Edit": {
                "autosave": self.build_action(
                    Icon.AUTOSAVE.value,
                    "Toggle AutoSave",
                    "Toggle automatic saving",
                    self.toggle_autosave,
                    "Ctrl+Shift+A",
                ),
                "autorevert": self.build_action(
                    Icon.AUTOREVERT.value,
                    "Toggle AutoRevert",
                    "Toggle automatic reloading from disk",
                    self.toggle_autorevert,
                    "Ctrl+Shift+R",
                ),
            },
            "View": {
                "darkmode": self.build_action(
                    Icon.DARK_MODE.value,
                    "Dark Mode",
                    "Toggle Dark Mode",
                    self.toggle_app_dark_mode,
                    "Alt+D",
                ),
                "preview": PreviewAction(
                    self.tab_widget.currentWidget()
                    if self.tab_widget.count() > 0
                    else None
                ),
                "overlay": OverlayPreviewAction(
                    self.tab_widget.currentWidget()
                    if self.tab_widget.count() > 0
                    else None
                ),
                "Tabs": {
                    "previous_tab": self.build_action(
                        Icon.PREVIOUS_TAB.value,
                        "Previous Tab",
                        "Switch to the previous tab",
                        self.previous_tab,
                        "Ctrl+[",
                    ),
                    "next_tab": self.build_action(
                        Icon.NEXT_TAB.value,
                        "Next Tab",
                        "Switch to the next tab",
                        self.next_tab,
                        "Ctrl+]",
                    ),
                },
            },
        }
        # Store the AutoSave and AutoRevert actions for later use
        self.autosave_action = actions["Edit"]["autosave"]
        self.autorevert_action = actions["Edit"]["autorevert"]

        # Fill the Toolbar with actions
        # Flatten dictionary structure
        self.fill_toolbar(
            [
                actions["File"]["new_tab"],
                actions["File"]["close_tab"],
                "sep",
                actions["File"]["open"],
                actions["File"]["save"],
                "sep",
                actions["File"]["revert"],
                actions["Edit"]["autosave"],
                "sep",
                actions["View"]["darkmode"],
                "sep",
                actions["View"]["Tabs"]["previous_tab"],
                actions["View"]["Tabs"]["next_tab"],
                "sep",
                actions["View"]["preview"],
                actions["View"]["overlay"],
            ]
        )

        main_menu = self.menuBar()
        self.create_menus_from_structure(actions, main_menu)

    def build_action(
        self,
        icon: str,
        name: str,
        description: str,
        callback: Callable,
        shortcut_key: str | None,
    ) -> QAction:
        name = "&" + name  # Add an accelerator key (i.e. a Mnemonic)
        action = QAction(QIcon(icon), name, self)
        action.setStatusTip(description)
        action.triggered.connect(callback)
        if shortcut_key:
            action.setShortcut(shortcut_key)
        return action

    def fill_toolbar(self, actions):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))

        for action in actions:
            if isinstance(action, QAction):
                toolbar.addAction(action)
            else:
                if isinstance(action, str):
                    if action == "sep":
                        toolbar.addSeparator()

        self.addToolBar(toolbar)

    def create_menus_from_structure(self, menu_structure, parent_menu=None):
        if parent_menu is None:
            parent_menu = (
                self.menuBar()
            )  # Start from the menu bar if no parent menu is provided

        for menu_title, submenu_or_action in menu_structure.items():
            menu_title = "&"+menu_title  # Add an accelerator key (i.e. a Mnemonic)
            if isinstance(submenu_or_action, dict):
                # Create a new submenu
                sub_menu = parent_menu.addMenu(menu_title)
                # Recursively create submenus and actions
                self.create_menus_from_structure(submenu_or_action, sub_menu)
            elif isinstance(submenu_or_action, QAction):
                # Add action to the current menu
                parent_menu.addAction(submenu_or_action)
            else:
                # Handle incorrect types
                print(
                    f"Warning: Unsupported menu structure item type {type(submenu_or_action)}"
                )

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

        # Update the markdown editor's dark mode for all tabs
        for i in range(self.tab_widget.count()):
            markdown_editor = self.tab_widget.widget(i)
            markdown_editor.dark_mode = is_dark
            markdown_editor.editor.set_dark_mode(is_dark)
            markdown_editor.update_preview()

    def setup_shortcuts(self):
        # Toggle Preview shortcut
        toggle_preview_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        toggle_preview_shortcut.activated.connect(self.toggle_preview)

        # Toggle Dark Mode shortcut
        toggle_dark_mode_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        toggle_dark_mode_shortcut.activated.connect(
            self.dark_mode_button.toggle_dark_mode
        )

    def toggle_preview(self):
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            current_editor.toggle_preview()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Markdown Editor with Preview")
    parser.add_argument(
        "--css", type=str, help="Path to a CSS file for the markdown preview"
    )
    parser.add_argument(
        "input_files", nargs="*", help="Paths to the markdown files to open"
    )
    parser.add_argument(
        "--autosave", action="store_true", help="Start with autosave enabled"
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = MainWindow()

    if args.input_files:
        window.open_multiple_files(args.input_files)

    if args.autosave:
        window.toggle_autosave()

    window.show()
    sys.exit(app.exec())

# Footnotes
# [^1]: https://facelessuser.github.io/pymdown-extensions/extensions/blocks/plugins/details/
# [^2]: https://github.com/mkdocs/mkdocs/issues/282
