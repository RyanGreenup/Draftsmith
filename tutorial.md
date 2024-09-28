# Markdown Editor with Live Preview: A Tutorial Walkthrough

This tutorial will guide you through understanding the code for a Markdown editor with live preview, built using PyQt6 and Python. We'll break down the main components and explain how they work together.

The minimum working example is contained in `~/Notes/codechunks/pyqt6-markdown-editor`
## Introduction

This is a walk through of a basic Markdown editor in PyQt6. The left pane is an editor and the right side is a preview using the builtin python `markdown` library and the `pymdown-extension.superfences` library for better handling of code blocks.

## Main Components

The application consists of three main classes:

1. `MarkdownHighlighter`: Provides syntax highlighting for the Markdown editor.
2. `MarkdownEditor`: The main widget containing the editor and preview panes.
3. `MainWindow`: The application's main window that hosts the MarkdownEditor.

## MarkdownHighlighter Class

The `MarkdownHighlighter` class deals with syntax highlighting within the Markdown editor. It inherits from `QSyntaxHighlighter`.

It does this by

    1. Define highlighting rules for Markdown elements (headings, bold, italic...)
        2. Via regex not treesitter though.
    3. Applies different text formats based on those rules

## MarkdownEditor Class

The `MarkdownEditor` class contains the editor and the preview, it uses:


1. `QTextEdit` for the Markdown input.
2. `QWebEngineView` for the HTML preview.
3. Defines and `update_preview` method to update the preview when the text changes.
4. Supports custom CSS for styling the preview.

## MainWindow Class

The `MainWindow` class is a container for the `MarkdownEditor` widget.


## Code Structure

To better understand the organization of the code, here's a tree of the logic:

- Main execution (`if __name__ == "__main__":`)
  - Parse command-line arguments (`argparse.ArgumentParser()`)
  - Create QApplication (`QApplication(sys.argv)`)
  - Create MainWindow (`MainWindow()`)
    - Initialize the markdown editor (`__init__`)
      - Create MarkdownEditor (`MarkdownEditor(css_file=args.css)`)
        - Create QTextEdit (editor) (`QTextEdit()`)
        - Create QWebEngineView (preview) (`QWebEngineView()`)
        - Create MarkdownHighlighter (`MarkdownHighlighter(self.editor.document())`)
          - Define highlighting rules (`__init__`)
        - Set up layout with QSplitter (`QSplitter(Qt.Orientation.Horizontal)`)
        - Connect signals (`textChanged.connect(self.update_preview)`)
    - Set MarkdownEditor as central widget (`setCentralWidget()`)
  - Show MainWindow (`window.show()`)
  - Start application event loop (`app.exec()`)

## Complete Walkthrough

### Imports and Basic Logic
#### Imports
```python
import sys
import argparse
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QSplitter,
    QDialog,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QFont,
    QColor,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

import markdown
from pygments.formatters import HtmlFormatter
```
#### Main Window
```python
class MainWindow(QMainWindow):
    """Main window containing the Markdown editor."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown Editor with Preview")
        self.resize(800, 600)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Markdown Editor with Preview")
    parser.add_argument(
        "--css", type=str, help="Path to a CSS file for the markdown preview"
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

```


### Create the Markdown Editor and Preview
#### Initial Viewer

```python
class MainWindow(QMainWindow):
    """Main window containing the Markdown editor."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown Editor with Preview")
        self.resize(800, 600)

```

```python
class MarkdownEditor(QWidget):
    """A QWidget containing a Markdown editor with live preview."""

    def __init__(self, css_file=None):
        super().__init__()
        self.css_file = css_file

        # Create the editor and preview widgets
        self.editor = QTextEdit()
        self.preview = QWebEngineView()

        # Create a splitter to divide editor and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setSizes([300, 300])

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        # Connect signals
        self.editor.textChanged.connect(self.update_preview)

    def update_preview(self):
        """Update the Markdown preview."""
        # Generate the markdown with extensions
        html_body = markdown.markdown(self.editor.toPlainText())
        self.preview.setHtml(html)

```


#### Add KaTeX Support

```python
class MarkdownEditor(QWidget):
    """A QWidget containing a Markdown editor with live preview."""

    def __init__(self):
        # As Above

    def update_preview(self):
        """Update the Markdown preview."""
        text = self.editor.toPlainText()

        # Generate the markdown with extensions
        html_body = markdown.markdown(
            text,
            extensions=[
                "markdown_katex",
                "codehilite",
                "fenced_code",
                "wikilinks",
                "footnotes",
                "md_in_html",
                "tables",
                # [^2] This extension is needed for indented code blocks, like under lists
                "pymdownx.superfences",
                # Admonition blocks [^1]
                "pymdownx.blocks.details",
                "admonition",
                "toc",
            ],
        )

        # Get the CSS styles for code highlighting and additional CSS if provided
        css_styles = ""
        if self.css_file:
            with open(self.css_file, "r") as file:
                css_styles += file.read()
        formatter = HtmlFormatter()
        css_styles += formatter.get_style_defs(".codehilite")

        # Build the full HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
            {css_styles}
            </style>
            <!-- KaTeX CSS -->
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.15.1/dist/katex.min.css" crossorigin="anonymous">
        </head>
        <body>
            {html_body}
            <!-- KaTeX JS -->
            <script defer src="https://cdn.jsdelivr.net/npm/katex@0.15.1/dist/katex.min.js" crossorigin="anonymous"></script>
            <script defer src="https://cdn.jsdelivr.net/npm/katex@0.15.1/dist/contrib/auto-render.min.js" crossorigin="anonymous"></script>
            <script>
            document.addEventListener("DOMContentLoaded", function() {{
                renderMathInElement(document.body, {{
                    delimiters: [
                      {{left: "$$", right: "$$", display: true}},
                      {{left: "$", right: "$", display: false}}
                    ]
                }});
            }});
            </script>
        </body>
        </html>
        """
        self.preview.setHtml(html)
```

