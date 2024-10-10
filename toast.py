from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

class ToastNotification(QLabel):
    def __init__(self, message: str, duration: int = 3000):
        super().__init__(message)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.ToolTip |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            background-color: rgba(0, 0, 0, 180);
            color: white;
            padding: 10px;
            border-radius: 5px;
        """)
        self.adjustSize()
        self.setFixedSize(self.size())

        # Automatically close the toast after the specified duration
        QTimer.singleShot(duration, self.close)

    def show_at(self, position: tuple[int, int]):
        self.move(*position)
        self.show()
