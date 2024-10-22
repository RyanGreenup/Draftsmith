from enum import Enum
from fts import FTS
from utils import popup_notification
from editor_highlighting_regex import MarkdownHighlighter
import markdown
import os
from palette import (
    CommandPalette,
    InsertLinkPalette,
    OpenFilePalette,
    SearchFilePalette,
)
from typing import Callable
from PyQt6.QtWidgets import QTextEdit, QToolBar
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtGui import QAction, QIcon, QKeyEvent, QTextCursor, QKeySequence
from markdown_utils import Markdown, set_web_security_policies, WebEngineViewWithBaseUrl
from PyQt6.QtCore import QSize, QUrl, Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from vimkeys import VimTextEdit
from popup import MultiMathPopups
from pygments.formatters import HtmlFormatter
import markdown
from pathlib import Path
from config import Config  # Import Config class
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
    QLabel,
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

    overlay_toggled = pyqtSignal(bool)

    def __init__(
        self,
        config,
        css_dir=None,
        base_url=None,
        local_katex=True,
        allow_remote_content=True,
        open_file_callback=None,  # Add this parameter
    ):
        super().__init__()
        self.config = config
        self.css_dir = css_dir
        self.dark_mode = False
        self.preview_visible = True
        self.preview_overlay = False
        self.base_url = base_url or QUrl.fromLocalFile(
            os.path.join(os.getcwd() + os.path.sep)
        )
        self.local_katex = local_katex
        self.open_file_callback = open_file_callback  # Store the callback

        # Add this line to initialize current_file
        self.current_file = None

        self.setup_ui()

        # NOTE Must allow external content for remote content with a base_url set
        if allow_remote_content:
            set_web_security_policies(self.preview)

        self.math_popups = MultiMathPopups(self.editor)

    def get_layout_state(self):
        return {
            "preview_visible": self.preview_visible,
            "preview_overlay": self.preview_overlay,
        }

    def set_layout_state(self, state):
        self.preview_visible = state["preview_visible"]
        self.preview_overlay = state["preview_overlay"]
        self.update_layout()

    def update_layout(self):
        if self.preview_overlay:
            self.editor.hide()
            self.preview.show()
        else:
            self.editor.show()
            if self.preview_visible:
                self.preview.show()
                self.splitter.setSizes([300, 300])
            else:
                self.preview.hide()
                self.splitter.setSizes([600, 0])
        self.update_preview()

    def setup_ui(self):
        # Create the editor and preview widgets
        self.editor = VimTextEdit()
        self.preview = WebEngineViewWithBaseUrl()
        if self.config.config.get("no_side_by_side"):
            self.preview.hide()

        # Set up the custom page with the callback and base directory
        self.preview_page = PreviewPage(
            parent=self.preview,
            open_file_callback=self.open_file_callback,
            base_dir=self.base_url.toLocalFile(),
        )
        self.preview.setPage(self.preview_page)

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

        # Set initial content for the preview
        self.update_preview()

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
        if self.preview_overlay:
            self.editor.show()
            if self.preview_visible:
                self.preview.show()
        else:
            self.editor.hide()
            self.preview.show()
            self.update_preview()

        self.preview_overlay = not self.preview_overlay
        self.overlay_toggled.emit(self.preview_overlay)

    def update_preview(self):
        """Update the Markdown preview."""
        if self.preview_visible or self.preview_overlay:
            text = self.editor.toPlainText()
            markdown_content = Markdown(
                text=text, css_path=self.css_dir, dark_mode=self.dark_mode
            )
            html = markdown_content.build_html(local_katex=self.local_katex)
            self.preview.setHtml(html)

    def toggle_math_popups(self):
        self.math_popups.toggle()


