import os
import markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
import re

# TODO this requires some the math handling.


class IncludeFilePreprocessor(Preprocessor):
    INCLUDE_RE = re.compile(r'!\[\[([^\]]+)\]\]')

    def __init__(self, md, base_path='.'):
        super().__init__(md)
        self.base_path = base_path

    def run(self, lines):
        new_lines = []
        for line in lines:
            m = self.INCLUDE_RE.search(line)
            if m:
                file_name = m.group(1) + '.md'
                file_path = os.path.join(self.base_path, file_name)

                if os.path.isfile(file_path):
                    # Read the contents of the file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()

                    # Create a new Markdown instance and parse the included file's content
                    included_md = markdown.Markdown(extensions=self.md.registeredExtensions)
                    print(file_content)
                    included_html = included_md.convert(file_content)

                    # Add the parsed HTML to new_lines
                    new_lines.append(included_html)
                else:
                    new_lines.append(f'**Error:** Unable to find file `{file_name}`.')
            else:
                new_lines.append(line)
        return new_lines


class IncludeFileExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {
            'base_path': ['.', 'Base path for including files'],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        base_path = self.getConfig('base_path')
        md.preprocessors.register(
            IncludeFilePreprocessor(md, base_path=base_path),
            'include_file',
            25
        )


def makeExtension(**kwargs):
    return IncludeFileExtension(**kwargs)


# Usage Example:
if __name__ == '__main__':
    md_text = """
    This is a markdown example.

    ![[example]]

    More text here.
    """

    # Initialize with the tables extension explicitly
    md = markdown.Markdown(extensions=[
        'tables', IncludeFileExtension(base_path='.')
    ])
    html = md.convert(md_text)
    print(html)

