
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

class WebViewPopups:
    """
    A class creating webview popups
    """
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
        self.frame.setFixedSize(302, 102)
        self.frame.hide()

        self.popup_view.page().contentsSizeChanged.connect(self.adjust_popup_size)
        self.visible = False
        self.dark_mode = False

    def show_popup(self, content, is_math=False):
        if is_math:
            is_block_math = content.strip().startswith("$$") and content.strip().endswith("$$")
            math_text = content.strip() if is_block_math else f"${content.strip()}$"
            markdown_content = Markdown(text=math_text, dark_mode=self.dark_mode)
            html = markdown_content.build_html()
        else:
            html = content

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
        new_width = min(round(size.width()) + 2, max_width)
        new_height = min(round(size.height()) + 2, max_height)
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

    def cleanup(self):
        self.frame.deleteLater()

    def update_popup_position(self):
        # Implement basic positioning logic here
        pass

class AutoPopups(WebViewPopups):
    """
    A class creating auto popups
    """
    def __init__(self, text_edit: QTextEdit, pin_to_scrollbar: bool = True):
        super().__init__(text_edit)

        if pin_to_scrollbar:
            on_scroll = self.update_popup_position_and_move_window
        else:
            on_scroll = self.update_popup_position
        self.text_edit.verticalScrollBar().valueChanged.connect(on_scroll)
        self.text_edit.horizontalScrollBar().valueChanged.connect(on_scroll)
        self.text_edit.resizeEvent = self.on_text_edit_resize

    def update_popup_position_and_move_window(self):
        self.on_cursor_position_changed()

    def on_cursor_position_changed(self):
        raise NotImplementedError, "Subclass must implement this method"


    def on_text_edit_resize(self, event):
        self.update_popup_position()
        QTextEdit.resizeEvent(self.text_edit, event)

class MathAutoPopups(AutoPopups):
    """
    A class creating math auto popups based on Regex
    """
    def __init__(self, text_edit: QTextEdit, pin_to_scrollbar: bool = True):
        super().__init__(text_edit, pin_to_scrollbar)

    def on_cursor_position_changed(self):
        cursor = self.text_edit.textCursor()
        math_content = self.is_cursor_in_math_environment(cursor)
        if math_content is not None:
            self.show_popup(math_content, is_math=True)
        else:
            self.hide_popup()

    def is_cursor_in_math_environment(self, cursor):
        text = self.text_edit.toPlainText()
        pos = cursor.position()

        for match in BLOCK_MATH_PATTERN.finditer(text):
            start, end = match.span()
            if start <= pos <= end:
                return match.group(0)

        for match in INLINE_MATH_PATTERN.finditer(text):
            start, end = match.span()
            if start <= pos <= end:
                return match.group(1)

        return None

    def get_math_block_end(self, content):
        text = self.text_edit.toPlainText()
        start_pos = text.find(content)
        end_pos = start_pos + len(content)

        closing_pos = text.find("$$", end_pos - 2)
        if closing_pos != -1:
            return closing_pos + 2
        return end_pos

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

                viewport_pos = self.text_edit.viewport().mapToGlobal(end_rect.bottomRight())

                text_edit_rect = self.text_edit.rect()
                text_edit_global_rect = self.text_edit.mapToGlobal(text_edit_rect.topLeft())

                max_y = text_edit_global_rect.y() + text_edit_rect.height() - self.frame.height()
                new_y = min(viewport_pos.y(), max_y)

                new_x = max(text_edit_global_rect.x(), min(viewport_pos.x(), text_edit_global_rect.x() + text_edit_rect.width() - self.frame.width()))

                self.frame.move(new_x, new_y)

                if text_edit_rect.contains(self.text_edit.mapFromGlobal(QPoint(new_x, new_y))):
                    self.frame.show()
                else:
                    self.frame.hide()
            else:
                self.hide_popup()
