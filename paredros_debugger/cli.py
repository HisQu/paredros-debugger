"""
This module contains the CLI tool for visualizing the parsing process of a given input file in 
the command line. Using the tool, the user can interact with the parse tree and explore the 
parsing process step by step.

Example:
    $ python -m paredros_debugger.cli <path_to_main_grammar_file> <path_to_input_file>
"""

import argparse
import os
import sys
from paredros_debugger.ParseInformation import ParseInformation

def display_node(node, depth=0, is_alternative=False, rules_dict=None):
    """
    Display information about the current node in the parse tree.

    Args:
        node (ParseNode): The current node to display information about.
        depth (int): The depth of the current node in the parse tree.
        is_alternative (bool): Whether the current node is an alternative.
        rules_dict (dict): A dictionary containing the rules of the grammar.

    Returns:
        None
    """
    indent = "  " * depth
    prefix = "↳" if is_alternative else "●"

    if node.has_error:
        print(f"\n{indent}{prefix} [ID {node.get_unique_identifier()}] ErrorNode!")
    else:
        print(f"\n{indent}{prefix} [ID {node.get_unique_identifier()}]")

    print("\n=== General Informations ===")
    print(f"{indent}  Node type: {node.node_type}")
    print(f"{indent}  State: {node.state}")
    print(f"{indent}  Rulename: {node.rule_name}")
    if rules_dict:
        print(f"{indent}  Rule: {rules_dict.get(node.rule_name).content}")
    print(f"{indent}  Token: {node.current_token}")
    print(f"{indent}  Input: {node.input_text}")

    if node.possible_alternatives:
        print(f"{indent}  Possible transitions:")
        for i, (target_state, matches) in enumerate(node.possible_alternatives, 1):
            print(f"{indent}    {i}: Matches: ({target_state}, {matches})")
        print(f"{indent}  Chosen: Alternative {node.chosen}")

def handle_repl_interaction(node, parse_info, depth=0, rules_dict=None):
    """
    Handle the REPL interaction with the user.
    
    Args:
        node (ParseNode): The current node to interact with.
        parse_info (ParseInformation): The ParseInformation object.
        depth (int): The depth of the current node in the parse tree.
        rules_dict (dict): A dictionary containing the rules of the grammar.

    Returns:
        None
    """
    display_node(node, depth, rules_dict=rules_dict)
    print("=== User Interaction ===")
    direction = input("  Step to parent or child (p/c): ")
    if direction == "p":
        if node.parent:
            handle_repl_interaction(node.parent, parse_info, depth, rules_dict)
    else:
        if node.possible_alternatives and len(node.possible_alternatives) > 1:
            user_io = f"Choose alternative (1-{len(node.possible_alternatives)}) or 0 for next: "
            chosen_alternative = input(user_io)
            if chosen_alternative not in ["0", ""]:
                # Use parse_info.traversal to access expand_alternative
                expanded_alt_node = parse_info.traversal.expand_alternative(node,
                                                                            int(chosen_alternative))
                expanded_alt_node.is_on_parse_tree = False
                handle_repl_interaction(expanded_alt_node, parse_info, depth, rules_dict)
            elif node.next_node:
                handle_repl_interaction(node.next_node, parse_info, depth, rules_dict)
        elif node.next_node:
            handle_repl_interaction(node.next_node, parse_info, depth, rules_dict)

def visualize_parsing(grammar_file, input_file):
    """
    Visualize the parsing process of the input file using the REPL interaction.
    
    Args:
        grammar_file (str): The path to the main .g4 Grammar file.
        input_file (str): The path of the input file.

    Returns:
        None
    """
    try:
        print(f"\n=== Parsing {input_file} ===")
        parse_info = ParseInformation(grammar_file)
        parse_info.parse(input_file)
        print("=== Parsing completed ===")
        print(parse_info.traversal.root)
        print("=== REPL Interaction ===")
        # Start REPL interaction
        handle_repl_interaction(parse_info.traversal.root, parse_info,
                                rules_dict=parse_info.rules_dict)

    except Exception as e:
        print(f"\n💥 Parsing failed: {str(e)}")

def traverse_tree(node, depth=0):
    """
    Traverse the parse tree and print the nodes in a tree-like structure.

    Args:
        node (ParseNode): The current node to traverse.
        depth (int): The depth of the current node in the parse tree.

    Returns:
        None
    """
    indent = "  " * depth
    print(f"{indent}- {node.get_text()}")
    for child in node.get_children():
        traverse_tree(child, depth + 1)

def main():
    """
    Main function for the CLI tool.
    """
    parser = argparse.ArgumentParser(description="Process ANTLR4 grammar and modify parser.")
    parser.add_argument("grammar_file_path", type=str, help="Path to the main .g4 Grammar file")
    parser.add_argument("input_file_path", type=str, help="Path of the input file")
    args = parser.parse_args()

    grammar_file = os.path.abspath(args.grammar_file_path)
    input_file = os.path.abspath(args.input_file_path)

    if not os.path.exists(grammar_file) or not os.path.isfile(grammar_file):
        print(f"Error: The grammar file {grammar_file} does not exist or is not a file.")
        sys.exit(1)

    if not os.path.exists(input_file) or not os.path.isfile(input_file):
        print(f"Error: The file {input_file} does not exist.")
        sys.exit(1)

    print("grammar file:" + grammar_file)
    print("input file:" + input_file)
    visualize_parsing(grammar_file, input_file)

if __name__ == "__main__":
    main()
