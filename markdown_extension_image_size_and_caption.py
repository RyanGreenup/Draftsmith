import re
from markdown import Markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
from xml.etree.ElementTree import Element

# Pattern to match the image syntax with optional attributes
IMAGE_WITH_ATTR_PATTERN = r"!\[([^\]]*)\]\(([^)]+)\)(?:\s*\{([^}]+)\})?"


def parse_attrs(attr_string):
    """Parse the attribute string into a dictionary."""
    attrs = {}
    if attr_string:
        for attr in attr_string.split():
            if "=" in attr:
                key, value = attr.split("=")
                attrs[key.strip()] = value.strip()
    return attrs


class FigureInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        alt_text, src, attr_string = m.groups()

        # Parse attributes
        attributes = parse_attrs(attr_string)
        has_attrs = bool(attributes)

        # Create the img element
        img = Element("img")
        img.set("src", src)
        if alt_text is not None:
            img.set("alt", alt_text)

        # Determine if we need a figure or just an img
        if (alt_text and has_attrs) or (alt_text):
            # Create the figure element
            figure = Element("figure")
            figcaption = None

            # Apply styles or attributes
            styles = []
            if "float" in attributes:
                float_value = attributes.pop("float")
                if float_value == "left":
                    styles.append("float: left; margin-right: 10px;")
                elif float_value == "right":
                    styles.append("float: right; margin-left: 10px;")
                elif float_value == "center":
                    styles.append(
                        "display: block; margin-left: auto; margin-right: auto;"
                    )

            for attr in ["width", "height"]:
                if attr in attributes:
                    styles.append(f"{attr}: {attributes[attr]}")

            # Set figure style if styles exist
            if styles:
                figure.set("style", " ".join(styles))

            # Add img and figure caption
            figure.append(img)
            if alt_text:
                figcaption = Element("figcaption")
                figcaption.text = alt_text
                figure.append(figcaption)

            return figure, m.start(0), m.end(0)
        else:
            # Handle an image with style attributes but no caption or figure
            styles = []
            for attr in ["width", "height"]:
                if attr in attributes:
                    styles.append(f"{attr}:{attributes[attr]}")

            if styles:
                img.set("style", " ".join(styles))

            if not alt_text:
                return img, m.start(0), m.end(0)
            else:
                # Wrap in paragraph if alt text exists without attributes
                p = Element("p")
                p.append(img)
                return p, m.start(0), m.end(0)


class ImageWithFigureExtension(Extension):
    def extendMarkdown(self, md):
        # Register the inline pattern with the markdown instance
        md.inlinePatterns.register(
            FigureInlineProcessor(IMAGE_WITH_ATTR_PATTERN, md), "figure_with_attr", 175
        )


def makeExtension(**kwargs):
    return ImageWithFigureExtension(**kwargs)


# Usage example
if __name__ == "__main__":
    tests = [
        "![A Descriptive caption for the image](image.png){ width=50% height=10% float=right }",
        "![A Descriptive caption for the image](image.png){ width=50% height=10% }",
        "![](image.png){ width=50% height=10% }",
        "![A Descriptive caption for the image](image.png)",
        "![](image.png)",
    ]

    md = Markdown(extensions=[ImageWithFigureExtension()])
    for test in tests:
        html = md.convert(test)
        print(html)
