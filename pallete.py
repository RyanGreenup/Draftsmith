import os
from pathlib import Path
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
from PyQt6.QtCore import Qt, QEvent

from markdown_utils import Markdown
import sys

# TODO Autoselect on Command Palette


class Palette(QDialog):
    def __init__(self, title="Palette", size=(400, 300), previewer=None):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(100, 100, *size)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.main_layout.addWidget(self.search_bar)

        # List widget
        self.list_widget = QListWidget()

        # Preview
        self.preview = QWebEngineView()
        self.preview.setHtml("")

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
        # Get the Maximum Length of the Action Text
        m = max(len(action.text()) for action in self.actions)
        # Upper Bound of 60 char
        max_length = min(m, 60)

        # Add the Actions
        for action in self.actions:
            lab = f"{action.text().replace('&', ''):<{max_length}
                     }     ({action.shortcut().toString()})"
            item = QListWidgetItem(lab)  # Use action text for display
            item.setData(
                Qt.ItemDataRole.UserRole, action
            )  # Store the actual action in the item
            self.list_widget.addItem(item)

        # Highlight the first item
        self.highlight_first_item()

    def execute_item(self, item):
        action = item.data(Qt.ItemDataRole.UserRole)
        if action:
            action.trigger()  # Execute the action
        self.close()

    def filter_items(self, text):
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            item.setHidden(text.lower() not in item.text().lower())

        self.highlight_first_item()

    def eventFilter(self, obj, event):
        if obj == self.search_bar and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Up:
                self.move_selection(-1)
                return True
            elif key == Qt.Key.Key_Down:
                self.move_selection(1)
                return True
            elif key == Qt.Key.Key_Enter or key == Qt.Key.Key_Return:
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


# TODO allow a pallete for navigating directories
# NOTE open directory should display a tree
class OpenDirectoryPalette(Palette):
    def __init__(self, main_window):
        pass


class OpenFilePalette(Palette):
    def __init__(self, main_window):
        super().__init__(title="Open File")
        self.main_window = main_window
        self.all_files = []  # Store all files
        self.filtered_files = []  # Store filtered files
        # Adjust fixed size
        # TODO candidate for config
        self.setFixedSize(1600, 1000)

        # Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.list_widget)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([300, 300])
        self.preview.show()

        self.main_layout.addWidget(self.splitter)
        self.list_widget.currentItemChanged.connect(self.preview_item)

    def preview_item(self, item):
        try:
            item_data = item.data(Qt.ItemDataRole.UserRole)
        except AttributeError:
            item_data = None
        except Exception as e:
            print(e, file=sys.stderr)
            item_data = None
        if item_data:
            with open(item.data(Qt.ItemDataRole.UserRole), "r") as file:
                content = file.read()
            self.markdown_content = Markdown(
                text=content,
                css_path=self.main_window.css_path,
                # TODO dark mode
                dark_mode=False,
            )
            self.preview.setHtml(self.markdown_content.build_html())

    def populate_items(self):
        self.list_widget.clear()
        self.all_files.clear()
        self.filtered_files.clear()

        current_dir = os.getcwd()
        for root, dirs, files in os.walk(current_dir):
            for file in files:
                if file.endswith(".md"):  # Only include Markdown files
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, current_dir)
                    self.all_files.append((relative_path, full_path))

        self.filtered_files = self.all_files.copy()
        self._update_list_widget()

    def _update_list_widget(self):
        self.list_widget.clear()
        for relative_path, full_path in self.filtered_files:
            item = QListWidgetItem(relative_path)
            item.setData(Qt.ItemDataRole.UserRole, full_path)
            self.list_widget.addItem(item)

    def filter_items(self, text):
        self.filtered_files = [
            (relative_path, full_path)
            for relative_path, full_path in self.all_files
            if text.lower() in relative_path.lower()
        ]
        self._update_list_widget()
        self.highlight_first_item()

    def move_selection(self, direction):
        current_row = self.list_widget.currentRow()
        total_items = self.list_widget.count()
        if total_items == 0:
            return

        next_row = (current_row + direction) % total_items
        self.list_widget.setCurrentRow(next_row)
        self.list_widget.scrollToItem(self.list_widget.currentItem())

    def execute_item(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.main_window.open_file(file_path)
        self.close()

    def eventFilter(self, obj, event):
        if obj == self.search_bar and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Up:
                self.move_selection(-1)
                return True
            elif key == Qt.Key.Key_Down:
                self.move_selection(1)
                return True
            elif key == Qt.Key.Key_Enter or key == Qt.Key.Key_Return:
                current_item = self.list_widget.currentItem()
                if current_item:
                    self.execute_item(current_item)
                return True
        return super().eventFilter(obj, event)
