from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QTextEdit,
    QTextEdit,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent, QTextCursor


class VimTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vim_mode = False
        self.insert_mode = False
        self.visual_mode = False
        self.visual_anchor = None
        self.yanked_text = ""

    def keyPressEvent(self, e: QKeyEvent):
        if not self.vim_mode:
            if e.key() == Qt.Key.Key_Escape:
                self.vim_mode = True
                self.insert_mode = False
                self.visual_mode = False
            else:
                super().keyPressEvent(e)
        elif self.insert_mode:
            if e.key() == Qt.Key.Key_Escape:
                self.insert_mode = False
            else:
                super().keyPressEvent(e)
        elif self.visual_mode:
            self.handle_visual_mode(e)
        else:
            self.handle_normal_mode(e)

    def handle_normal_mode(self, e: QKeyEvent):
        cursor = self.textCursor()
        if e.key() == Qt.Key.Key_H:
            cursor.movePosition(QTextCursor.MoveOperation.Left)
        elif e.key() == Qt.Key.Key_J:
            cursor.movePosition(QTextCursor.MoveOperation.Down)
        elif e.key() == Qt.Key.Key_K:
            cursor.movePosition(QTextCursor.MoveOperation.Up)
        elif e.key() == Qt.Key.Key_L:
            cursor.movePosition(QTextCursor.MoveOperation.Right)
        elif e.key() == Qt.Key.Key_I:
            self.insert_mode = True
        elif (
            e.key() == Qt.Key.Key_V
            and not e.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.visual_mode = True
            self.visual_anchor = cursor.position()
        elif (
            e.key() == Qt.Key.Key_V
            and e.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.visual_mode = True
            self.select_entire_line(cursor)
        elif e.key() == Qt.Key.Key_P:
            self.put_text(cursor)
        self.setTextCursor(cursor)

    def handle_visual_mode(self, e: QKeyEvent):
        cursor = self.textCursor()
        if e.key() == Qt.Key.Key_Escape:
            self.exit_visual_mode(cursor)
        elif e.key() == Qt.Key.Key_J:
            cursor.movePosition(
                QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor
            )
        elif e.key() == Qt.Key.Key_K:
            cursor.movePosition(
                QTextCursor.MoveOperation.Up, QTextCursor.MoveMode.KeepAnchor
            )
        elif e.key() == Qt.Key.Key_Y:
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

    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        self.vim_mode = False
        self.insert_mode = False
        self.visual_mode = False
