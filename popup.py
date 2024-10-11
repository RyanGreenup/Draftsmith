
from PyQt6.QtWidgets import QTextEdit, QFrame, QVBoxLayout, QWidget, QScrollBar
from markdown_utils import WebEngineViewWithBaseUrl
from PyQt6.QtCore import Qt, QSize, QPoint
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
    def __init__(self, text_edit: QTextEdit, pin_to_scroolbar: bool = True):
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

        if pin_to_scroolbar:
            on_scroll = self.update_popup_position_and_move_window
        else:
            on_scroll = self.update_popup_position
        self.text_edit.verticalScrollBar().valueChanged.connect(on_scroll)
        self.text_edit.horizontalScrollBar().valueChanged.connect(on_scroll)
        self.text_edit.resizeEvent = self.on_text_edit_resize

    def get_math_block_end(self, content):
        text = self.text_edit.toPlainText()
        start_pos = text.find(content)
        end_pos = start_pos + len(content)

        # Find the position of the closing $$
        closing_pos = text.find("$$", end_pos - 2)
        if closing_pos != -1:
            return closing_pos + 2  # Return the position after the closing $$
        return end_pos  # Fallback to the end of the content if no closing $$ found

    def show_popup(self, cursor, content, is_math=True):
        if is_math:
            is_block_math = content.strip().startswith("$$") and content.strip().endswith("$$")
            math_text = content.strip() if is_block_math else f"${content.strip()}$"
            markdown_content = Markdown(text=math_text, dark_mode=self.dark_mode)
            html = markdown_content.build_html()
        else:
            html = content

        # TODO only set HTML if it has changed
        self.popup_view.setHtml(html)
        self.visible = True
        self.update_popup_position()
        self.frame.show()

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

    def update_popup_position_and_move_window(self):
        self.on_cursor_position_changed()

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

    def update_popup_position(self):
        if self.visible:
            self.hide_popup()
            cursor = self.text_edit.textCursor()
            math_content = self.is_cursor_in_math_environment(cursor)
            if math_content is not None:
                end_pos = self.get_math_block_end(math_content)
                end_cursor = QTextCursor(self.text_edit.document())
                end_cursor.setPosition(end_pos)
                end_rect = self.text_edit.cursorRect(end_cursor)

                # Calculate the position relative to the viewport
                viewport_pos = self.text_edit.viewport().mapToGlobal(end_rect.bottomRight())

                # Adjust the position if it's outside the visible area
                text_edit_rect = self.text_edit.rect()
                text_edit_global_rect = self.text_edit.mapToGlobal(text_edit_rect.topLeft())

                max_y = text_edit_global_rect.y() + text_edit_rect.height() - self.frame.height()
                new_y = min(viewport_pos.y(), max_y)

                # Ensure the popup stays within the text edit's boundaries
                new_x = max(text_edit_global_rect.x(), min(viewport_pos.x(), text_edit_global_rect.x() + text_edit_rect.width() - self.frame.width()))

                # Set the new position
                self.frame.move(new_x, new_y)

                # Make sure the popup is visible if it's within the text edit's boundaries
                if text_edit_rect.contains(self.text_edit.mapFromGlobal(QPoint(new_x, new_y))):
                    self.frame.show()
                else:
                    self.frame.hide()
            else:
                self.hide_popup()

    def on_text_edit_resize(self, event):
        self.update_popup_position()
        # Call the original resizeEvent
        QTextEdit.resizeEvent(self.text_edit, event)
