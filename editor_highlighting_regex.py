import re
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QFont,
    QColor,
)
from regex_patterns import INLINE_MATH_PATTERN, BLOCK_MATH_PATTERN


def utf16_index(text, unicode_index):
    # Encode the string up to the unicode index in utf-16 and count the 2-byte characters.
    return len(text[:unicode_index].encode("utf-16-le")) // 2


class MarkdownHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Markdown code in QTextEdit."""

    def __init__(self, document):
        super().__init__(document)
        # Define the highlighting rules
        self.highlightingRules = []
        # If using Native re module, use this list as unicode is handled differently
        self.highlightingRules_unicode = []

        # Heading format
        for i in range(1, 7):
            headingFormat = QTextCharFormat()
            headingFormat.setFontWeight(QFont.Weight.Bold)
            headingFormat.setForeground(QColor("blue"))
            headingFormat.setFontPointSize(24 - i * 2)
            hashes = "#" * i
            self.highlightingRules.append(
                (QRegularExpression(f"^{hashes} .+"), headingFormat)
            )

        # Block Math (use native Regex because DotALL doesn't seem to be working)
        blockMathFormat = QTextCharFormat()
        blockMathFormat.setForeground(QColor("darkGreen"))
        blockMathFormat.setBackground(QColor("lightGray"))
        self.highlightingRules_unicode.append(
            (BLOCK_MATH_PATTERN, blockMathFormat)
        )

        # Inline Math
        inlineMathFormat = QTextCharFormat()
        inlineMathFormat.setForeground(QColor("darkGreen"))
        # Set Background to highlight math
        inlineMathFormat.setBackground(QColor("lightGray"))
        self.highlightingRules_unicode.append(
            (INLINE_MATH_PATTERN, inlineMathFormat)
        )

        # Bold format
        boldFormat = QTextCharFormat()
        boldFormat.setFontWeight(QFont.Weight.Bold)
        self.highlightingRules.append(
            (QRegularExpression("\\*\\*(.*?)\\*\\*"), boldFormat)
        )
        self.highlightingRules.append((QRegularExpression("__(.*?)__"), boldFormat))

        # Italic format
        italicFormat = QTextCharFormat()
        italicFormat.setFontItalic(True)
        self.highlightingRules.append((QRegularExpression("\\*(.*?)\\*"), italicFormat))
        self.highlightingRules.append((QRegularExpression("_(.*?)_"), italicFormat))

        # Code format
        codeFormat = QTextCharFormat()
        codeFormat.setFontFamily("Courier")
        codeFormat.setForeground(QColor("darkGreen"))
        self.highlightingRules.append((QRegularExpression("`[^`]+`"), codeFormat))
        self.highlightingRules.append((QRegularExpression("^\\s*```.*"), codeFormat))

        # Link format
        linkFormat = QTextCharFormat()
        linkFormat.setForeground(QColor("darkBlue"))
        self.highlightingRules.append(
            (QRegularExpression("\\[.*?\\]\\(.*?\\)"), linkFormat)
        )

        # Image format
        imageFormat = QTextCharFormat()
        imageFormat.setForeground(QColor("darkMagenta"))
        self.highlightingRules.append(
            (QRegularExpression("!\\[.*?\\]\\(.*?\\)"), imageFormat)
        )

        # List format
        listFormat = QTextCharFormat()
        listFormat.setForeground(QColor("brown"))
        self.highlightingRules.append(
            (QRegularExpression("^\\s*([-+*])\\s+.*"), listFormat)
        )
        self.highlightingRules.append(
            (QRegularExpression("^\\s*\\d+\\.\\s+.*"), listFormat)
        )

    def highlightBlock(self, text):
        if text:
            for pattern, format in self.highlightingRules:
                iterator = pattern.globalMatch(text)
                while iterator.hasNext():
                    match = iterator.next()
                    index = match.capturedStart()
                    length = match.capturedLength()
                    self.setFormat(index, length, format)

            for pattern, format in self.highlightingRules_unicode:
                matches = re.finditer(pattern, text)
                for match in matches:
                    index = match.start()
                    length = match.end() - index

                    # Convert to utf-16 indices
                    index_utf16 = utf16_index(text, index)
                    length_utf16 = utf16_index(text, match.end()) - index_utf16

                    self.setFormat(index_utf16, length_utf16, format)
