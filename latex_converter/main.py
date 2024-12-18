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
