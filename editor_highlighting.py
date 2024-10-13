from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from tree_sitter import Language, Parser
import os

# Specify the path to the compiled shared library
MARKDOWN_LANGUAGE = Language("libtree-sitter-markdown.so")


class MarkdownTSHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Markdown code using py-tree-sitter."""

    def __init__(self, document):
        super().__init__(document)

        # Initialize the parser
        self.parser = Parser()
        self.parser.set_language(MARKDOWN_LANGUAGE)

        # Compile tree-sitter queries for Markdown elements
        self.query = MARKDOWN_LANGUAGE.query(
            """
        ; Headings
        (atx_heading) @heading
        (setext_heading) @heading

        ; Bold Text (Strong Emphasis)
        (strong) @strong

        ; Italic Text (Emphasis)
        (emph) @emphasis

        ; Code Blocks
        (fenced_code_block) @code_block
        (indented_code_block) @code_block

        ; Inline Code
        (code_span) @code

        ; Links
        (link) @link

        ; Images
        (image) @image

        ; Lists
        (list_item) @list_item

        ; Block Quotes
        (block_quote) @blockquote

        ; Thematic Breaks
        (thematic_break) @thematic_break
        """
        )

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

        # Blockquote format
        blockquote_format = QTextCharFormat()
        blockquote_format.setForeground(QColor("darkGray"))
        blockquote_format.setFontItalic(True)

        # Thematic break format
        thematic_break_format = QTextCharFormat()
        thematic_break_format.setForeground(QColor("gray"))

        # Map node types to formats
        self.formats = {
            "heading": heading_format,
            "strong": strong_format,
            "emphasis": emphasis_format,
            "code": code_format,
            "code_block": code_format,
            "link": link_format,
            "image": image_format,
            "list_item": list_format,
            "blockquote": blockquote_format,
            "thematic_break": thematic_break_format,
            # Add other mappings as needed...
        }

        # Parse the initial document
        self.parse_document()

        # Reparse and rehighlight when the document changes
        self.document().contentsChanged.connect(self.rehighlight)

    def parse_document(self):
        """Parse the entire document and build the syntax tree."""
        text = self.document().toPlainText()
        self.tree = self.parser.parse(bytes(text, "utf-8"))
        self.byte_to_char = self.build_byte_to_char_map(text)

    def rehighlight(self):
        """Reparse the document and rehighlight."""
        self.parse_document()
        super().rehighlight()

    def highlightBlock(self, text):
        block = self.currentBlock()
        block_start = block.position()
        block_length = block.length()
        block_end = block_start + block_length

        # Query the syntax tree for nodes overlapping with this block
        captures = self.query.captures(self.tree.root_node)

        for node, capture_name in captures:
            start_byte = node.start_byte
            end_byte = node.end_byte

            start_char = self.byte_to_char.get(start_byte)
            end_char = self.byte_to_char.get(end_byte)

            if start_char is None or end_char is None:
                continue

            # Check if the node overlaps with the current block
            if end_char <= block_start or start_char >= block_end:
                continue  # Node is outside the current block

            # Calculate the overlap between node and block
            relative_start = max(start_char, block_start) - block_start
            relative_end = min(end_char, block_end) - block_start
            length = relative_end - relative_start

            if length > 0:
                fmt = self.formats.get(capture_name)
                if fmt:
                    self.setFormat(relative_start, length, fmt)

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

    def build_byte_to_char_map(self, text):
        byte_to_char = {}
        byte_index = 0
        char_index = 0
        while char_index < len(text):
            char = text[char_index]
            char_bytes = char.encode("utf-8")
            for _ in char_bytes:
                byte_to_char[byte_index] = char_index
                byte_index += 1
            char_index += 1
        # Map the final byte index to the end of the text
        byte_to_char[byte_index] = char_index
        return byte_to_char
