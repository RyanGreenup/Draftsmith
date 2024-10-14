import re
from markdown import Markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.inlinepatterns import InlineProcessor
from xml.etree.ElementTree import Element
from py_asciimath.translator.translator import ASCIIMath2Tex

# This is too slow to use in a GUI application
# Look at a faster parser


class AsciiMathProcessor(Preprocessor):
    ASCIIMATH_BLOCK_RE = re.compile(
        r"\[asciimath\]\n\+\+\+\+\n(.*?)\n\+\+\+\+", re.DOTALL
    )

    def run(self, lines):
        text = "\n".join(lines)
        if not re.search(AsciiMathProcessor.ASCIIMATH_BLOCK_RE, text):
            return lines
        new_text = []

        # Iterate over all matches
        for match in AsciiMathProcessor.ASCIIMATH_BLOCK_RE.finditer(text):
            # Capture the content
            captured_math = match.group(1).strip()
            # Convert to TeX (hypothetical conversion)
            ascii_to_tex = ASCIIMath2Tex(log=False, inplace=True)
            tex_eq: str = ascii_to_tex.translate(
                captured_math, displaystyle=False, from_file=False, pprint=False
            )  # type: ignore
            # Replace display formula delimiters
            tex_eq = tex_eq.replace(r"\[", "\n$$\n").replace(r"\]", "\n$$\n")
            new_text.append(f"<p>{tex_eq}</p>")

        # Replace the matched blocks with the converted HTML
        text = AsciiMathProcessor.ASCIIMATH_BLOCK_RE.sub(
            lambda x: "\n".join(new_text), text
        )

        return text.splitlines()


class AsciiMathInlineProcessor(InlineProcessor):
    STEM_PATTERN = r'stem:\[(.*?)\]'

    def __init__(self, markdown_instance):
        super().__init__(AsciiMathInlineProcessor.STEM_PATTERN, markdown_instance)

    def handleMatch(self, m, data):
        captured_math = m.group(1)
        ascii_to_tex = ASCIIMath2Tex(log=False, inplace=True)
        tex_eq = ascii_to_tex.translate(
            captured_math, displaystyle=False, from_file=False, pprint=False
        )
        # Construct <span> element to hold converted math
        span = Element('span')
        span.text = f"${tex_eq}$"  # Use inline math delimiters
        return span, m.start(0), m.end(0)


class AsciiMathExtension(Extension):
    def extendMarkdown(self, md):
        # Register the preprocessor for block conversions
        md.preprocessors.register(AsciiMathProcessor(md), "ascii_math_block", 175)
        # Register the inline pattern for inline conversions
        md.inlinePatterns.register(AsciiMathInlineProcessor(md), "ascii_math_inline", 175)


# Example usage with Markdown
if __name__ == "__main__":
    md_text = """
Before inline math stem:[sqrt(4) = 2] and after.

[asciimath]
++++
sqrt(4) = 2
++++
"""

    md = Markdown(extensions=[AsciiMathExtension()])
    html = md.convert(md_text)
    print(html)

