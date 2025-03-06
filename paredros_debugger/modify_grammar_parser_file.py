import re

def modify_parser_file(filename):
    """
    Modifies ANTLR-generated parser files to use our custom parser implementation.
    This script replaces the base Parser class with our CustomParser class to enable
    parsing event interception and traversal tracking.

    Args:
        filename (str): The path to the parser file to modify

    Returns:
        None
    """
    with open(filename, 'r') as file:
        lines = file.readlines()

    modified_lines = []
    import_added = False
    class_pattern = re.compile(r'^(\s*class\s+\w+\s*\(\s*)Parser(\s*\).*)$')

    for line in lines:
        if class_pattern.match(line):
            line = class_pattern.sub(r'\1CustomParser\2', line)
        modified_lines.append(line)

    # Check if an import for CustomParser is already present
    for line in modified_lines:
        if re.match(r'^\s*from\s+paredros_debugger\s+import\s+CustomParser|^\s*from\s+paredros_debugger\.CustomParser\s+import\s+CustomParser', line):
            import_added = True
            break

    if not import_added:
        modified_lines.insert(0, 'from paredros_debugger.CustomParser import CustomParser\n')

    with open(filename, 'w') as file:
        file.writelines(modified_lines)
