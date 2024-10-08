from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QDialog,
    QListWidget,
    QLineEdit,
    QVBoxLayout,
    QListWidgetItem,
    QAction,
)
import sys


class CommandPalette(QDialog):
    def __init__(self, actions):
        super().__init__()
        self.setWindowTitle("Command Palette")

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

    def populate_actions(self):
        for action in self.actions:
            item = QListWidgetItem(action.text())  # Use action text for display
            item.setData(1, action)  # Store the actual action in the item
            self.list_widget.addItem(item)

    def filter_actions(self, text):
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            item.setHidden(text.lower() not in item.text().lower())

    def execute_action(self, item):
        action = item.data(1)
        if action:
            action.trigger()  # Execute the action
        self.close()
