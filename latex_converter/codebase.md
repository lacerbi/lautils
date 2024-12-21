# Codebase Documentation `latex_converter`

## File Contents

### __init__.py

```
from .main import clean_latex_file
```

### converters.py

```
import re
# ./converters.py

def apply_inline_formats(text):
    """
    Applies inline formatting rules:
    - \emph{...}, \textit{...} -> *...*
    - \textbf{...} -> **...**
    - \textsc{...} -> `...`

    Parameters
    ----------
    text : str
        The LaTeX content.

    Returns
    -------
    str
        The text with inline formats applied.
    """
    # \emph{...}, \textit{...} -> *...*
    emph_pattern = re.compile(r'\\(?:emph|textit)\{(.*?)\}')
    text = emph_pattern.sub(lambda m: "*" + m.group(1).strip() + "*", text)

    # \textbf{...} -> **...**
    bold_pattern = re.compile(r'\\textbf\{(.*?)\}')
    text = bold_pattern.sub(lambda m: "**" + m.group(1).strip() + "**", text)

    # \textsc{...} -> `...`
    textsc_pattern = re.compile(r'\\textsc\{(.*?)\}')
    text = textsc_pattern.sub(lambda m: "`" + m.group(1).strip() + "`", text)

    return text

def replace_maketitle(text, title, authors):
    """
    Replaces \maketitle with Markdown-formatted title and authors.

    Parameters
    ----------
    text : str
        The document content.
    title : str
        The extracted title.
    authors : str
        The extracted authors.

    Returns
    -------
    str
        Content with \maketitle replaced.
    """
    replacement = ""
    if title:
        replacement += f"# {apply_inline_formats(title)}\n\n"
    if authors:
        authors_clean = re.split(r'\\and|,', authors)
        authors_clean = [a.strip() for a in authors_clean if a.strip()]
        authors_md = ', '.join(authors_clean)
        replacement += f"**Authors:** {authors_md}\n\n"

    maketitle_pattern = re.compile(r'\\maketitle')
    return maketitle_pattern.sub(lambda m: replacement, text)

def replace_figures(text):
    """
    Replace figure environments with Markdown-style figure captions.

    Parameters
    ----------
    text : str
        The document content.

    Returns
    -------
    str
        Content with figures replaced.
    """
    figure_env = re.compile(r'\\begin\{figure.*?\}(.*?)\\end\{figure.*?\}', flags=re.DOTALL)

    def figure_repl(m):
        inner = m.group(1)
        captions = []

        cap_start_pattern = re.compile(r'\\caption\{')
        pos = 0
        while True:
            cmatch = cap_start_pattern.search(inner, pos)
            if not cmatch:
                break
            start = cmatch.end()
            brace_level = 1
            i = start
            while i < len(inner) and brace_level > 0:
                if inner[i] == '{':
                    brace_level += 1
                elif inner[i] == '}':
                    brace_level -= 1
                i += 1
            if brace_level == 0:
                caption_text = inner[start:i-1].strip()
                caption_text = re.sub(r'\\label\{[^}]+\}', '', caption_text).strip()
                captions.append(caption_text)
                pos = i
            else:
                print("Warning: Unbalanced braces in figure caption.")
                caption_text = inner[start:].strip()
                caption_text = re.sub(r'\\label\{[^}]+\}', '', caption_text).strip()
                captions.append(caption_text)
                break

        full_caption = ' '.join(captions).strip()
        full_caption = apply_inline_formats(full_caption)

        label_pattern = re.compile(r'\\label\{([^}]+)\}')
        labels = label_pattern.findall(inner)

        figure_markdown = "\n\n**Figure:** " + full_caption
        for label in labels:
            figure_markdown += f" \\label{{{label}}}"
        figure_markdown += "\n\n"

        return figure_markdown

    return figure_env.sub(figure_repl, text)

def replace_tables(text):
    """
    Replace table environments with Markdown tables. 
    If nested tabular environments are detected, the original LaTeX code is retained in a code block.

    Parameters
    ----------
    text : str
        The document content.

    Returns
    -------
    str
        Content with tables replaced by Markdown format (where possible).
    """
    table_env = re.compile(r'(\\begin\{table.*?\}.*?\\end\{table.*?\})', flags=re.DOTALL)

    def has_nested_tabulars(tex):
        open_tabulars = 0
        pos = 0
        while pos < len(tex):
            begin_match = re.search(r'\\begin\{tabular\}', tex[pos:])
            end_match = re.search(r'\\end\{tabular\}', tex[pos:])
            if begin_match:
                begin_pos = pos + begin_match.start()
            else:
                begin_pos = None
            if end_match:
                end_pos = pos + end_match.start()
            else:
                end_pos = None
            if begin_pos is not None and (end_pos is None or begin_pos < end_pos):
                open_tabulars += 1
                if open_tabulars > 1:
                    return True
                pos = begin_pos + len('\\begin{tabular}')
            elif end_pos is not None:
                open_tabulars -= 1
                pos = end_pos + len('\\end{tabular}')
            else:
                break
        return False

    def convert_tabular_to_markdown(inner):
        try:
            # Remove scalebox
            while True:
                scalebox_match = re.search(r'\\scalebox\{[^\}]*\}\{', inner)
                if not scalebox_match:
                    break
                inner = re.sub(r'\\scalebox\{[^\}]*\}\{(.*?)\}', r'\1', inner, flags=re.DOTALL)

            if has_nested_tabulars(inner):
                return None

            tabular_env = re.compile(r'\\begin\{tabular\}\{.*?\}(.*?)\\end\{tabular\}', flags=re.DOTALL)
            tabulars = list(tabular_env.finditer(inner))
            if not tabulars:
                return ""

            md_tables = []
            for tabular in tabulars:
                tabular_content = tabular.group(1)

                # Remove booktabs lines
                tabular_content = re.sub(r'\\toprule|\\midrule|\\bottomrule', '', tabular_content)
                tabular_content = re.sub(r'\\cmidrule\{[^\}]*\}', '', tabular_content)

                rows = re.split(r'\\\\', tabular_content)
                rows = [r.strip() for r in rows if r.strip()]

                if not rows:
                    continue

                table_rows = []
                for r in rows:
                    r = re.sub(r'\\textcolor\{[^\}]*\}\{(.*?)\}', r'\1', r)
                    r = re.sub(r'\\textbf\{(.*?)\}', r'**\1**', r)
                    r = re.sub(r'\\emph\{(.*?)\}', r'*\1*', r)

                    r = r.replace(r'\&', '&').replace(r'\\', '\\')
                    cells = [c.strip() for c in r.split('&')]
                    table_rows.append(cells)

                num_cols = len(table_rows[0])
                md_table = "\n\n| " + " | ".join(table_rows[0]) + " |\n"
                md_table += "| " + " | ".join(["---"] * num_cols) + " |\n"
                for row in table_rows[1:]:
                    if len(row) < num_cols:
                        row += [""] * (num_cols - len(row))
                    elif len(row) > num_cols:
                        row = row[:num_cols]
                    md_table += "| " + " | ".join(row) + " |\n"
                md_table += "\n\n"

                md_tables.append(md_table)

            return ''.join(md_tables)
        except Exception as e:
            print(f"Error during tabular conversion: {e}")
            return ""

    def remove_captions_and_labels(tex):
        out = ""
        start_idx = 0
        caption_pattern = re.compile(r'\\caption\{')
        while True:
            cmatch = caption_pattern.search(tex, start_idx)
            if not cmatch:
                break
            out += tex[start_idx:cmatch.start()]
            pos = cmatch.end()
            brace_level = 1
            while pos < len(tex) and brace_level > 0:
                if tex[pos] == '{':
                    brace_level += 1
                elif tex[pos] == '}':
                    brace_level -= 1
                pos += 1
            start_idx = pos
        out += tex[start_idx:]

        out = re.sub(r'\\label\{[^}]+\}', '', out)
        return out

    def table_repl(m):
        entire_table = m.group(1)

        # Extract captions
        captions = []
        pos = 0
        cap_start_pattern = re.compile(r'\\caption\{')
        while True:
            cmatch = cap_start_pattern.search(entire_table, pos)
            if not cmatch:
                break
            start = cmatch.end()
            brace_level = 1
            i = start
            while i < len(entire_table) and brace_level > 0:
                if entire_table[i] == '{':
                    brace_level += 1
                elif entire_table[i] == '}':
                    brace_level -= 1
                i += 1
            if brace_level == 0:
                caption_text = entire_table[start:i-1].strip()
                caption_text = re.sub(r'\\label\{[^}]+\}', '', caption_text).strip()
                captions.append(caption_text)
                pos = i
            else:
                print("Warning: Unbalanced braces in table caption.")
                caption_text = entire_table[start:].strip()
                caption_text = re.sub(r'\\label\{[^}]+\}', '', caption_text).strip()
                captions.append(caption_text)
                break

        full_caption = ' '.join(captions).strip()
        full_caption = apply_inline_formats(full_caption)

        label_pattern = re.compile(r'\\label\{([^}]+)\}')
        labels = label_pattern.findall(entire_table)

        markdown_table = convert_tabular_to_markdown(entire_table)

        if markdown_table is None:
            # Nested tabular detected
            print("Warning: Nested tabular environments detected. Retaining tabular content as LaTeX code.")
            tabulars = re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}', entire_table, flags=re.DOTALL)
            tabular_content = '\n'.join(tabulars)
            labels_str = ' '.join([f"\\label{{{label}}}" for label in labels])
            return f"\n\n**Table:** {full_caption} {labels_str}\n\n```latex\n{tabular_content}\n```\n\n"

        if not markdown_table:
            # Conversion failed or no tabulars found
            print("Warning: Table conversion failed or no tabulars found.")
            cleaned_table = remove_captions_and_labels(entire_table)
            labels_str = ' '.join([f"\\label{{{label}}}" for label in labels])
            return f"\n\n**Table:** {full_caption} {labels_str}\n\n```latex\n{cleaned_table}\n```\n\n"

        labels_str = ' '.join([f"\\label{{{label}}}" for label in labels])
        return f"\n\n**Table:** {full_caption} {labels_str}\n\n{markdown_table}\n"

    return table_env.sub(table_repl, text)

def replace_equations(text):
    """
    Replace equation environments with Markdown math block format.

    Parameters
    ----------
    text : str
        The document content.

    Returns
    -------
    str
        Content with equations replaced.
    """
    eq_env = re.compile(r'\\begin\{equation\}(.*?)\\end\{equation\}', flags=re.DOTALL)

    def eq_repl(m):
        eq_text = m.group(1).strip()
        eq_text = re.sub(r'(\\label\{[^}]+\})\s*', r'\1\n', eq_text)
        return "\n\n$$\n" + eq_text + "\n$$\n\n"

    return eq_env.sub(eq_repl, text)

def replace_headings(text):
    """
    Convert LaTeX sectioning commands to Markdown headings.

    Parameters
    ----------
    text : str
        The document content.

    Returns
    -------
    str
        Content with headings replaced by Markdown.
    """
    sec_pattern = re.compile(
        r'\\(section|subsection|subsubsection|paragraph|runningtitle)\*?\{(.*?)\}'
        r'(?:\s*\\label\{([^}]+)\})?', flags=re.DOTALL
    )

    def sec_repl(m):
        level_map = {
            "section": 1,
            "subsection": 2,
            "subsubsection": 3,
            "paragraph": 4,
            "runningtitle": 1
        }
        level = level_map.get(m.group(1), 2)
        title = m.group(2).strip()
        label = m.group(3)

        markdown = "\n\n" + "#" * level + " " + title
        if label:
            markdown += "\n\\label{" + label + "}"
        markdown += "\n\n"
        return markdown

    return sec_pattern.sub(sec_repl, text)

def replace_lists(text):
    """
    Convert LaTeX itemize and enumerate environments into Markdown lists.

    Parameters
    ----------
    text : str
        The document content.

    Returns
    -------
    str
        Content with lists replaced by Markdown lists.
    """
    enum_env = re.compile(r'\\begin\{enumerate\}(\[[^\]]*\])?(.*?)\\end\{enumerate\}', flags=re.DOTALL)
    def enum_repl(m):
        inner = m.group(2)
        items = re.split(r'\\item', inner)
        items = [i.strip() for i in items if i.strip()]
        result = "\n\n"
        for idx, it in enumerate(items, start=1):
            it = apply_inline_formats(it)
            result += f"{idx}. {it}\n"
        result += "\n"
        return result

    text = enum_env.sub(enum_repl, text)

    item_env = re.compile(r'\\begin\{itemize\}(\[[^\]]*\])?(.*?)\\end\{itemize\}', flags=re.DOTALL)
    def item_repl(m):
        inner = m.group(2)
        items = re.split(r'\\item', inner)
        items = [i.strip() for i in items if i.strip()]
        result = "\n\n"
        for it in items:
            it = apply_inline_formats(it)
            result += f"- {it}\n"
        result += "\n"
        return result

    text = item_env.sub(item_repl, text)
    text = re.sub(r'\\item\s+', '\n- ', text)
    return text
```

