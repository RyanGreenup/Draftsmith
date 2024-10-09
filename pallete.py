import os
from pathlib import Path
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QDialog,
    QLineEdit,
    QListWidget,
    QVBoxLayout,
    QListWidgetItem,
)
from PyQt6.QtCore import Qt, QEvent


class Palette(QDialog):
    def __init__(self, title="Palette", size=(400, 300)):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(100, 100, *size)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.layout.addWidget(self.search_bar)

        # List widget
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

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

    def filter_items(self, text):
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            item.setHidden(text.lower() not in item.text().lower())

        # Highlight the first visible item after filtering
        self.highlight_first_item()

    def highlight_first_item(self):
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            if not item.isHidden():
                self.list_widget.setCurrentItem(item)
                break

    def execute_item(self, item):
        raise NotImplementedError("Subclasses must implement execute_item method")

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
        next_row = current_row + direction
        while 0 <= next_row < self.list_widget.count():
            item = self.list_widget.item(next_row)
            if not item.isHidden():
                self.list_widget.setCurrentItem(item)
                return
            next_row += direction

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
            lab = f"{action.text().replace('&', ''):<{max_length}}     ({action.shortcut().toString()})"
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


class OpenFilePalette(Palette):
    def __init__(self, main_window):
        super().__init__(title="Open File")
        self.main_window = main_window

    def populate_items(self):
        current_dir = os.getcwd()
        # Glob Directories
        files = Path(current_dir).rglob("*.md")
        files = [file.relative_to(current_dir) for file in files]
        files = [str(file) for file in files]

        # Add the Files
        for file in files:
            if os.path.isfile(file):
                item = QListWidgetItem(file)
                item.setData(Qt.ItemDataRole.UserRole, file)
                self.list_widget.addItem(item)

        # Highlight the first item
        self.highlight_first_item()

    def repopulate_items(self):
        self.clear_items()
        self.populate_items()

    def execute_item(self, item):
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.main_window.open_file(file_path)
        self.close()