class Icon(Enum):
    LINK = "icons/link.png"
    SEARCH = "icons/search.png"
    SEARCH_REMOVE = "icons/search-minus.png"
    PREVIEW = "icons/magnifier.png"
    OVERLAY = "icons/switch.png"
    NEW_TAB = "icons/plus-octagon.png"
    CLOSE_TAB = "icons/cross-octagon.png"
    OPEN = "icons/folder-open.png"
    OPEN_DIR = "./icons/drawer-open.png"
    SAVE = "icons/disk.png"
    REVERT = "icons/arrow-circle-315.png"
    AUTOSAVE = "icons/clock-moon-phase.png"
    AUTOREVERT = "icons/arrow-circle-315-frame.png"
    PREVIOUS_TAB = "icons/arrow-180.png"
    NEXT_TAB = "icons/arrow.png"
    DARK_MODE = "icons/light-bulb.png"
    PALETTE = "icons/keyboard.png"


class MainWindow(QMainWindow):
    """Main window containing the Markdown editor."""

    def __init__(self, css_path: Path, config: Config, remote_katex: bool = False, disable_remote_content: bool = False):
        super().__init__()
        self.config = config
        self.setWindowTitle("Markdown Editor with Preview")
        self.resize(800, 600)

        # Initialize dark_mode attribute
        self.dark_mode = False

        # Use args here
        self.css_path = css_path

        # Create a QTabWidget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Set local_katex and allow_remote_content options
        self.local_katex = not remote_katex
        self.allow_remote_content = not disable_remote_content

        # Create the first tab
        self.new_tab()

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

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.update_current_tab_actions)

    def open_new_window(self):
        new_window = MainWindow()
        new_window.show()

    def insert_text(self, text):
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            cursor = current_editor.editor.textCursor()
            cursor.insertText(text)
            current_editor.editor.setTextCursor(cursor)

    # TODO Remove this?
    def update_current_tab_actions(self):
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            self.overlay_preview_action.setChecked(current_editor.preview_overlay)

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
        base_url = QUrl.fromLocalFile(os.path.join(os.getcwd() + os.path.sep))
        markdown_editor = MarkdownEditor(
            config=self.config,
            css_dir=self.css_path,
            base_url=base_url,
            local_katex=self.local_katex,
            allow_remote_content=self.allow_remote_content,
            open_file_callback=self.open_file,  # Pass the open_file method as a callback
        )

        # Add the new MarkdownEditor to a new tab
        tab_title = f"Untitled {self.tab_widget.count() + 1}"
        self.tab_widget.addTab(markdown_editor, tab_title)

        # Set the new tab as the current tab
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

    def open_file(self, file_path=None, focus_tab=True):
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

                # Store the current layout state
                layout_state = (
                    current_editor.get_layout_state() if current_editor else None
                )

                # If there's no current tab or the current tab is not empty, create a new tab
                if not current_editor or current_editor.editor.toPlainText().strip():
                    self.new_tab()
                    current_editor = self.tab_widget.currentWidget()

                current_editor.editor.setPlainText(content)
                current_editor.current_file = file_path

                # Apply the stored layout state
                if layout_state:
                    current_editor.set_layout_state(layout_state)

                # Update the tab text and window title
                self.tab_widget.setTabText(
                    self.tab_widget.currentIndex(), os.path.basename(file_path)
                )
                self.setWindowTitle(f"Markdown Editor - {os.path.basename(file_path)}")

                if focus_tab:
                    self.tab_widget.setCurrentWidget(current_editor)

            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open file: {str(e)}")

    def open_multiple_files(self, file_paths):
        for file_path in file_paths:
            self.open_file(file_path)

    def set_directory(self, directory=None):
        if directory:
            os.chdir(directory)
        else:
            directory = QFileDialog.getExistingDirectory(self, "Select Directory")
            if directory:
                os.chdir(directory)

        # Update base_url for all tabs
        base_url = QUrl.fromLocalFile(os.path.join(os.getcwd() + os.path.sep))
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            editor.base_url = base_url
            editor.update_preview()

        self.files_palette.clear_items()

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
        current_editor = self.tab_widget.currentWidget()
        if current_editor and current_editor.current_file:
            self.open_file(current_editor.current_file, focus_tab=False)
        else:
            print("No file to autorevert")

    def save_file(self):
        current_editor = self.tab_widget.currentWidget()
        if not current_editor:
            return

        if not current_editor.current_file:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save File", "", "Markdown Files (*.md);;All Files (*)"
            )
            if not file_path:
                return  # User cancelled the save dialog
            current_editor.current_file = file_path

        with open(current_editor.current_file, "w", encoding="utf-8") as file:
            file.write(current_editor.editor.toPlainText())

        self.tab_widget.setTabText(
            self.tab_widget.currentIndex(),
            os.path.basename(current_editor.current_file),
        )
        self.setWindowTitle(
            f"Markdown Editor - {os.path.basename(current_editor.current_file)}"
        )

    def revert_to_disk(self):
        current_editor = self.tab_widget.currentWidget()
        if current_editor and current_editor.current_file:
            reply = QMessageBox.question(
                self,
                "Revert to Disk",
                "Are you sure you want to revert to the saved version? All unsaved changes will be lost.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.open_file(current_editor.current_file, focus_tab=False)
        else:
            QMessageBox.warning(self, "Revert to Disk", "No file is currently open.")

    def toggle_autosave(self):
        self.autosave_enabled = not self.autosave_enabled
        if self.autosave_enabled:
            self.autosave_timer.start(self.autosave_interval)
            popup_notification("Autosave enabled").show_timeout()

        else:
            self.autosave_timer.stop()
            popup_notification("Autosave Disabled").show_timeout()

        # Update the AutoSave action state
        if self.autosave_action:
            self.autosave_action.setChecked(self.autosave_enabled)

    def autosave(self):
        current_editor = self.tab_widget.currentWidget()
        if current_editor and current_editor.current_file:
            self.save_file()
        else:
            print("No file to autosave")

    def reset_search_index(self):
        current_dir = os.getcwd()
        with FTS([".md"], current_dir) as fts:
            fts.remove_database()

    def index_current_dir(self):
        current_dir = os.getcwd()
        with FTS([".md"], current_dir) as fts:
            fts.index_current_dir()

    def create_toolbar(self):
        # Create a Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))

        def toggle_overlay_preview():
            current_editor = self.tab_widget.currentWidget()
            if current_editor:
                current_editor.toggle_preview_overlay()

        def toggle_preview():
            current_editor = self.tab_widget.currentWidget()
            if current_editor:
                current_editor.toggle_preview()

        menu_dict = {
            "File": {
                "new_window": self.build_action(
                    Icon.NEW_TAB.value,
                    "New Window",
                    "Open a new window",
                    self.open_new_window,
                    "Ctrl+Shift+N",
                ),
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
                "Set Directory": self.build_action(
                    Icon.OPEN_DIR.value,
                    "Set Directory",
                    "Set the current directory",
                    self.set_directory,
                    "Ctrl+Shift+O",
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
                "Insert Link": self.build_action(
                    Icon.LINK.value,
                    "Insert Link",
                    "Insert a link",
                    self.open_link_palette,
                    "Ctrl+K",
                ),
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
            "Search": {
                "Index Current Directory": self.build_action(
                    Icon.SEARCH.value,
                    "Index Current Directory",
                    "Index all files in the current directory",
                    self.index_current_dir,
                    "Ctrl+I",
                ),
                "Reset Search Index": self.build_action(
                    Icon.SEARCH_REMOVE.value,
                    "Reset Search Index",
                    "Reset the search index",
                    self.reset_search_index,
                    "Ctrl+Shift+I",
                ),
                "Search": self.build_action(
                    Icon.SEARCH.value,
                    "Search",
                    "Search the indexed files",
                    self.open_search_palette,
                    "Ctrl+F",
                ),
            },
            "View": {
                "darkmode": self.build_action(
                    Icon.DARK_MODE.value,
                    "Dark Mode (Toggle)",
                    "Toggle Dark Mode",
                    self.toggle_app_dark_mode,
                    "Ctrl+D",
                    True,
                ),
                "preview": self.build_action(
                    Icon.OVERLAY.value,
                    "Toggle Preview",
                    "Hide Preview",
                    toggle_preview,
                    "Ctrl+G",
                ),
                "overlay": self.build_action(
                    Icon.PREVIEW.value,
                    "Overlay Preview",
                    "Replace Editor with Preview",
                    toggle_overlay_preview,
                    "Ctrl+E",
                ),
                "Open Command Pallete": self.build_action(
                    Icon.PALETTE.value,
                    "Command Palette",
                    "Open the command palette",
                    self.open_command_palette,
                    "Ctrl+Shift+P",
                ),
                "Files Pallete": self.build_action(
                    Icon.PALETTE.value,
                    "Files Palette",
                    "Open the Files palette",
                    self.open_files_palette,
                    "Ctrl+P",
                ),
                "Toggle Math Popups": self.build_action(
                    Icon.PREVIEW.value,  # You may want to use a different icon
                    "Toggle Math Popups",
                    "Toggle display of multiple math popups",
                    self.toggle_math_popups,
                    "Ctrl+M",
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
        # Store the AutoSave, AutoRevert, and Overlay Preview actions for later use
        self.autosave_action = menu_dict["Edit"]["autosave"]
        self.autorevert_action = menu_dict["Edit"]["autorevert"]
        self.overlay_preview_action = menu_dict["View"]["overlay"]

        # Fill the Toolbar with actions
        # Flatten dictionary structure
        self.fill_toolbar(
            [
                menu_dict["File"]["new_window"],
                menu_dict["File"]["new_tab"],
                menu_dict["File"]["close_tab"],
                "sep",
                menu_dict["File"]["open"],
                menu_dict["File"]["save"],
                "sep",
                menu_dict["File"]["revert"],
                menu_dict["Edit"]["autosave"],
                "sep",
                menu_dict["View"]["darkmode"],
                "sep",
                menu_dict["View"]["Tabs"]["previous_tab"],
                menu_dict["View"]["Tabs"]["next_tab"],
                "sep",
                menu_dict["View"]["preview"],
                menu_dict["View"]["overlay"],
            ]
        )

        main_menu = self.menuBar()

        self.create_menus_from_structure(menu_dict, main_menu)

        # Collect actions from the menu structure
        self.actions = self.collect_actions_from_menu(menu_dict)

        # Palettes
        # Create command palette
        self.command_palette = CommandPalette(self.actions)
        self.link_palette = InsertLinkPalette(self)
        self.files_palette = OpenFilePalette(self)
        self.search_palette = SearchFilePalette(self)

    def collect_actions_from_menu(self, menu_dict):
        actions = []
        for value in menu_dict.values():
            if isinstance(value, dict):
                if "action" in value:
                    actions.append(value["action"])
                else:
                    actions.extend(self.collect_actions_from_menu(value))
        return actions

    def build_action(
        self,
        icon: str,
        name: str,
        description: str,
        callback: Callable,
        shortcut_key: str | None,
        checkable: bool = False,
    ) -> QAction:
        name = "&" + name  # Add an accelerator key (i.e. a Mnemonic)
        action = QAction(QIcon(icon), name, self)
        action.setStatusTip(description)
        action.triggered.connect(callback)
        action.setCheckable(checkable)
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
            menu_title = "&" + menu_title  # Add an accelerator key (i.e. a Mnemonic)
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
            app.setPalette(get_dark_palette())
        else:
            app.setPalette(app.style().standardPalette())

        # Update the dark_mode attribute
        self.dark_mode = is_dark

        # Update the markdown editor's dark mode for all tabs
        for i in range(self.tab_widget.count()):
            markdown_editor = self.tab_widget.widget(i)
            markdown_editor.dark_mode = is_dark
            markdown_editor.editor.set_dark_mode(is_dark)
            markdown_editor.update_preview()

    def open_command_palette(self):
        self.command_palette.open()

    def open_search_palette(self):
        self.search_palette.open()

    def open_link_palette(self):
        self.link_palette.open()

    def open_files_palette(self):
        self.files_palette.open()

    def toggle_math_popups(self):
        current_editor = self.tab_widget.currentWidget()
        if current_editor:
            current_editor.toggle_math_popups()

    def collect_actions_from_menu(self, menu_dict):
        actions = []
        for value in menu_dict.values():
            if isinstance(value, dict):
                actions.extend(self.collect_actions_from_menu(value))
            elif isinstance(value, QAction):
                actions.append(value)
        return actions


class PreviewPage(QWebEnginePage):
    def __init__(self, parent=None, open_file_callback=None, base_dir=None):
        super().__init__(parent)
        self.open_file_callback = open_file_callback
        self.base_dir = base_dir or os.getcwd()

    def acceptNavigationRequest(self, url, type, isMainFrame):
        if type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            href = url.toString()
            # Convert relative URLs to absolute paths
            if not url.isLocalFile():
                href = os.path.abspath(os.path.join(self.base_dir, href))
            else:
                href = url.toLocalFile()
            if href and os.path.isfile(href):
                if self.open_file_callback:
                    self.open_file_callback(href, focus_tab=True)
                return False  # Prevent the webview from navigating to the link
        return super().acceptNavigationRequest(url, type, isMainFrame)

def main():
    # Initialize configuration
    config = Config()

    # Argument Parser
    parser = argparse.ArgumentParser(description="Markdown Editor with Preview")
    parser.add_argument(
        "--dir",
        type=str,
        default=config.config.get("directory", None),
        help="Directory to Set as the Current Directory",
    )
    parser.add_argument(
        "--css",
        type=str,
        default=config.config.get("css_path", None),
        help=(
            "Path to a directory containing css files for the markdown preview"
            "CSS files are applied alphabetically"
        ),
    )
    parser.add_argument(
        "--remote-katex",
        action="store_true",
        default=config.config.get("remote_katex", True),
        help="Use Remote KaTeX CDN instead of local KaTeX",
    )
    parser.add_argument(
        "--disable-remote-content",
        action="store_true",
        default=config.config.get("disable_remote_content", False),
        help="Disable Remote Content in the Preview",
    )
    parser.add_argument(
        "input_files", nargs="*", help="Paths to the markdown files to open"
    )
    parser.add_argument(
        "--autosave", action="store_true", help="Start with autosave enabled"
    )
    args = parser.parse_args()

    # Ensure CSS path is resolved
    if args.css:
        args.css = Path(args.css).resolve()
    else:
        args.css = Path(config.config.get("css_path")).resolve()

    app = QApplication(sys.argv)
    window = MainWindow(args.css,  config, args.remote_katex, args.disable_remote_content)

    if args.input_files:
        window.open_multiple_files(args.input_files)

    if args.autosave:
        window.toggle_autosave()

    if args.dir:
        window.set_directory(args.dir)

    app.setStyle("Fusion")
    window.show()
    sys.exit(app.exec())



if __name__ == "__main__":
    main()
# Footnotes
# [^1]: https://facelessuser.github.io/pymdown-extensions/extensions/blocks/plugins/details/
# [^2]: https://github.com/mkdocs/mkdocs/issues/282


# Footnotes
# [^1]: https://facelessuser.github.io/pymdown-extensions/extensions/blocks/plugins/details/


# Footnotes
# [^1]: https://facelessuser.github.io/pymdown-extensions/extensions/blocks/plugins/details/