### file_utils.py

```
# ./file_utils.py
import os

def read_input(input_str):
    """
    Reads the input LaTeX content from a string or a file.

    Parameters
    ----------
    input_str : str
        If `input_str` contains newlines, it will be treated as raw LaTeX content.
        Otherwise, if it ends with '.tex', it will be read from that file.

    Returns
    -------
    tuple (str, str)
        A tuple containing:
        - The LaTeX content as a string.
        - The output file path as a string.
    """
    if isinstance(input_str, str) and '\n' in input_str:
        return input_str, "output.txt"
    else:
        if not input_str.endswith('.tex'):
            raise ValueError("Input file must have a .tex extension.")
        base, _ = os.path.splitext(input_str)
        output_path = f"{base}.txt"

        with open(input_str, 'r', encoding='utf-8') as infile:
            content = infile.read()
        return content, output_path

def write_output(document_content, output_path):
    """
    Writes the cleaned and converted content to the specified output file.

    Parameters
    ----------
    document_content : str
        The cleaned LaTeX content in Markdown-like format.
    output_path : str
        The path to the output file to write.

    Returns
    -------
    None
    """
    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write(document_content)
    print(f"Cleaned file has been written to: {output_path}")
```

### formats.py

```
# ./formats.py
import re

def remove_leftover_commands(text):
    """
    Remove specified leftover LaTeX commands and replace newline-related commands with double newlines.

    Parameters
    ----------
    text : str
        The document content.

    Returns
    -------
    str
        Content with leftover commands removed.
    """
    commands_to_remove = ['vspace', 'hspace', 'bigskip', 'smallskip', 'medskip', 'ignore', 'bibliographystyle']
    commands_to_replace_newline = ['newpage', 'pagebreak', 'linebreak', 'clearpage', 'cleardoublepage']

    for cmd in commands_to_remove:
        text = _remove_latex_command(text, cmd)

    remove_pattern = re.compile(r'\\(?:' + '|'.join(commands_to_remove) + r')\s*')
    text = remove_pattern.sub('', text)

    replace_newline_pattern = re.compile(r'\\(?:' + '|'.join(commands_to_replace_newline) + r')\s*')
    text = replace_newline_pattern.sub('\n\n', text)

    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def _remove_latex_command(text, command):
    """
    Removes all instances of a LaTeX command with its argument, handling nested braces.

    Parameters
    ----------
    text : str
        The document text.
    command : str
        The LaTeX command to remove.

    Returns
    -------
    str
        The text with the specified command removed.
    """
    pattern = re.compile(r'\\' + re.escape(command) + r'\{')
    result = []
    pos = 0
    while True:
        cmatch = pattern.search(text, pos)
        if not cmatch:
            result.append(text[pos:])
            break
        start = cmatch.start()
        result.append(text[pos:start])
        brace_level = 1
        i = cmatch.end()
        while i < len(text) and brace_level > 0:
            if text[i] == '{':
                brace_level += 1
            elif text[i] == '}':
                brace_level -= 1
            i += 1
        pos = i
    return ''.join(result)

def remove_formatting_cmds(text):
    """
    Removes various formatting commands like vspace, hspace, bigskip, etc.
    that may appear without arguments.

    Parameters
    ----------
    text : str
        The document content.

    Returns
    -------
    str
        Content with formatting commands removed.
    """
    formatting_cmds = re.compile(
        r'\\(vspace|hspace|bigskip|newpage|smallskip|medskip|pagebreak|linebreak|clearpage|cleardoublepage)'
        r'(\[[^\]]*\])?(\{[^}]*\})?'
    )
    text = formatting_cmds.sub(' ', text)
    return text

def final_cleanup(text):
    """
    Final cleanup of extra spaces and newlines.

    Parameters
    ----------
    text : str
        The document content.

    Returns
    -------
    str
        Cleaned up text, ready to be written to the output file.
    """
    # Replace spaces or tabs before and after '\n' with just '\n'
    text = re.sub(r'[ \t]*\n[ \t]*', '\n', text)
    # Replace sequences of two or more spaces with a single space
    text = re.sub(r' {2,}', ' ', text)
    # Replace sequences of three or more newlines with two newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip() + "\n"

```

