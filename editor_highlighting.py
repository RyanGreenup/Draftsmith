from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from tree_sitter import Language, Parser
import os


class MarkdownTSHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Markdown code using py-tree-sitter."""

    def __init__(self, document):
        super().__init__(document)

        # Initialize the parser
        self.parser = Parser()
        self.parser.set_language(MARKDOWN_LANGUAGE)

        # Define text formats for different markdown elements
        self.formats = {}

        # Heading format
        heading_format = QTextCharFormat()
        heading_format.setFontWeight(QFont.Weight.Bold)
        heading_format.setForeground(QColor("blue"))

        # Emphasis format
        emphasis_format = QTextCharFormat()
        emphasis_format.setFontItalic(True)
        emphasis_format.setForeground(QColor("darkRed"))

        # Strong emphasis format
        strong_format = QTextCharFormat()
        strong_format.setFontWeight(QFont.Weight.Bold)
        strong_format.setForeground(QColor("darkRed"))

        # Code format
        code_format = QTextCharFormat()
        code_format.setFontFamily("Courier")
        code_format.setForeground(QColor("darkGreen"))

        # Link format
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("darkBlue"))

        # Image format
        image_format = QTextCharFormat()
        image_format.setForeground(QColor("darkMagenta"))

        # List format
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("brown"))

        # Map node types to formats
        self.formats = {
            "atx_heading": heading_format,
            "setext_heading": heading_format,
            "emphasis": emphasis_format,
            "strong_emphasis": strong_format,
            "inline_code": code_format,
            "fenced_code_block": code_format,
            "link_destination": link_format,
            "image": image_format,
            "list_item": list_format,
            # Add other mappings as needed...
        }

    def highlightBlock(self, text):
        # Parse the text
        tree = self.parser.parse(bytes(text, "utf-8"))

        # Create a mapping from byte offsets to character offsets
        self.byte_to_char = self.build_byte_to_char_map(text)

        # Start highlighting from the root node
        root_node = tree.root_node
        self.highlight_node(root_node, text)

    def highlight_node(self, node, text):
        # Check if the node type has a corresponding format
        if node.type in self.formats:
            start_byte = node.start_byte
            end_byte = node.end_byte

            # Get character offsets using the mapping
            start = self.byte_to_char.get(start_byte)
            end = self.byte_to_char.get(end_byte)

            if start is not None and end is not None:
                length = end - start
                if length > 0:
                    # Apply the format
                    self.setFormat(start, length, self.formats[node.type])

        # Recursively highlight child nodes
        for child in node.children:
            self.highlight_node(child, text)
# Specify the path to the compiled shared library
MARKDOWN_LANGUAGE = Language('libtree-sitter-markdown.so', 'markdown')
    def build_byte_to_char_map(self, text):
        byte_to_char = {}
        byte_index = 0
        char_index = 0
        while char_index < len(text):
            char = text[char_index]
            char_bytes = char.encode('utf-8')
            for _ in char_bytes:
                byte_to_char[byte_index] = char_index
                byte_index += 1
            char_index += 1
        # Map the final byte index to the end of the text
        byte_to_char[byte_index] = char_index
        return byte_to_char