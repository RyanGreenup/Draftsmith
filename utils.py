from config import Config
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QMessageBox
from typing import Optional


class popup_notification(QMessageBox):
    def __init__(self, message: str):
        super().__init__()
        self.setIcon(QMessageBox.Icon.Information)
        self.setText(message)
        self.setWindowTitle("Notification")
        self.setStandardButtons(QMessageBox.StandardButton.Ok)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

    def show(self):
        super().show()
        _ = self.exec()

    def show_timeout(self, time_ms: Optional[int] = None):
        """
        Close the popup after a certain time in milliseconds.
        """
        if time_ms:
            QTimer.singleShot(time_ms, self.accept)
        else:
            config = Config()
            time_ms = config.config.get("notification_timeout", 500)
            QTimer.singleShot(time_ms, self.accept)

        self.show()
