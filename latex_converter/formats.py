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

