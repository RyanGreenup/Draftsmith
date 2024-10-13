from PyQt6.QtWidgets import QTextEdit, QFrame, QVBoxLayout
from PyQt6.sip import delete
from markdown_utils import WebEngineViewWithBaseUrl
from PyQt6.QtCore import QSize, Qt, QPoint
import re
from markdown_utils import Markdown

from PyQt6.QtGui import (
    QTextCursor,
)

from regex_patterns import INLINE_MATH_PATTERN, BLOCK_MATH_PATTERN


class PopupManager:
    def __init__(self, text_edit: QTextEdit):
        self.text_edit = text_edit
        self.create_frame()
        self.dark_mode = False

    def create_frame(self):
        if hasattr(self, "frame"):
            self.frame.hide()
            self.frame.deleteLater()
        self.frame = QFrame(self.text_edit)
        self.frame.setFrameShape(QFrame.Shape.Box)
        self.frame.setLineWidth(1)

        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(1, 1, 1, 1)

        self.popup_view = self.build_popup()
        layout.addWidget(self.popup_view)

        self.frame.setLayout(layout)
        self.frame.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.frame.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.frame.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.frame.hide()

    def build_popup(self):
        popup_view = WebEngineViewWithBaseUrl(self.frame)

        # This ccauses flickering which is annoying
        popup_view.setFixedWidth(100)
        popup_view.setFixedHeight(100)
        # popup_view.loadFinished.connect(self.adjust_size)
        return popup_view

    def resize_from_js(self, sizes):
        width = sizes["width"]
        height = sizes["height"]
        self.popup_view.setFixedWidth(int(width))
        self.popup_view.setFixedHeight(int(height))

    def adjust_size(self):
        # Reset the popup size to the size of the content
        # self.popup_view.page().runJavaScript(
        #     """
        #     function getDocumentSize() {
        #         return {
        #             width: document.documentElement.scrollWidth,
        #             height: document.documentElement.scrollHeight
        #         };
        #     }
        #     getDocumentSize();
        #     """,
        #     self.resize_from_js,
        # )

        # Destroy and recreate the popup to get the correct size

        # if not self.size_already_set:  # Set this to False in the constructor
        #     self.size_already_set = True
        if page := self.popup_view.page():
            if w := page.contentsSize().width():
                self.popup_view.setFixedWidth(int(w) + 10)
            if h := page.contentsSize().height():
                self.popup_view.setFixedHeight(int(h) + 10)
            # size = QSize(print(out.width()), int(out.height()))
            # self.frame.resize(size)

    def _show_popup(self, content, is_math=False):
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
        self.visible = True
        self.frame.show()

    def hide_popup(self):
        if hasattr(self, "visible") and hasattr(self, "frame"):
            if self.visible:
                self.frame.hide()
                self.visible = False

    def show_popup(self, content, is_math=False):
        self.create_frame()
        self._show_popup(content, is_math)

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

    def update_popup_position(self, content: str, end_pos: int):
        end_cursor = QTextCursor(self.text_edit.document())
        end_cursor.setPosition(end_pos)
        end_rect = self.text_edit.cursorRect(end_cursor)

        self.popup_manager.frame.hide()

        if vp := self.text_edit.viewport():
            viewport_pos = vp.mapToGlobal(end_rect.bottomRight())

            text_edit_rect = self.text_edit.rect()
            text_edit_global_rect = self.text_edit.mapToGlobal(text_edit_rect.topLeft())

            max_y = (
                text_edit_global_rect.y()
                + text_edit_rect.height()
                - self.popup_manager.frame.height()
            )
            new_y = min(viewport_pos.y(), max_y)

            new_x = max(
                text_edit_global_rect.x(),
                min(
                    viewport_pos.x() - self.popup_manager.frame.width(),
                    text_edit_global_rect.x()
                    + text_edit_rect.width()
                    - self.popup_manager.frame.width(),
                ),
            )

            self.popup_manager.frame.move(new_x, new_y)

            if self.text_edit.rect().contains(
                self.text_edit.mapFromGlobal(QPoint(new_x, new_y))
            ):
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

    def get_content_from_regex(
        self, cursor, pattern: re.Pattern[str]
    ) -> tuple[str, int, int] | None:
        text = self.text_edit.toPlainText()
        pos = cursor.position()

        for match in pattern.finditer(text):
            start, end = match.span()
            if start <= pos <= end:
                return match.group(0), start, end
        return None

    def get_all_math_content(self) -> list[tuple[str, int, int]]:
        text = self.text_edit.toPlainText()
        all_content = []
        for pattern in [BLOCK_MATH_PATTERN, INLINE_MATH_PATTERN]:
            for match in pattern.finditer(text):
                content = match.group(0)
                start, end = match.span()
                all_content.append((content, start, end))
        return all_content


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
                content, _, end = content_and_indices
                self.popup_positioner.update_popup_position(content, end)

    def update_popup_position_and_move_window(self):
        cursor = self.text_edit.textCursor()
        if content_and_indices := self.content_extractor.get_content(cursor):
            content, _, end = content_and_indices
            self.popup_manager.show_popup(content, is_math=True)
            self.popup_positioner.update_popup_position(content, end)
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


class MultiMathPopups:
    def __init__(self, text_edit: QTextEdit):
        self.text_edit = text_edit
        self.content_extractor = ContentExtractor(text_edit)
        self.popups = []
        self.text_edit.textChanged.connect(self.update_popups)
        self.text_edit.verticalScrollBar().valueChanged.connect(self.update_popups)
        self.text_edit.horizontalScrollBar().valueChanged.connect(self.update_popups)
        self.text_edit.resizeEvent = self.on_text_edit_resize
        self.enabled = False

    def update_popups(self):
        if not self.enabled:
            return
        # Remove existing popups
        for popup in self.popups:
            popup.cleanup()
        self.popups.clear()

        # Create new popups for all math content
        all_content = self.content_extractor.get_all_math_content()
        for content, _, end in all_content:
            popup_manager = PopupManager(self.text_edit)
            popup_positioner = PopupPositioner(self.text_edit, popup_manager)

            popup_manager.show_popup(content, is_math=True)
            popup_positioner.update_popup_position(content, end)

            self.popups.append(popup_manager)

    def on_text_edit_resize(self, event):
        self.update_popups()
        QTextEdit.resizeEvent(self.text_edit, event)

    def set_dark_mode(self, is_dark: bool):
        for popup in self.popups:
            popup.set_dark_mode(is_dark)

    def cleanup(self):
        for popup in self.popups:
            popup.cleanup()
        self.popups.clear()

    def toggle(self):
        self.enabled = not self.enabled
        if self.enabled:
            self.update_popups()
        else:
            self.cleanup()
