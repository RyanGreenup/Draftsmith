import os
from fts import FTS
from markdown_utils import set_web_security_policies
from utils import popup_notification
from pathlib import Path
from PyQt6.QtWebEngineCore import QWebEngineSettings
from fuzzywuzzy import fuzz
from PyQt6.QtGui import QAction
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QDialog,
    QLineEdit,
    QListWidget,
    QSplitter,
    QVBoxLayout,
    QListWidgetItem,
)
from PyQt6.QtCore import QUrl, Qt, QEvent

from markdown_utils import Markdown, WebEngineViewWithBaseUrl
import sys

from config import Config

config = Config()


class Palette(QDialog):
    def __init__(self, title="Palette", size=(400, 300), previewer=None):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(100, 100, *size)

        self.items = []  # Store all items (can be strings or tuples)
        self.filtered_items = []  # Store filtered items

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.main_layout.addWidget(self.search_bar)

        # List widget
        self.list_widget = QListWidget()

        # Preview
        self.preview = WebEngineViewWithBaseUrl()
        self.preview.hide()
        self.preview.setHtml("<b>Preview</b>")

        self.main_layout.addWidget(self.list_widget)

        # Connect search functionality
        self.search_bar.textChanged.connect(self.filter_items)
        self.list_widget.itemActivated.connect(self.execute_item)

        # Connect key press event
        self.search_bar.installEventFilter(self)

        # Set a Fixed Size
        self.setFixedSize(*size)

        # Check if it's been populated
        self.populated = False

    def populate_items(self):
        raise NotImplementedError("Subclasses must implement populate_items method")

    def clear_items(self):
        self.list_widget.clear()
        self.populated = False

    def repopulate_items(self):
        self.clear_items()
        self.populate_items()

    def highlight_first_item(self):
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def execute_item(self, item):
        raise NotImplementedError("Subclasses must implement execute_item method")

    def open(self, refresh: bool = False):
        self.show()
        self.search_bar.setFocus()
        self.search_bar.clear()
        if not self.populated:
            self.populate_items()
            self.populated = True
        if refresh:
            self.repopulate_items()

    def _update_list_widget(self):
        self.list_widget.clear()
        for item in self.filtered_items:
            list_item = QListWidgetItem(self.get_display_text(item))
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.list_widget.addItem(list_item)

    def _filter_items(self, text, fuzzy=False):
        if fuzzy:
            if not text:
                self.filtered_items = self.items.copy()
            else:
                displays = [self.get_display_text(item).lower() for item in self.items]
                self.filtered_items = fzy_sort(self.items, displays, text.lower())
        else:
            self.filtered_items = [
                item
                for item in self.items
                if text.lower() in self.get_display_text(item).lower()
            ]

        self._update_list_widget()
        self.highlight_first_item()

    def filter_items(self, text):
        self._filter_items(text)

    def get_display_text(self, item):
        # To be overridden by subclasses if necessary
        return str(item)

    def eventFilter(self, obj, event):
        if obj == self.search_bar and event.type() == QEvent.Type.KeyPress:
            direction_keys = DirectionKeys(event)

            if direction_keys.up():
                self.move_selection(-1)
                return True
            elif direction_keys.down():
                self.move_selection(1)
                return True
            elif direction_keys.select():
                current_item = self.list_widget.currentItem()
                if current_item:
                    self.execute_item(current_item)
                return True
        return super().eventFilter(obj, event)

    def move_selection(self, direction):
        current_row = self.list_widget.currentRow()
        total_items = self.list_widget.count()

        for i in range(1, total_items):
            next_row = (current_row + direction * i) % total_items
            item = self.list_widget.item(next_row)
            if not item.isHidden():
                self.list_widget.setCurrentItem(item)
                self.list_widget.scrollToItem(item)
                break


class DirectionKeys:
    def __init__(self, event):
        self.key = event.key()
        self.modifiers = event.modifiers()

    def up(self) -> bool:
        return self.key == Qt.Key.Key_Up or (
            self.key == Qt.Key.Key_P
            and self.modifiers == Qt.KeyboardModifier.ControlModifier
        )

    def down(self) -> bool:
        return self.key == Qt.Key.Key_Down or (
            self.key == Qt.Key.Key_N
            and self.modifiers == Qt.KeyboardModifier.ControlModifier
        )

    def select(self) -> bool:
        return self.key == Qt.Key.Key_Enter or self.key == Qt.Key.Key_Return


