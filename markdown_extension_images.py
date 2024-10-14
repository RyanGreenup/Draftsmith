import re
from markdown import Markdown
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
from xml.etree.ElementTree import Element

# Pattern to match the image syntax with attributes
IMAGE_WITH_ATTR_PATTERN = r"!\[([^\]]*)\]\(([^)]+)\)\s*\{([^}]+)\}"


def parse_attrs(attr_string):
    """Parse the attribute string into a dictionary."""
    attrs = {}
    # Split the attribute string by spaces and then by '='
    for attr in attr_string.split():
        key, value = attr.split("=")
        attrs[key.strip()] = value.strip()
    return attrs


class ImageWithAttrInlineProcessor(InlineProcessor):
    def handleMatch(self, m, data):
        alt_text, src, attr_string = m.groups()
        img = Element("img")
        img.set("src", src)
        img.set("alt", alt_text)

        # Parse and set image attributes
        attributes = parse_attrs(attr_string)
        for attr, value in attributes.items():
            img.set(attr, value)

        return img, m.start(0), m.end(0)


class ImageWithAttrExtension(Extension):
    """
    An extension to add attributes to markdown images.

    Notably this allows including images with attributes like width and height.
    consistently with the pandoc syntax:

    ![Alt text](image.png){ width=50% height=100px }

    <img src="image.png" alt="Alt text" width="50%" height="100px">
    """

    def extendMarkdown(self, md):
        # Register the inline pattern with the markdown instance
        md.inlinePatterns.register(
            ImageWithAttrInlineProcessor(IMAGE_WITH_ATTR_PATTERN, md),
            "image_with_attr",
            175,
        )


def makeExtension(**kwargs):
    return ImageWithAttrExtension(**kwargs)


# Usage example
if __name__ == "__main__":
    md_text = "![Alt text](image.png){ width=50% height=100px }"
    md = Markdown(extensions=[ImageWithAttrExtension()])
    html = md.convert(md_text)
    print(html)
