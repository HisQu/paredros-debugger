import argparse
import os
import sys
from ParseInformations import ParseInformations

def display_node(node, depth=0, is_alternative=False, rules_dict=None):
    """Display node information without REPL interaction."""
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
    """Handle REPL interaction for node traversal."""
    display_node(node, depth, rules_dict=rules_dict)
    print("=== User Interaction ===")
    direction = input(f"  Step to parent or child (p/c): ")
    if direction == "p":
        if node.parent:
            handle_repl_interaction(node.parent, parse_info, depth, rules_dict)
    else:
        if node.possible_alternatives and len(node.possible_alternatives) > 1:
            user_io = f"Choose alternative (1-{len(node.possible_alternatives)}) or 0 for next: "
            chosen_alternative = input(user_io)
            if chosen_alternative not in ["0", ""]:
                # Use parse_info.traversal to access expand_alternative
                expanded_alt_node = parse_info.traversal.expand_alternative(node, int(chosen_alternative))
                expanded_alt_node.is_on_parse_tree = False
                handle_repl_interaction(expanded_alt_node, parse_info, depth, rules_dict)
            elif node.next_node:
                handle_repl_interaction(node.next_node, parse_info, depth, rules_dict)
        elif node.next_node:
            handle_repl_interaction(node.next_node, parse_info, depth, rules_dict)

def visualize_parsing(grammar_folder, input_file):
    """Visualizes the parsing process for the given input file."""
    try:
        print(f"\n=== Parsing {input_file} ===")
        parse_info = ParseInformations(grammar_folder , input_file)
        print("=== Parsing completed ===")
        print(parse_info.traversal.root)
        print("=== REPL Interaction ===")
        # Start REPL interaction
        handle_repl_interaction(parse_info.traversal.root, parse_info, rules_dict=parse_info.rules_dict)
        # todo: add repl like logic

    except Exception as e:
        print(f"\n💥 Parsing failed: {str(e)}")

def traverse_tree(node, depth=0):
    """Recursively prints the parse tree structure."""
    indent = "  " * depth
    print(f"{indent}- {node.get_text()}")
    for child in node.get_children():
        traverse_tree(child, depth + 1)

def main():
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(description="Process ANTLR4 grammar and modify parser.")
    parser.add_argument("grammar_folder_path", type=str, nargs='?', 
                       default="/home/patrick/DigitalHumanities/paredros-debugger/grammar",
                       help="Path to the folder containing the .g4 Grammar file")
    parser.add_argument("input_file_path", type=str, nargs='?',
                       default="/home/patrick/DigitalHumanities/paredros-debugger/grammar/input.txt",
                       help="Path of the input file")
    args = parser.parse_args()
    

    folder_path = os.path.abspath(args.grammar_folder_path)
    input_file = os.path.abspath(args.input_file_path)

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print(f"Error: The folder {folder_path} does not exist or is not a directory.")
        sys.exit(1)

    if not os.path.exists(input_file) or not os.path.isfile(input_file):
        print(f"Error: The file {input_file} does not exist.")
        sys.exit(1)

    print("folder path:" + folder_path)
    print("input file:" + input_file)
    visualize_parsing(folder_path, input_file)

if __name__ == "__main__":
    main()
