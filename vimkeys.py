from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent, QTextCursor, QColor, QTextFormat

class VimTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vim_mode = False
        self.insert_mode = False
        self.visual_mode = False
        self.visual_anchor = None
        self.yanked_text = ""
        self.g_pressed = False
        self.cursorPositionChanged.connect(self.update_line_highlight)

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
