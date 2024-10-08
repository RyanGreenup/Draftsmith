from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QLineEdit,
    QListWidget,
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
    QListWidgetItem,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression, QFile, QTextStream, QTimer, QEvent
from PyQt6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QFont,
    QColor,
    QPalette,
    QKeyEvent,
    QShortcut,
)
import sys


class CommandPalette(QDialog):
    def __init__(self, actions):
        super().__init__()
        self.setWindowTitle("Command Palette")
        self.setGeometry(100, 100, 400, 300)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search actions...")
        self.layout.addWidget(self.search_bar)

        # List showing all actions
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        # Populate the list widget with actions
        self.actions = actions
        self.populate_actions()

        # Connect search functionality
        self.search_bar.textChanged.connect(self.filter_actions)
        self.list_widget.itemActivated.connect(self.execute_action)

        # Connect key press event
        self.search_bar.installEventFilter(self)

        # Set a Fixed Size
        self.setFixedSize(400, 300)

    def populate_actions(self):
        for action in self.actions:
            # Remove '&' from action text (& represents the shortcut key)
            action.setText(action.text().replace("&", ""))
            item = QListWidgetItem(action.text())  # Use action text for display
            item.setData(Qt.ItemDataRole.UserRole, action)  # Store the actual action in the item
            self.list_widget.addItem(item)

        # Highlight the first item
        self.highlight_first_item()

    def filter_actions(self, text):
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

    def execute_action(self, item):
        action = item.data(Qt.ItemDataRole.UserRole)
        if action:
            action.trigger()  # Execute the action
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
                    self.execute_action(current_item)
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