class CommandPalette(Palette):
    def __init__(self, actions):
        super().__init__(title="Command Palette")
        self.actions = actions

    def populate_items(self):
        # Set Monospace font
        font = self.list_widget.font()
        font.setFamily("Fira Code")  # TODO config Option
        self.list_widget.setFont(font)

        # Set Margins
        self.list_widget.setContentsMargins(10, 10, 10, 10)

        # Measure Alignment of shortcut and action
        max_length = min(max(len(action.text()) for action in self.actions), 60)

        self.items.clear()
        self.items = [(action, max_length) for action in self.actions]
        self.filtered_items = self.items.copy()
        self._update_list_widget()

        # Highlight the first item
        self.highlight_first_item()

    def get_display_text(self, item):
        action, max_length = item
        return f"{action.text().replace('&', ''):<{max_length}}     ({action.shortcut().toString()})"

    def execute_item(self, item):
        action, _ = item.data(Qt.ItemDataRole.UserRole)
        if action:
            action.trigger()  # Execute the action
        self.close()


# TODO allow a palette for navigating directories
# NOTE open directory should display a tree
class OpenDirectoryPalette(Palette):
    def __init__(self, main_window):
        pass


class OpenFilePalette(Palette):
    def __init__(self, main_window):
        super().__init__(title="Open File")
        self.main_window = main_window
        # Adjust fixed size
        # TODO candidate for config
        self.setFixedSize(1600, 1000)

        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.list_widget)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([300, 300])

        self.main_layout.addWidget(self.splitter)
        self.list_widget.currentItemChanged.connect(self.preview_item)

    def filter_items(self, text):
        self._filter_items(text, fuzzy=True)

    def preview_item(self, item):
        try:
            item_data = item.data(Qt.ItemDataRole.UserRole)
        except AttributeError:
            item_data = None
        except Exception as e:
            print(e, file=sys.stderr)
            item_data = None
        if item_data:
            try:
                with open(item_data, "r") as file:
                    self.set_preview(file.read(), item_data)
            except Exception as e:
                print(e, file=sys.stderr)
                self.preview.setHtml("<b>Error reading file</b>")

    def set_preview(self, content, item_data):
        if self.main_window.allow_remote_content:
            set_web_security_policies(self.preview)

        self.markdown_content = Markdown(
            text=content,
            css_path=self.main_window.css_path,
            # Use the main window's dark mode state
            dark_mode=self.main_window.dark_mode,
        )

        # Set Base Path so Images are loaded correctly
        # NOTE, base_path ==> requires remote access on preview for remote katex
        self.preview.setHtml(
            self.markdown_content.build_html(local_katex=self.main_window.local_katex)
        )

        self.preview.show()

    def populate_items(self):
        self.items.clear()
        current_dir = os.getcwd()
        for root, dirs, files in os.walk(current_dir):
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, current_dir)
                    self.items.append(relative_path)
        self.filtered_items = self.items.copy()
        self._update_list_widget()

    def execute_item(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.main_window.open_file(file_path)
        self.close()


class InsertLinkPalette(OpenFilePalette):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setWindowTitle("Insert Link")

    def execute_item(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            use_wikilink = config.config.get("insert_wikilinks")
            path_components = file_path.split(os.path.sep)
            if len(path_components) > 1:
                # wikilinks with / are not supported and using fallback
                # md link for now
                use_wikilink = False
                popup_notification(
                    "Wikilinks with `/` are not supported. Using fallback markdown link."
                ).show_timeout()
            if use_wikilink:
                file_path = file_path.replace(".md", "")
                self.main_window.insert_text(f"[[{file_path}]]")
            else:
                self.main_window.insert_text(f"[{file_path}]({file_path})")
        self.close()


class SearchFilePalette(OpenFilePalette):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setWindowTitle("Insert Link")

    def filter_items(self, text):
        fts = FTS()
        current_dir = os.getcwd()
        with FTS([".md"], current_dir) as fts:
            self.filtered_items = fts.search(text)

        self._update_list_widget()
        self.highlight_first_item()


def fzy_dist(s1: str, s2: str) -> float:
    return fuzz.ratio(s1, s2)


def fzy_sort(values: list[str], displays: list[str], text: str) -> list[str] | None:
    """
    Sort a list of strings, given a term using Levenshtein distance.
    """
    if not values:
        return None

    def sort_func(x):
        return fzy_dist(x[0], text)

    sorted_values = sorted(zip(values, displays), key=sort_func, reverse=True)
    sorted_values = [value for value, _ in sorted_values]
    return sorted_values
