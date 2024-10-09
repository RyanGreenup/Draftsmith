from pygments.formatters import HtmlFormatter
import shutil
import markdown
import subprocess
import os
from pathlib import Path
import re
from markdown.extensions.wikilinks import WikiLinkExtension

INLINE_MATH_PATTERN = re.compile(r"\$(.+?)\$")
BLOCK_MATH_PATTERN = re.compile(r"\$\$([\s\S]+?)\$\$")


class Markdown:
    def __init__(
        self, text: str, css_path: Path | None = None, dark_mode: bool = False
    ):
        self.css_path = css_path
        self.dark_mode = dark_mode
        self.text = text
        self.math_blocks = []

    def _preserve_math(self, match):
        math = match.group(0)
        placeholder = f"MATH_PLACEHOLDER_{len(self.math_blocks)}"
        self.math_blocks.append(math)
        return placeholder

    def _restore_math(self, text):
        for i, math in enumerate(self.math_blocks):
            placeholder = f"MATH_PLACEHOLDER_{i}"
            text = text.replace(placeholder, math)
        return text

    def make_html(self) -> str:
        # Preserve math environments
        text = BLOCK_MATH_PATTERN.sub(self._preserve_math, self.text)
        text = INLINE_MATH_PATTERN.sub(self._preserve_math, text)

        # Generate the markdown with extensions
        html_body = markdown.markdown(
            text,
            extensions=[
                "codehilite",
                "fenced_code",
                "tables",
                "pymdownx.superfences",
                "pymdownx.blocks.details",
                "admonition",
                "toc",
                # TODO Make base_url configurable to share between preview and editor
                WikiLinkExtension(base_url=os.getcwd(), end_url=".md"),
            ],
            extension_configs={
                "codehilite": {
                    "css_class": "highlight",
                    "linenums": False,
                    "guess_lang": False,
                }
            },
        )

        # Restore math environments
        html_body = self._restore_math(html_body)

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

    def build_html(self, content_editable=False, local_katex=True) -> str:
        html_body = self.make_html()
        css_styles = self.build_css()
        content_editable_attr = 'contenteditable="true"' if content_editable else ""

        katex_dark_mode_styles = """
        .katex { color: #d4d4d4; }
        """ if self.dark_mode else ""

        katex_min_css, katex_min_js, auto_render_min_js = get_katex_html(local=local_katex)

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
            {css_styles}
            {katex_dark_mode_styles}
            </style>
            {katex_min_css}
        </head>
        <body {content_editable_attr}>
            {html_body}
            {katex_min_js}
            {auto_render_min_js}
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


def install_katex():
    current_dir = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    os.makedirs("assets", exist_ok=True)
    os.chdir("assets")
    subprocess.run(["npm", "install", "katex"], check=True)
    os.chdir(current_dir)


def get_katex_html(local: bool = True) -> tuple[str, str, str]:
    if local:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(f"{dir_path}/assets/node_modules/katex/dist/katex.min.css", "r") as f:
            katex_min_css = f.read()
        with open(f"{dir_path}/assets/node_modules/katex/dist/katex.min.js", "r") as f:
            katex_min_js = f.read()
        with open(f"{dir_path}/assets/node_modules/katex/dist/contrib/auto-render.min.js", "r") as f:
            auto_render_min_js = f.read()
        
        return (
            f"<style>{katex_min_css}</style>",
            f"<script>{katex_min_js}</script>",
            f"<script>{auto_render_min_js}</script>"
        )
    else:
        url = "https://cdn.jsdelivr.net/npm/katex@0.15.1/dist/"
        katex_min_css = f'<link rel="stylesheet" href="{url}katex.min.css" crossorigin="anonymous">'
        katex_min_js = f'<script defer src="{url}katex.min.js" crossorigin="anonymous"></script>'
        auto_render_min_js = f'<script defer src="{url}contrib/auto-render.min.js" crossorigin="anonymous"></script>'
        return katex_min_css, katex_min_js, auto_render_min_js