### latex_processing.py

```
# ./latex_processing.py

import re

def preprocess_abstract(text):
    """
    Convert the abstract environment into a section-like format.

    Parameters
    ----------
    text : str
        The LaTeX content.

    Returns
    -------
    str
        Modified text where `\\begin{abstract}` is replaced with `\\section*{Abstract}`.
    """
    text = re.sub(r'\\begin\{abstract\}', r'\\section*{Abstract}', text)
    text = re.sub(r'\\end\{abstract\}', '', text)
    return text

def extract_title_authors(text):
    """
    Extracts the title and author(s) from the LaTeX content and removes
    their definitions from the text.

    Parameters
    ----------
    text : str
        The LaTeX content.

    Returns
    -------
    tuple (str, str, str)
        A tuple containing:
        - The modified LaTeX content without the \title and \author commands.
        - The extracted title as a string.
        - The extracted authors as a string.
    """
    title = ""
    authors = ""

    # Extract title
    title_pattern = re.compile(r'\\title\{')
    title_match = title_pattern.search(text)
    if title_match:
        start = title_match.end()
        brace_level = 1
        i = start
        while i < len(text) and brace_level > 0:
            if text[i] == '{':
                brace_level += 1
            elif text[i] == '}':
                brace_level -= 1
            i += 1
        if brace_level == 0:
            title = text[start:i-1].strip()
            text = text[:title_match.start()] + text[i:]
        else:
            print("Warning: Unbalanced braces in \\title command.")
            title = text[start:].strip()
            text = text[:title_match.start()]

    # Extract authors
    author_pattern = re.compile(r'\\author\{')
    author_match = author_pattern.search(text)
    if author_match:
        start = author_match.end()
        brace_level = 1
        i = start
        while i < len(text) and brace_level > 0:
            if text[i] == '{':
                brace_level += 1
            elif text[i] == '}':
                brace_level -= 1
            i += 1
        if brace_level == 0:
            authors = text[start:i-1].strip()
            text = text[:author_match.start()] + text[i:]
        else:
            print("Warning: Unbalanced braces in \\author command.")
            authors = text[start:].strip()
            text = text[:author_match.start()]

    return text, title, authors

def extract_document_content(content):
    """
    Extract the content between \begin{document} and \end{document}.
    If not found, assume the entire content is the document.

    Parameters
    ----------
    content : str
        The entire LaTeX file content.

    Returns
    -------
    str
        The extracted document body.
    """
    doc_match = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', content, flags=re.DOTALL)
    if doc_match:
        return doc_match.group(1)
    return content

def remove_comments(text):
    """
    Remove LaTeX comments that are not escaped (i.e., lines starting with '%').

    Parameters
    ----------
    text : str
        The LaTeX document content.

    Returns
    -------
    str
        Content without LaTeX comments.
    """
    text = re.sub(r'(?<!\\)%.*', '', text)
    # Normalize whitespace
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.replace('\n\n', '<<<PARA_BREAK>>>')
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.replace('<<<PARA_BREAK>>>', '\n\n')
    return text
```