### Add Syntax Highlighting to the Editor

#### Class for Markdown Highlighter

```python
class MarkdownHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Markdown code in QTextEdit."""

    def __init__(self, document):
        super().__init__(document)
        # Define the highlighting rules
        self.highlightingRules = []

        # Heading format
        headingFormat = QTextCharFormat()
        headingFormat.setFontWeight(QFont.Weight.Bold)
        headingFormat.setForeground(QColor("blue"))
        # Headings: lines starting with one or more '#' characters
        self.highlightingRules.append((QRegularExpression("^#{1,6} .+"), headingFormat))

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
        for pattern, format in self.highlightingRules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                index = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(index, length, format)
```


#### Add the Highlighter to the Editor


Simply add:

```python
self.highlighter = MarkdownHighlighter(self.editor.document())`
```

To the `MarkdownEditor` constructor:


```python
class MarkdownEditor(QWidget):
    """A QWidget containing a Markdown editor with live preview."""

    def __init__(self, css_file=None):
        super().__init__()
        self.css_file = css_file

        # Create the editor and preview widgets
        self.editor = QTextEdit()
        self.preview = QWebEngineView()

        # Apply syntax highlighting to the editor
        self.highlighter = MarkdownHighlighter(self.editor.document())

        # Create a splitter to divide editor and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setSizes([300, 300])

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        # Connect signals
        self.editor.textChanged.co
```


### All the code

```python
import sys
import argparse
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QSplitter,
    QDialog,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import (
    QSyntaxHighlighter,
    QTextCharFormat,
    QFont,
    QColor,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

import markdown
from pygments.formatters import HtmlFormatter


class MarkdownHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Markdown code in QTextEdit."""

    def __init__(self, document):
        super().__init__(document)
        # Define the highlighting rules
        self.highlightingRules = []

        # Heading format
        headingFormat = QTextCharFormat()
        headingFormat.setFontWeight(QFont.Weight.Bold)
        headingFormat.setForeground(QColor("blue"))
        # Headings: lines starting with one or more '#' characters
        self.highlightingRules.append((QRegularExpression("^#{1,6} .+"), headingFormat))

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
        for pattern, format in self.highlightingRules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                index = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(index, length, format)


class MarkdownEditor(QWidget):
    """A QWidget containing a Markdown editor with live preview."""

    def __init__(self, css_file=None):
        super().__init__()
        self.css_file = css_file

        # Create the editor and preview widgets
        self.editor = QTextEdit()
        self.preview = QWebEngineView()

        # Apply syntax highlighting to the editor
        self.highlighter = MarkdownHighlighter(self.editor.document())

        # Create a splitter to divide editor and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setSizes([300, 300])

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        # Connect signals
        self.editor.textChanged.connect(self.update_preview)

    def update_preview(self):
        """Update the Markdown preview."""
        text = self.editor.toPlainText()

        # Generate the markdown with extensions
        html_body = markdown.markdown(
            text,
            extensions=[
                "markdown_katex",
                "codehilite",
                "fenced_code",
                "wikilinks",
                "footnotes",
                "md_in_html",
                "tables",
                # [^2] This extension is needed for indented code blocks, like under lists
                "pymdownx.superfences",
                # Admonition blocks [^1]
                "pymdownx.blocks.details",
                "admonition",
                "toc",
            ],
        )

        # Get the CSS styles for code highlighting and additional CSS if provided
        css_styles = ""
        if self.css_file:
            with open(self.css_file, "r") as file:
                css_styles += file.read()
        formatter = HtmlFormatter()
        css_styles += formatter.get_style_defs(".codehilite")

        # Build the full HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
            {css_styles}
            </style>
            <!-- KaTeX CSS -->
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.15.1/dist/katex.min.css" crossorigin="anonymous">
        </head>
        <body>
            {html_body}
            <!-- KaTeX JS -->
            <script defer src="https://cdn.jsdelivr.net/npm/katex@0.15.1/dist/katex.min.js" crossorigin="anonymous"></script>
            <script defer src="https://cdn.jsdelivr.net/npm/katex@0.15.1/dist/contrib/auto-render.min.js" crossorigin="anonymous"></script>
            <script>
            document.addEventListener("DOMContentLoaded", function() {{
                renderMathInElement(document.body, {{
                    delimiters: [
                      {{left: "$$", right: "$$", display: true}},
                      {{left: "$", right: "$", display: false}}
                    ]
                }});
            }});
            </script>
        </body>
        </html>
        """
        self.preview.setHtml(html)


class MainWindow(QMainWindow):
    """Main window containing the Markdown editor."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Markdown Editor with Preview")
        self.resize(800, 600)

        # Initialize the Markdown editor
        self.markdown_editor = MarkdownEditor(css_file=args.css)
        self.setCentralWidget(self.markdown_editor)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Markdown Editor with Preview")
    parser.add_argument(
        "--css", type=str, help="Path to a CSS file for the markdown preview"
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


## Footnotes
# [^1]: https://facelessuser.github.io/pymdown-extensions/extensions/blocks/plugins/details/
# [^2]: https://github.com/mkdocs/mkdocs/issues/282
```

