It seems that code inside a list item does not correctly syntaxh highlight. I believe this is due to preceeding whitespace. For example the following has syntax highlighting:


```rust
println!("Some Exemplar Code");
```

But the following does not:


1. Code Block

    ```rust
    println!("Some Exemplar Code that should be under and ordered list");
    ```

Fix the code so syntax highlighting correctly occurs regardless of whitespace characters.


I believe this is related to the code:


```python
        # Code format
        codeFormat = QTextCharFormat()
        codeFormat.setFontFamily("Courier")
        codeFormat.setForeground(QColor("darkGreen"))
        self.highlightingRules.append((QRegularExpression("`[^`]+`"), codeFormat))
        self.highlightingRules.append((QRegularExpression("^```.*"), codeFormat))
```


/// details | Some summary
Some content
///



$$
\oint_\gamma \implies \overrightarrow{v} = \begin{bmatrix} 1 \\ 2 \\ 3 \end{bmatrix}
$$
