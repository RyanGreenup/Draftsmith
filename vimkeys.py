from PyQt6.QtWidgets import QTextEdit, QFrame, QVBoxLayout
from markdown_utils import WebEngineViewWithBaseUrl
from PyQt6.QtCore import Qt
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


class BaseEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set fonts based on configuration
        self.set_fonts()

        # Load configuration

    def set_fonts(self):
        config = Config().config
        font = QFont()
        font_config = config["fonts"]["editor"]

        # Set monospace font for the editor
        font.setFamily(font_config["mono"])

        # You can set a default size here, or use a size from the config if you add one
        font.setPointSize(12)  # Default size, adjust as needed

        self.setFont(font)

    def update_fonts(self):
        self.set_fonts()
        self.update()


class VimTextEdit(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vim_mode = False
        self.insert_mode = False
        self.visual_mode = False
        self.visual_anchor = None
        self.yanked_text = ""
        self.g_pressed = False
        self.dark_mode = False

        # Initialize the WebPopupInTextEdit
        self.web_popup = WebPopupInTextEdit(self)

        # Connect signals after initializing web_popup
        self.cursorPositionChanged.connect(self.update_line_highlight)
        self.cursorPositionChanged.connect(self.web_popup.on_cursor_position_changed)
        self.textChanged.connect(self.web_popup.on_cursor_position_changed)

    def update_line_highlight(self):
        if self.vim_mode and not self.insert_mode:
            self.highlight_current_line()
        else:
            self.clear_line_highlight()

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(Qt.GlobalColor.yellow)
            line_color.setAlpha(40)  # Set transparency
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def clear_line_highlight(self):
        self.setExtraSelections([])

    def keyPressEvent(self, e: QKeyEvent):
        match (self.vim_mode, self.insert_mode, self.visual_mode, e.key()):
            case (False, _, _, Qt.Key.Key_Escape):
                self.vim_mode = True
                self.insert_mode = False
                self.visual_mode = False
                self.update_line_highlight()

            case (False, _, _, _):
                super().keyPressEvent(e)

            case (True, True, _, Qt.Key.Key_Escape):
                self.insert_mode = False
                self.update_line_highlight()

            case (True, True, _, _):
                super().keyPressEvent(e)

            case (True, False, True, _):
                self.handle_visual_mode(e)

            case (True, False, False, _):
                self.handle_normal_mode(e)

    def handle_normal_mode(self, e: QKeyEvent):
        cursor = self.textCursor()
        match e.key():
            case Qt.Key.Key_H:
                cursor.movePosition(QTextCursor.MoveOperation.Left)
            case Qt.Key.Key_J:
                cursor.movePosition(QTextCursor.MoveOperation.Down)
            case Qt.Key.Key_K:
                cursor.movePosition(QTextCursor.MoveOperation.Up)
            case Qt.Key.Key_L:
                cursor.movePosition(QTextCursor.MoveOperation.Right)
            case Qt.Key.Key_I:
                self.insert_mode = True
                self.clear_line_highlight()
            case Qt.Key.Key_V:
                if not e.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self.visual_mode = True
                    self.visual_anchor = cursor.position()
                else:
                    self.visual_mode = True
                    self.select_entire_line(cursor)
            case Qt.Key.Key_P:
                self.put_text(cursor)
            case Qt.Key.Key_G:
                if self.g_pressed:
                    self.move_to_top(cursor)
                    self.g_pressed = False
                else:
                    self.move_to_bottom(cursor)
            case _:
                self.g_pressed = False

        # This separate check for Key_G ensures that the `g_pressed` state is handled correctly.
        if e.key() == Qt.Key.Key_G and not self.g_pressed:
            self.g_pressed = True
        else:
            self.setTextCursor(cursor)

        self.update_line_highlight()

    def handle_visual_mode(self, e: QKeyEvent):
        cursor = self.textCursor()

        match e.key():
            case Qt.Key.Key_Escape:
                self.exit_visual_mode(cursor)
            case Qt.Key.Key_J:
                cursor.movePosition(
                    QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor
                )
            case Qt.Key.Key_K:
                cursor.movePosition(
                    QTextCursor.MoveOperation.Up, QTextCursor.MoveMode.KeepAnchor
                )
            case Qt.Key.Key_Y:
                self.yank_text(cursor)

        self.setTextCursor(cursor)

    def exit_visual_mode(self, cursor):
        self.visual_mode = False
        cursor.clearSelection()
        self.setTextCursor(cursor)

    def yank_text(self, cursor):
        self.yanked_text = cursor.selectedText()
        self.exit_visual_mode(cursor)

    def put_text(self, cursor):
        if self.yanked_text:
            cursor.insertText(self.yanked_text)

    def select_entire_line(self, cursor):
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(
            QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor
        )
        self.setTextCursor(
            cursor
        )  # Set the cursor to reflect the entire line selection.

    def move_to_top(self, cursor):
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.setTextCursor(cursor)

    def move_to_bottom(self, cursor):
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.vim_mode = False
        self.insert_mode = False
        self.visual_mode = False
        self.clear_line_highlight()

    def closeEvent(self, event):
        self.web_popup.cleanup()
        super().closeEvent(event)

    def set_dark_mode(self, is_dark):
        self.dark_mode = is_dark
        self.web_popup.set_dark_mode(is_dark)
