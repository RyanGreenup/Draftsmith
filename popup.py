from PyQt6.QtWidgets import QTextEdit, QFrame, QVBoxLayout
from markdown_utils import WebEngineViewWithBaseUrl
from PyQt6.QtCore import Qt, QPoint
import re
from markdown_utils import Markdown

from PyQt6.QtGui import (
    QTextCursor,
)

from regex_patterns import INLINE_MATH_PATTERN, BLOCK_MATH_PATTERN

class PopupManager:
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

class PopupPositioner:
    def __init__(self, text_edit: QTextEdit, popup_manager: PopupManager):
        self.text_edit = text_edit
        self.popup_manager = popup_manager

    def update_popup_position(self, content, start_pos, end_pos):
        end_cursor = QTextCursor(self.text_edit.document())
        end_cursor.setPosition(end_pos)
        end_rect = self.text_edit.cursorRect(end_cursor)

        if vp := self.text_edit.viewport():
            viewport_pos = vp.mapToGlobal(end_rect.bottomRight())

            text_edit_rect = self.text_edit.rect()
            text_edit_global_rect = self.text_edit.mapToGlobal(text_edit_rect.topLeft())

            max_y = text_edit_global_rect.y() + text_edit_rect.height() - self.popup_manager.frame.height()
            new_y = min(viewport_pos.y(), max_y)

            new_x = max(
                text_edit_global_rect.x(),
                min(
                    viewport_pos.x() - self.popup_manager.frame.width(),
                    text_edit_global_rect.x() + text_edit_rect.width() - self.popup_manager.frame.width(),
                ),
            )

            self.popup_manager.frame.move(new_x, new_y)

            if self.text_edit.rect().contains(self.text_edit.mapFromGlobal(QPoint(new_x, new_y))):
                self.popup_manager.frame.show()
            else:
                self.popup_manager.frame.hide()

class CursorTracker:
    def __init__(self):
        self.cursor_history = [False, False]
        self.last_cursor_position = 0

    def update_cursor_history(self, is_inside):
        self.cursor_history[0] = self.cursor_history[1]
        self.cursor_history[1] = is_inside

    def was_cursor_inside(self):
        return self.cursor_history[0]

class ContentExtractor:
    def __init__(self, text_edit: QTextEdit):
        self.text_edit = text_edit

    def get_content(self, cursor) -> tuple[str, int, int] | None:
        for pattern in [BLOCK_MATH_PATTERN, INLINE_MATH_PATTERN]:
            if content := self.get_content_from_regex(cursor, pattern):
                return content
        return None

    def get_content_from_regex(self, cursor, pattern: re.Pattern[str]) -> tuple[str, int, int] | None:
        text = self.text_edit.toPlainText()
        pos = cursor.position()

        for match in pattern.finditer(text):
            start, end = match.span()
            if start <= pos <= end:
                return match.group(0), start, end
        return None

class AutoPopups:
    def __init__(self, text_edit: QTextEdit, pin_to_scrollbar: bool = True):
        self.text_edit = text_edit
        self.popup_manager = PopupManager(text_edit)
        self.popup_positioner = PopupPositioner(text_edit, self.popup_manager)
        self.cursor_tracker = CursorTracker()
        self.content_extractor = ContentExtractor(text_edit)

        if pin_to_scrollbar:
            on_scroll = self.update_popup_position_and_move_window
        else:
            on_scroll = self.update_popup_position
        self.text_edit.verticalScrollBar().valueChanged.connect(on_scroll)
        self.text_edit.horizontalScrollBar().valueChanged.connect(on_scroll)
        self.text_edit.resizeEvent = self.on_text_edit_resize
        self.text_edit.textChanged.connect(self.on_text_changed)

    def update_popup_position(self):
        if self.popup_manager.visible:
            self.popup_manager.hide_popup()
            cursor = self.text_edit.textCursor()
            if content_and_indices := self.content_extractor.get_content(cursor):
                content, start, end = content_and_indices
                self.popup_positioner.update_popup_position(content, start, end)

    def update_popup_position_and_move_window(self):
        cursor = self.text_edit.textCursor()
        if content_and_indices := self.content_extractor.get_content(cursor):
            content, start, end = content_and_indices
            self.popup_manager.show_popup(content, is_math=True)
            self.popup_positioner.update_popup_position(content, start, end)
        else:
            self.popup_manager.hide_popup()

    def on_text_edit_resize(self, event):
        self.update_popup_position()
        QTextEdit.resizeEvent(self.text_edit, event)

    def on_text_changed(self):
        cursor = self.text_edit.textCursor()
        current_position = cursor.position()

        is_inside = self.content_extractor.get_content(cursor) is not None
        self.cursor_tracker.update_cursor_history(is_inside)

        if self.cursor_tracker.was_cursor_inside():
            if is_inside:
                self.update_popup_position_and_move_window()
            else:
                self.popup_manager.hide_popup()
        else:
            if is_inside:
                self.update_popup_position_and_move_window()

        self.cursor_tracker.last_cursor_position = current_position

class MathAutoPopups(AutoPopups):
    def __init__(self, text_edit: QTextEdit, pin_to_scrollbar: bool = True):
        super().__init__(text_edit, pin_to_scrollbar)
        self.text_edit.cursorPositionChanged.connect(self.on_cursor_position_changed)

    def on_cursor_position_changed(self):
        self.on_text_changed()
