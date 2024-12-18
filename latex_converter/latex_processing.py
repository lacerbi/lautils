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
