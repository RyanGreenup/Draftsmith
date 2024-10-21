- Pallette
  - Specific Palettes
      - [X] Command
      - [X] Open Files
          - Preview file in a splitter
      - Open Buffers
- [ ] Preview Images
- Katex
    - [ ] Include a local copy of the javascript
    - Convert the math environments to an SVG separately to reduce dependence
  - Features
      - Recall the last Palette
- Follow Links
    - https://www.perplexity.ai/search/in-pyqt6-how-to-map-hyperlinks-_FfaUbMsTr.M7kak4.ZxEA
- Insert Links
- Search
    - FTS
        - Whoosh
        - Tantivy
        - DuckDB
        - Xapian
    - Semantic Search
- FZF Open from Pallete
- Image Preview
- YAML Config
    - Web Security
    - Local KaTeX
        - markdown_utils.py
    - Pull Local KaTeX Automatically (if not present), Requires npm
- Markdown Extensions
    - Footnotes
    - Wikilinks
    -
- [ ] Handle broken symlinks
- [ ] Consider storing the katex as an attribute to reduce load times
    - Store the entire html skeleton in the preview or Markdown object
- WYSIWYM
    - Permit Toggleable:
        - Inline Images in the editor
        - Inline Math for all equations (not just popup)
    - Enter on a link should open that link in the same way that a hyperlink does
- Opening Links
    - Links should first check to see if a tab is already open with that target
    - Behaviour should be shared between WYSIWYM and Clicking the link in the preview
    - Insert
        - Handle Relative links from the current focused page :(
- More markdown extensions
    - [Library Reference — Python-Markdown 3.7 documentation](https://python-markdown.github.io/reference/#markdown)
    - [Extensions — Python-Markdown 3.7 documentation](https://python-markdown.github.io/extensions/)
    - [Markdown in HTML — Python-Markdown 3.7 documentation](https://python-markdown.github.io/extensions/md_in_html/)
    - [Footnotes — Python-Markdown 3.7 documentation](https://python-markdown.github.io/extensions/footnotes/)
    - [Attribute Lists — Python-Markdown 3.7 documentation](https://python-markdown.github.io/extensions/attr_list/)
    - [Arithmatex - PyMdown Extensions Documentation](https://facelessuser.github.io/pymdown-extensions/extensions/arithmatex/)

- Treesitter not Regex
- Wikilinks
- Remember split after following links
- Visit Tab instead
- As it stands index.md doesn't work.
- Config Option
    - Open New tab when follow link vs follow link in current tab
- Wikilinks
- Databases
    - Wikilinks to ID
    - DuckDB with ODBC
        - Optional support for postgres
- Datatables could be nice
    - Native Tables would be even nicer
- Allow Default view for split as opposed to overlay
- Visiting tab fails if base name matches

- Links
    - Currently links are resolved from the root of the notes directory
         - I could change this to resolve them relative to the current file, but this is simpler in terms of:
              - Inserting links from vim (e.g. resolve from cwd)
              - Following links with the code base logic (e.g. resolve from cwd)
              - Moving files makes it easier to update links
    - [ ] Slashes should be automatically replaced for the `os.path.sep`
- FTS
    - Should only index if the file hash changes
    - Use the same file open logic as insert link etc.
    - Progress bar for the user would be nice
        - Atleast a toast notification
- Paths
    - Should images be relative to the file or the notes directory
        - Currently they are relative to the file
    - Implement a config option for relative paths
        - Change each call to `setHtml` to use the current file like so:

            ```python
            self.preview.setHtml(html, QUrl.fromLocalFile(self.current_file))
            # If dir add trailing slash
            self.preview.setHtml(html, QUrl.fromLocalFile(file_dir + os.path.sep))
            ```
- Titles
    - The first heading should be the displayed title in everything, not the filename
- Preview
    - Links in Palettes
        - Should they still open in the original window?
            - Or just outright disable?
- Sync Scroll
- Images
  - AI Image Generation
  - Image Annotation with LLava
      - Add to Database as AI description
  - Image Search
      - Using Semantic Space
          - Or Descriptions :shrug:


## Next

- Semantic Search
- RAG
- Better Vim
- Display inline mathematics and images
- Toaster Notifications
    - [ ] Wikilinks
    - [ ] FTS
- Progress Bar for FTS
    - [ ] Inherit from Toast



## DONE
- Ctrl-K should insert a wikilink if so configured
    - Only if directories can be supported

