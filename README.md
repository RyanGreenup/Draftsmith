# Draftsmith

A markdown editor written with PyQt6. It implements mathematics, custom CSS, a command palette, popup previews for math and basic vim bindings.

The goal is to write something with a open source with a simple code base that can be used in place of Obsidian or VSCode. [^1]

![](./screenshot.png)

[^1]: VSCode is great, but a popup preview for math would be nice. Obsidian is great, but it's not open source.

# Installation

In the future this will be packaged with Poetry and allow for install with `pipx`. For now, you can clone the repo:

```bash
cd $(mktemp -d)
git clone https://github.com/RyanGreenup/Draftsmith
cd Draftsmith
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py --css github-pandoc.css  /home/ryan/Notes/slipbox/index.md --dir ~/Notes/
```

