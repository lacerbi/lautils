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
