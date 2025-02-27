from PyQt6.QtWidgets import QTextEdit, QFrame, QVBoxLayout, QWidget
from markdown_utils import WebEngineViewWithBaseUrl
from PyQt6.QtCore import Qt, QSize
import re
from markdown_utils import Markdown
from config import Config

# from popup import MathAutoPopups


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
        # self.web_popup = MathAutoPopups(self)
        #
        # # Connect signals after initializing web_popup
        # self.cursorPositionChanged.connect(self.update_line_highlight)
        # self.cursorPositionChanged.connect(self.web_popup.on_cursor_position_changed)
        # self.textChanged.connect(self.web_popup.on_cursor_position_changed)

        # self.math_webviews = []

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

    def insert_math_webviews(self):
        # Clear existing math webviews
        for webview in self.math_webviews:
            self.document().removeChild(webview)
        self.math_webviews.clear()

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        while True:
            # Find next math environment
            cursor = self.document().find(BLOCK_MATH_PATTERN, cursor)
            if cursor.isNull():
                break

            math_content = cursor.selectedText()

            # Create WebView for math content
            math_webview = WebEngineViewWithBaseUrl(self)
            markdown_content = Markdown(text=math_content, dark_mode=self.dark_mode)
            html = markdown_content.build_html()
            math_webview.setHtml(html)

            # Create a container widget for the WebView
            container = QWidget(self)
            layout = QVBoxLayout(container)
            layout.addWidget(math_webview)
            layout.setContentsMargins(0, 5, 0, 5)  # Add some vertical spacing

            # Insert the container into the document
            cursor.insertBlock()
            format = QTextCharFormat()
            format.setObjectType(
                QTextFormat.ObjectTypes.UserObject + 1
            )  # Custom object type
            cursor.insertText("\uFFFc", format)  # Object replacement character

            self.document().addChild(container)
            container.setParent(self.document())

            # Set the size of the container
            container.setFixedSize(
                QSize(self.width() - 20, 100)
            )  # Adjust height as needed

            self.math_webviews.append(container)

            # Move cursor to end of inserted block
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)

        self.setTextCursor(cursor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Resize math webviews when the editor is resized
        for webview in self.math_webviews:
            webview.setFixedWidth(self.width() - 20)

    def set_dark_mode(self, is_dark):
        self.dark_mode = is_dark
        # Update existing math webviews
        # self.web_popup.set_dark_mode(is_dark)
        # self.insert_math_webviews()
