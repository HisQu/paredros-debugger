import argparse
import os
import sys
from ParseInformations import ParseInformations

def visualize_parsing(grammar_folder, input_file):
    """Visualizes the parsing process for the given input file."""
    try:
        print(f"\n=== Parsing {input_file} ===")
        parser_info = ParseInformations(grammar_folder , input_file)
        root_node = parser_info.get_root_node()
        
        print("\n=== Final Parse Tree ===")
        print(root_node.get_text())
        
        print("\n=== Traversing the Parse Tree ===")
        traverse_tree(root_node)
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
    parser.add_argument("grammar_folder_path", type=str, help="Path to the folder containing the .g4 Grammar file")
    parser.add_argument("input_file_path", type=str, help="Path of the input file")
    args = parser.parse_args()

    folder_path = os.path.abspath(args.grammar_folder_path)
    input_file = os.path.abspath(args.input_file_path)

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print(f"Error: The folder {folder_path} does not exist or is not a directory.")
        sys.exit(1)

    if not os.path.exists(input_file) or not os.path.isfile(input_file):
        print(f"Error: The file {input_file} does not exist.")
        sys.exit(1)

    visualize_parsing(folder_path, input_file)

if __name__ == "__main__":
    main()
