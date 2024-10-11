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

    # NOTE Tieing this together in the higher level class makes sense
    # Behaviour should be uniform
    # TODO Do we want this behaviour though?
    # Only makes sense to update on textEdit, not on cursor change
    # Scrollbar change should be enough
    def update_popup_position_and_move_window(self):
        raise NotImplementedError("Subclasses must implement this method")

    def on_cursor_position_changed(self):
        """
        Action to be taken when the cursor position changes.
        This shouldn't be needed for popup windows,
        Scrollbar change should be enough. The `pin_to_scrollbar`
        automatically calles `.update_popup_position_and_move_window`
        when the scrollbar changes.

        This method is just legacy at this stage.
        """

        pass

    def on_text_edit_resize(self, event):
        self.update_popup_position()
        QTextEdit.resizeEvent(self.text_edit, event)

    def is_cursor_inside(self) -> bool | None:
        """
        Check if the cursor is inside the popup.
        """
        cursor = self.text_edit.textCursor()
        if vp := self.text_edit.viewport():
            cursor_pos = vp.mapToGlobal(self.text_edit.cursorRect(cursor).center())
            return self.frame.geometry().contains(cursor_pos)
        else:
            return None

    def get_popup_position(self) -> tuple[int, int] | None:
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

    # def get_region_content_regex():
    #     pass

    def update_popup_position_and_move_window(self):
        cursor = self.text_edit.textCursor()
        # The text in the region the popup will display
        content = self.get_content(cursor)
        if content is not None:
            # Show the popup if we got something
            self.show_popup(content, is_math=True)
        else:
            # Hide the popup if we didn't get anything
            self.hide_popup()

    def get_content(self, cursor):
        """
        Get the content to display in the popup.
        """
        raise NotImplementedError("Subclasses must implement this method")

    def get_content_from_regex(self, cursor, pattern: re.Pattern[str]) -> str | None:
        text = self.text_edit.toPlainText()
        pos = cursor.position()

        for match in pattern.finditer(text):
            start, end = match.span()
            if start <= pos <= end:
                return match.group(0)

        return None


class MathAutoPopups(AutoPopups):
    """
    A class creating math auto popups based on Regex
    """

    def __init__(self, text_edit: QTextEdit, pin_to_scrollbar: bool = True):
        super().__init__(text_edit, pin_to_scrollbar)
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.last_cursor_position = 0

    def on_text_changed(self):
        cursor = self.text_edit.textCursor()
        current_position = cursor.position()
        
        # Check if we've just entered a math environment
        if self.is_math_environment_start(current_position):
            self.update_popup_position_and_move_window(cursor)
        elif current_position < self.last_cursor_position:
            # If we've moved backwards (e.g., deleted text), check again
            self.update_popup_position_and_move_window(cursor)
        else:
            # If we're already showing a popup, update its content
            if self.visible:
                self.update_popup_position_and_move_window(cursor)
        
        self.last_cursor_position = current_position

    def is_math_environment_start(self, position):
        text = self.text_edit.toPlainText()
        if position > 0:
            if text[position-1:position+1] == '$$':
                return True
            if position > 1 and text[position-2:position] == '$$':
                return True
            if text[position-1] == '$' and (position == 1 or text[position-2] != '$'):
                return True
        return False

    def update_popup_position_and_move_window(self, cursor=None):
        if cursor is None:
            cursor = self.text_edit.textCursor()
        content = self.get_content(cursor)
        if content is not None:
            self.show_popup(content, is_math=True)
        else:
            self.hide_popup()

    def get_content(self, cursor):
        # Try for Block Math first
        for ptn in [BLOCK_MATH_PATTERN, INLINE_MATH_PATTERN]:
            if c := self.get_content_from_regex(cursor, ptn):
                return c
        return None

    def get_math_block_end(self, content):
        text = self.text_edit.toPlainText()
        start_pos = text.find(content)
        end_pos = start_pos + len(content)

        closing_pos = text.find("$$", end_pos - 2)
        if closing_pos != -1:
            return closing_pos + 2
        return end_pos

    def get_popup_position(self) -> tuple[int, int] | None:
        """
        Get the cursor position to show the popup.

        Typically this will be below the Auto Environment.

        Default implementation is to show the popup below the cursor.
        """

        cursor = self.text_edit.textCursor()
        math_content = self.get_content(cursor)
        if math_content:
            end_pos = self.get_math_block_end(math_content)
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

    def is_cursor_inside(self) -> bool:
        """
        Check if the cursor is inside the math popup.
        """
        if not self.visible:
            return False

        cursor = self.text_edit.textCursor()
        return self.get_content(cursor) is not None