### main.py

```
import os
# ./main.py

from .latex_processing import extract_title_authors, extract_document_content, remove_comments, preprocess_abstract
from .converters import (replace_maketitle, replace_figures, replace_tables, 
                        replace_equations, replace_headings, replace_lists, apply_inline_formats)
from .file_utils import read_input, write_output
from .formats import remove_leftover_commands, remove_formatting_cmds, final_cleanup

def clean_latex_file(input_str):
    """
    Cleans a LaTeX file by:
    - Removing comments and extracting content from \begin{document}...\end{document}
    - Extracting the title and authors and integrating them as Markdown metadata
    - Converting LaTeX sections, figures, tables, lists, equations, etc. to Markdown-friendly formats
    - Removing leftover formatting commands

    Parameters
    ----------
    input_str : str
        The input content or file name. If a filename is provided, it must end with '.tex'.

    Returns
    -------
    None
        Writes the cleaned output to a '.txt' file.
    """
    content, output_path = read_input(input_str)
    content = preprocess_abstract(content)

    # Extract title and authors
    content, title, authors = extract_title_authors(content)

    # Extract main document content
    document_content = extract_document_content(content)

    # Remove LaTeX comments
    document_content = remove_comments(document_content)

    # Apply various conversions
    document_content = replace_maketitle(document_content, title, authors)
    document_content = replace_figures(document_content)
    document_content = replace_tables(document_content)
    document_content = replace_equations(document_content)
    document_content = replace_headings(document_content)
    document_content = replace_lists(document_content)
    document_content = apply_inline_formats(document_content)

    # Remove leftover commands and do final cleanup
    document_content = remove_leftover_commands(document_content)
    document_content = remove_formatting_cmds(document_content)
    document_content = final_cleanup(document_content)

    # Write the output file
    write_output(document_content, output_path)

if __name__ == "__main__":
    # Example usage:
    # clean_latex_file("example.tex")
    pass
```

## Directory Structure

```
latex_converter/
├── __init__.py
├── converters.py
├── file_utils.py
├── formats.py
├── latex_processing.py
└── main.py
```
