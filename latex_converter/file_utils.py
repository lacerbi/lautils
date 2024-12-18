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
