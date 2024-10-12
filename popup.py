import sys
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
        self.cursor_history: list[bool] = [
            False,
            False,
        ]  # Track whether the cursor was inside the popup
        self.last_cursor_position = 0

    def update_cursor_history(self):
        """
        Update the cursor history which traccks the last two cursor positions.

        TODO candidate for class
        """
        print("---START---")
        print(f"{self.cursor_history=}")
        self.cursor_history[0] = self.cursor_history[1]
        if is_inside := self.is_cursor_inside():
            self.cursor_history[1] = is_inside
        else:
            # TODO review this
            self.cursor_history[1] = False
        print(f"{self.cursor_history=}")
        print("---END---")

    def is_cursor_inside(self):
        """
        Check if the cursor is in the region that the popup should be displayed.

        TODO should this take the cursor position or text?

        This should use the self.get_content method
        """
        if out := self.get_content():
            return True
        else:
            return False

    def was_cursor_inside(self):
        return self.cursor_history[0]

    def on_cursor_position_changed(self):
        """
        Action to be taken when the cursor position changes.
        This shouldn't be needed for popup windows,
        Scrollbar change should be enough. The `pin_to_scrollbar`
        automatically calles `.update_popup_position_and_move_window`
        when the scrollbar changes.

        This method is just legacy at this stage.
        """
        # The cursor position has changed So update the history
        self.update_cursor_history()

        # If the cursor was not inside the popup last time
        # and is inside the popup now, update the popup position
        # If the cursor was inside the popup last time
        # and is not inside the popup now, hide the popup
        if self.was_cursor_inside():
            if not self.is_cursor_inside():
                self.hide_popup()
        else:
            if self.is_cursor_inside():
                self.update_popup_position_and_move_window()

        # if self.is_cursor_inside():
        # Check if the cursor is inside the region
        self.update_popup_position_and_move_window()

        pass

    def on_text_edit_resize(self, event):
        self.update_popup_position()
        QTextEdit.resizeEvent(self.text_edit, event)

    def is_cursor_within_frame(self) -> bool | None:
        """
        Check if the cursor is inside the popup.
        """
        cursor = self.text_edit.textCursor()
        if vp := self.text_edit.viewport():
            cursor_pos = vp.mapToGlobal(self.text_edit.cursorRect(cursor).center())
            return self.frame.geometry().contains(cursor_pos)
        else:
            return None

    # TODO candidate for removal
    def get_current_coror_position(self) -> tuple[int, int] | None:
        """
        Get the cursor position to show the popup.

        Typically this will be below the Auto Environment.

        Default implementation is to show the popup below the cursor.
        """
        cursor = self.text_edit.textCursor()
        cursor_pos = self.text_edit.cursorRect(cursor).center()
        if vp := self.text_edit.viewport():
            cursor_pos = vp.mapToGlobal(cursor_pos)

            text_edit_rect = self.text_edit.rect()
            text_edit_global_rect = self.text_edit.mapToGlobal(text_edit_rect.topLeft())

            new_x = text_edit_global_rect.x()
            new_y = cursor_pos.y() + 10

            return new_x, new_y
        else:
            return None

    def update_popup_position(self):
        if self.visible:
            self.hide_popup()
            co_ords = self.get_popup_position()
            if co_ords:
                # * unpack the tuple
                new_x, new_y = co_ords
                self.frame.move(new_x, new_y)

                if self.text_edit.rect().contains(
                    self.text_edit.mapFromGlobal(QPoint(new_x, new_y))
                ):
                    self.frame.show()
                else:
                    self.frame.hide()
            else:
                self.hide_popup()

    def update_popup_position_and_move_window(self, cursor=None):
        if cursor is None:
            cursor = self.text_edit.textCursor()
        if content_and_indices := self.get_content():
            content, start, end = content_and_indices
            _ = start, end
            self.show_popup(content, is_math=True)
        else:
            self.hide_popup()

    def get_content(self) -> tuple[str, int, int] | None:
        """
        Get the content relevant to the trigger, This should be the region
        that the popup will display.
        """
        # TODO is there a way to force subclasses to store this?
        # TODO consider naming store_content and get_content?
        raise NotImplementedError("Subclasses must implement this method")

    def get_all_content_block_indices_from_regex(
        self, pattern: re.Pattern[str]
    ) -> list[tuple[str, tuple[int, int]]]:
        text = self.text_edit.toPlainText()
        return [(match.group(0), match.span()) for match in pattern.finditer(text)]

    def get_content_from_regex(
        self, cursor, pattern: re.Pattern[str]
    ) -> tuple[str, int, int] | None:
        """
        Take the entire editing text, apply regex over the whole thing and
        check if the cursor is inside one of the matches.
        """
        text = self.text_edit.toPlainText()

        # Length in terms of index, i.e. all text is an array of characters
        # This is the cursors index in that array
        pos = cursor.position()

        for text, (start, end) in self.get_all_content_block_indices_from_regex(
            pattern
        ):
            if start <= pos <= end:
                return text, start, end
        else:
            # If nothing is found
            return None

    def on_text_changed(self):
        cursor = self.text_edit.textCursor()
        current_position = cursor.position()

        if self.was_cursor_inside():
            if self.is_cursor_inside():
                pass
            else:
                self.hide_popup()
        else:
            if self.is_cursor_inside():
                self.update_popup_position_and_move_window()
                self.hide_popup()
            else:
                pass

        self.update_cursor_history()
        # TODO merge this with the history method above
        self.last_cursor_position = current_position

    def get_current_block_end(self, content):
        if out := self.get_content():
            _, _, end = out
            return end
        else:
            return None

    def get_popup_position(self) -> tuple[int, int] | None:
        """
        Get the cursor position to show the popup.

        Typically this will be below the Auto Environment.

        Default implementation is to show the popup below the cursor.
        """

        if math_content_and_indices := self.get_content():
            content, start_pos, end_pos = math_content_and_indices
            _ = start_pos
            _ = content
            end_cursor = QTextCursor(self.text_edit.document())
            end_cursor.setPosition(end_pos)
            end_rect = self.text_edit.cursorRect(end_cursor)

            if vp := self.text_edit.viewport():
                viewport_pos = vp.mapToGlobal(end_rect.bottomRight())

                text_edit_rect = self.text_edit.rect()
                text_edit_global_rect = self.text_edit.mapToGlobal(
                    text_edit_rect.topLeft()
                )

                max_y = (
                    text_edit_global_rect.y()
                    + text_edit_rect.height()
                    - self.frame.height()
                )
                new_y = min(viewport_pos.y(), max_y)

                new_x = max(
                    text_edit_global_rect.x(),
                    min(
                        viewport_pos.x(),
                        text_edit_global_rect.x()
                        + text_edit_rect.width()
                        - self.frame.width(),
                    ),
                )
                return new_x, new_y
            else:
                return None
        else:
            return None


class MathAutoPopups(AutoPopups):
    """
    A class creating math auto popups based on Regex
    """

    def __init__(self, text_edit: QTextEdit, pin_to_scrollbar: bool = True):
        super().__init__(text_edit, pin_to_scrollbar)
        self.text_edit.textChanged.connect(self.on_text_changed)

    def get_content(self) -> tuple[str, int, int] | None:
        cursor = self.text_edit.textCursor()
        # Try for Block Math first
        for ptn in [BLOCK_MATH_PATTERN, INLINE_MATH_PATTERN]:
            if c := self.get_content_from_regex(cursor, ptn):
                return c
        return None
