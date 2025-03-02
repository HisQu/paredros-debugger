import argparse
import os
import subprocess
import sys


from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker
from antlr4.atn.PredictionMode import PredictionMode
from antlr4.tree.Trees import Trees

from LookaheadVisualizer import LookaheadVisualizer
from DetailedParseListener import DetailedParseListener, resolveLiteralOrSymbolicName

from UserGrammar import UserGrammar
from utils import find_grammar_file, rename_grammar_file, generate_parser, modify_generated_parser, load_parser_and_lexer, get_start_rule


def visualize_parsing_cli(folder_path, input_text):
    """Visualizes the parsing process for the given input text."""
    lexer_class, parser_class = load_parser_and_lexer(folder_path)
    input_stream = InputStream(input_text)
    lexer = lexer_class(input_stream)
    tokens = CommonTokenStream(lexer)
    parser = parser_class(tokens)

    # Configure for lookahead visualization
    parser._interp = LookaheadVisualizer(parser)
    parser._interp.predictionMode = PredictionMode.LL_EXACT_AMBIG_DETECTION

    # Set up listeners
    parser.removeErrorListeners()
    walker = ParseTreeWalker()
    listener = DetailedParseListener(parser)

    # Setup grammar file
    grammar_file = os.path.join(folder_path, "MyGrammar.g4")
    grammar = UserGrammar()
    grammar.add_grammar_file(grammar_file)
    rules_dict = grammar.get_rules()

    print("=== Token Stream ===")
    tokens.fill()
    for token in tokens.tokens[:-1]:  # Skip EOF
        _t = resolveLiteralOrSymbolicName(parser, token)
        print(f"{_t}")
        if _t.startswith("Literal:"):
            print(f"[ LIT] {'':<15} '{token.text}'")
        else:
            # Add safety check for symbolic names
            symbol_name = ''
            if token.type >= 0 and token.type < len(lexer.symbolicNames) and lexer.symbolicNames[token.type]:
                symbol_name = lexer.symbolicNames[token.type]
            else:
                symbol_name = f"<T{token.type}>"
            print(f"[{token.type:4}] {symbol_name:15} '{token.text}'")

    print("\n=== Parsing Process ===")
    try:
        start_rule = get_start_rule(grammar_file)
        print(f"Starting rule: {start_rule}")
        parse_method = getattr(parser, start_rule)
        tree = parse_method()

        print("\n=== Final Parse Tree ===")
        print(Trees.toStringTree(tree, None, parser))

        print("\n=== Rule Execution Trace ===")
        walker.walk(listener, tree)

        print("\n=== Parse Traversal Analysis ===")
        traversal = parser._errHandler.traversal

        def print_node(node, depth=0, is_alternative=False):
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
            print(f"{indent}  Rule: {rules_dict.get(node.rule_name).content}")
            print(f"{indent}  Token: {node.current_token}")
            print(f"{indent}  Input: {node.input_text}")
            print("=== Possible Alternatives ===")

            # Add alternative details from stored possible_alternatives
            if node.possible_alternatives:
                print(f"{indent}  Possible transitions:")
                for i, (target_state, matches) in enumerate(node.possible_alternatives, 1):
                    print(f"{indent}    {i}: Matches: ({target_state}, {matches})")
                # print(f"{indent} Correct parse tree Chosen: Alternative {node.chosen}")
            print("=== Node Attributes ===")
            # Repl part
            node.print_attributes()
            print("=== User Interaction ===")
            direction = input(f"{indent} Step to parent or child (p/c): ")
            if direction == "p":
                print_node(node.parent, depth)
            else:
                user_io = f"Choose alternative (1-{len(node.possible_alternatives)}) or 0 for next: "
                choosen_alternative = input(user_io)
                if choosen_alternative not in ["0",""]:
                    expanded_alt_node = traversal.expand_alternative(node, int(choosen_alternative))
                    expanded_alt_node.is_on_parse_tree = False
                    print_node(expanded_alt_node, depth)
                else:
                    print_node(node.next_node, depth)

            if node.next_node:
                print_node(node.next_node, depth)

        print("\n=== After Cleanup ===")
        merged_groups = traversal.group_and_merge()
        traversal.replace_merged_nodes(merged_groups)
        traversal._fix_node_ids()

        if traversal.root:
            print_node(traversal.root)

    except Exception as e:
        print(f"\n💥 Parsing failed: {str(e)}")

def main():
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(description="Process ANTLR4 grammar and modify parser.")
    parser.add_argument(dest="grammar_folder_path", type=str,
                        help="Path to the folder containing the .g4 Grammar file")
    parser.add_argument(dest="input_file_path", type=str,
                        help="Path of the input file")
    args = parser.parse_args()

    folder_path = os.path.abspath(args.grammar_folder_path)
    input_file = os.path.abspath(args.input_file_path)

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print(f"Error: The folder {folder_path} does not exist or is not a directory.")
        sys.exit(1)

    grammar_file = find_grammar_file(folder_path)
    if not grammar_file:
        print("Error: No .g4 grammar file found in the provided folder.")
        sys.exit(1)

    renamed_path = rename_grammar_file(folder_path, grammar_file)
    print(f"Renamed grammar file to: {renamed_path}")

    try:
        generate_parser(folder_path)
        print("Parser generated successfully.")
    except subprocess.CalledProcessError:
        print("Error: Failed to generate parser with ANTLR4.")
        sys.exit(1)

    try:
        modify_generated_parser(folder_path + "/MyGrammarParser.py")
        print("Parser modification completed.")
    except subprocess.CalledProcessError:
        print("Error: Failed to modify the generated parser.")
        sys.exit(1)

    # with open("input.txt", "r") as file:
    #     input_text = file.read()
    # visualize_parsing(input_text)

    try:
        with open(os.path.join(folder_path, input_file), "r", encoding="utf-8") as f:
            input_text = f.read()
        visualize_parsing_cli(folder_path=folder_path, input_text=input_text)
    except Exception as e:
        print(f"Error during parsing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
