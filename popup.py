
from PyQt6.QtWidgets import QTextEdit, QFrame, QVBoxLayout, QWidget
from markdown_utils import WebEngineViewWithBaseUrl
from PyQt6.QtCore import Qt, QSize
import re
from markdown_utils import Markdown
from config import Config


from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QFont,
    QColor,
    QKeyEvent,
    QTextCursor,
    QTextFormat,
)

from regex_patterns import INLINE_MATH_PATTERN, BLOCK_MATH_PATTERN

class WebPopupInTextEdit:
    def __init__(self, text_edit: QTextEdit):
        self.text_edit = text_edit
        self.frame = QFrame(self.text_edit)
        self.frame.setFrameShape(QFrame.Shape.Box)
        self.frame.setLineWidth(1)

        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(1, 1, 1, 1)

        self.popup_view = WebEngineViewWithBaseUrl(self.frame)
        layout.addWidget(self.popup_view)

        self.frame.setLayout(layout)
        self.frame.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.frame.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.frame.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.frame.setFixedSize(302, 102)  # Adjust size as needed (including border)
        self.frame.hide()

        self.popup_view.page().contentsSizeChanged.connect(self.adjust_popup_size)
        self.visible = False
        self.dark_mode = False

    def show_popup(self, cursor, content, is_math=True):
        cursor_rect = self.text_edit.cursorRect(cursor)
        global_pos = self.text_edit.mapToGlobal(cursor_rect.bottomRight())

        if is_math:
            is_block_math = content.strip().startswith(
                "$$"
            ) and content.strip().endswith("$$")
            math_text = content.strip() if is_block_math else f"${content.strip()}$"
            markdown_content = Markdown(text=math_text, dark_mode=self.dark_mode)
            html = markdown_content.build_html()
        else:
            html = content

        self.popup_view.setHtml(html)
        self.frame.move(global_pos)
        self.frame.show()
        self.visible = True

    def hide_popup(self):
        if self.visible:
            self.frame.hide()
            self.visible = False

    def adjust_popup_size(self, size):
        max_width, max_height = 600, 400
        new_width = min(round(size.width()) + 2, max_width)  # +2 for borders
        new_height = min(round(size.height()) + 2, max_height)  # +2 for borders
        self.frame.resize(int(new_width), int(new_height))

    def set_dark_mode(self, is_dark):
        self.dark_mode = is_dark
        if is_dark:
            self.frame.setStyleSheet(
                """
                QFrame {
                    background-color: #2d2d2d;
                    border: 1px solid #555;
                }
            """
            )
        else:
            self.frame.setStyleSheet(
                """
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #ccc;
                }
            """
            )

        # Re-render the current content with the new dark mode setting
        if self.visible:
            cursor = self.text_edit.textCursor()
            math_content = self.is_cursor_in_math_environment(cursor)
            if math_content is not None:
                self.show_popup(cursor, math_content, is_math=True)

    def cleanup(self):
        self.frame.deleteLater()

    def on_cursor_position_changed(self):
        cursor = self.text_edit.textCursor()
        math_content = self.is_cursor_in_math_environment(cursor)
        if math_content is not None:
            self.show_popup(cursor, math_content, is_math=True)
        else:
            self.hide_popup()

    def is_cursor_in_math_environment(self, cursor):
        text = self.text_edit.toPlainText()
        pos = cursor.position()

        # Check if cursor is inside any double-dollar math environment
        for match in BLOCK_MATH_PATTERN.finditer(text):
            start, end = match.span()
            if start <= pos <= end:
                return match.group(0)  # Return the entire match including $$

        # Check if cursor is inside any single-dollar math environment
        for match in INLINE_MATH_PATTERN.finditer(text):
            start, end = match.span()
            if start <= pos <= end:
                return match.group(1)  # Return only the content inside $...$

        return None  # Return None if not inside a math environment

    def show_math_popup(self, cursor, math_content):
        self.show_popup(cursor, math_content, is_math=True)

    def hide_math_popup(self):
        self.hide_popup()
