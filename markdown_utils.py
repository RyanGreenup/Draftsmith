from pygments.formatters import HtmlFormatter
import markdown
from pathlib import Path
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.postprocessors import Postprocessor
import re

# Define a regular expression to match both inline and block math
INLINE_MATH_PATTERN = re.compile(r'\$(.+?)\$')
BLOCK_MATH_PATTERN = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)

class PreserveMathExtension(Extension):
    def extendMarkdown(self, md):
        md.registerExtension(self)
        md.preprocessors.register(MathPreprocessor(md), 'math_preprocessor', 25)
        md.postprocessors.register(MathPostprocessor(md), 'math_postprocessor', 25)

class MathPreprocessor(Preprocessor):
    def run(self, lines):
        self.math_blocks = []
        new_lines = []
        for line in lines:
            line = re.sub(BLOCK_MATH_PATTERN, self._store_math_block, line)
            line = re.sub(INLINE_MATH_PATTERN, self._store_inline_math, line)
            new_lines.append(line)
        return new_lines

    def _store_math_block(self, match):
        math = match.group(0)
        self.math_blocks.append(math)
        return f':::MATH_BLOCK_{len(self.math_blocks) - 1}:::'

    def _store_inline_math(self, match):
        math = match.group(0)
        self.math_blocks.append(math)
        return f':::MATH_INLINE_{len(self.math_blocks) - 1}:::'

class MathPostprocessor(Postprocessor):
    def run(self, text):
        # Restore the placeholders with original math
        for i, math in enumerate(self.md.preprocessors['math_preprocessor'].math_blocks):
            placeholder_block = f':::MATH_BLOCK_{i}:::'
            placeholder_inline = f':::MATH_INLINE_{i}:::'
            text = text.replace(placeholder_block, math)
            text = text.replace(placeholder_inline, math)
        return text

class Markdown:
    def __init__(
        self, text: str, css_path: Path | None = None, dark_mode: bool = False
    ):
        self.css_path = css_path
        self.dark_mode = dark_mode

        # Replace double backslashes with triple backslashes to avoid escaping issues with math
        two_backslashes = "\\" + "\\"
        three_backslashes = two_backslashes + "\\"
        text = text.replace(two_backslashes, three_backslashes)
        self.text = text

    def make_html(self) -> str:
        # Generate the markdown with extensions
        html_body = markdown.markdown(
            self.text,
            extensions=[
                # "markdown_katex",
                PreserveMathExtension(),
                "codehilite",
                "fenced_code",
                "tables",
                "pymdownx.superfences",
                "pymdownx.blocks.details",
                "admonition",
                "toc",
            ],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "linenums": False,
                    "guess_lang": False,
                }
            },
        )


        html_body = "<pre>" + html_body + "</pre>"
        return html_body

    def build_css(self) -> str:
        css_styles = ""
        if self.css_path:
            with open(self.css_path, "r") as file:
                css_styles += file.read()

        # Add Pygments CSS for code highlighting
        formatter = HtmlFormatter(style="default" if not self.dark_mode else "monokai")
        pygments_css = formatter.get_style_defs(".highlight")

        # Modify Pygments CSS for dark mode
        if self.dark_mode:
            pygments_css = pygments_css.replace(
                "background: #f8f8f8", "background: #2d2d2d"
            )
            pygments_css += """
            .highlight {
                background-color: #2d2d2d;
            }
            .highlight pre {
                background-color: #2d2d2d;
            }
            .highlight .hll {
                background-color: #2d2d2d;
            }
            """

        css_styles += pygments_css

        # Add dark mode styles if enabled
        if self.dark_mode:
            dark_mode_styles = """
            body {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            a {
                color: #3794ff;
            }
            code {
                background-color: #2d2d2d;
            }
            .katex { color: #d4d4d4; }
            """
            css_styles += dark_mode_styles
        return css_styles

    def build_html(self, content_editable=False) -> str:
        html_body = self.make_html()
        css_styles = self.build_css()
        content_editable_attr = 'contenteditable="true"' if content_editable else ""

        # Add dark mode styles for KaTeX
        katex_dark_mode_styles = (
            """
        .katex { color: #d4d4d4; }
        """
            if self.dark_mode
            else ""
        )

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
            {css_styles}
            {katex_dark_mode_styles}
            </style>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.15.1/dist/katex.min.css" crossorigin="anonymous">
        </head>
        <body {content_editable_attr}>
            {html_body}
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
        return html
