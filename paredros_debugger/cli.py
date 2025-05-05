# cli.py

import argparse
import os
import sys
from datetime import datetime

from paredros_debugger.ParseInformation import ParseInformation
from paredros_debugger.ParseTraceTree import ParseTraceTree
from paredros_debugger.ParseTreeExplorer import ParseTreeExplorer

def get_file_path(arg_value: str, default_path: str, arg_name: str) -> str:
    """
    Returns a valid absolute file path.
    - If 'arg_value' is provided, validates and returns that path.
    - Otherwise uses 'default_path', validates it, and returns it.
    - If the path does not exist or is not a file, prints error and exits.
    """
    if arg_value is None:
        # Attempt fallback
        if not (os.path.exists(default_path) and os.path.isfile(default_path)):
            print(f"Error: No {arg_name} provided and default '{default_path}' does not exist or is not a file.")
            sys.exit(1)
        return os.path.abspath(default_path)
    else:
        # Validate user-provided path
        abs_path = os.path.abspath(arg_value)
        if not (os.path.exists(abs_path) and os.path.isfile(abs_path)):
            print(f"Error: The {arg_name} '{abs_path}' does not exist or is not a file.")
            sys.exit(1)
        return abs_path

def main():
    parser = argparse.ArgumentParser(description="Process ANTLR4 grammar and modify parser.")
    parser.add_argument(
        "grammar_file_path",
        type=str,
        nargs='?',
        help="Path to the main .g4 Grammar file"
    )
    parser.add_argument(
        "input_file_path",
        type=str,
        nargs='?',
        help="Path of the input file"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print verbose parse-tree steps in JSON output"
    )
    args = parser.parse_args()

    # Retrieve the grammar and input file paths (either from args or defaults):
    grammar_file = get_file_path(
        arg_value=args.grammar_file_path,
        default_path="Simpleton/Simpleton_Reg.g4",
        arg_name="grammar_file_path"
    )

    input_file = get_file_path(
        arg_value=args.input_file_path,
        default_path="Simpleton/input.txt",
        arg_name="input_file_path"
    )

    visualize_parsing(grammar_file, input_file, verbose=args.verbose)

def visualize_parsing(grammar_file, input_file, verbose: bool =False):
    """
    Visualize the parsing process using our new step-based REPL.
    """
    print(f"\n=== Parsing {input_file} ===")
    parse_info = ParseInformation(grammar_file)
    parse_info.generate_parser()  # generate the parser
    parse_info.parse(input_file)  # run the parse

    # Check if at least one node had a parse error
    had_error = any(node.is_error_node for node in parse_info.traversal.all_steps)
    if had_error:
        print("=== Parsing completed: Errors were encountered. ===")
    else:
        print("=== Parsing completed successfully. ===")

    # Build the final parse tree
    parse_tree = ParseTraceTree()
    parse_tree.build_from_traversal(parse_info.traversal)

    # Dump final parse tree to JSON for reference
    if verbose:
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = f"parseTree_{now_str}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(parse_tree.to_json(indent=2, verbose=verbose))

        print(f"Final parse tree written to {out_file}")

    # Create the explorer
    explorer = ParseTreeExplorer(full_tree=parse_tree, traversal=parse_info.traversal)

    # Start the interactive REPL
    interactive_explorer_repl(explorer, parse_info, verbose)

def interactive_explorer_repl(
    explorer: ParseTreeExplorer, 
    parse_info: ParseInformation, 
    verbose: bool = False):
    """
    A more interactive REPL using our ParseTreeExplorer,
    but if the user presses Enter (no command), we interpret that as
    "go to default path."
    """

    print("\n=== Welcome to the interactive parse explorer REPL ===")
    print("You can step through the parse, explore or choose alternatives, etc.\n")

    while True:
        # 1) Show partial parse tree so far
        print(f"\n===== CURRENT PARTIAL TREE (cut at step_id={explorer.current_step_id}) =====")
        print(explorer.to_json(verbose))

        # 2) Show current step info
        cur_node = explorer._get_working_tree_step(explorer.current_step_id)
        if cur_node:
            print("\n----- Current Parse Step Info -----")
            print(f" Step ID: {cur_node.id}")
            print(f" Node Type: {cur_node.node_type}")
            print(f" Rule Name: {cur_node.rule_name}")
            print(f" Current Token: {cur_node.current_token_repr}")
            print(f" Chosen Alt: {cur_node.chosen_transition_index}")
            print(f" Matching Error? {cur_node.matching_error}")
            print(f" Possible Alts: {len(cur_node.possible_transitions)}")
            if cur_node.next_input_token or cur_node.next_input_literal:
                print(f" Next Input Token: {cur_node.next_input_token}")
                print(f" Next Input Literal: {cur_node.next_input_literal}")
        else:
            print("\n(No parse node at this step -- possibly at start or end of parse)")

        # 3) Print menu
        print("\nOptions:")
        print("  (b)ack one step")
        print("  (f)orward one step")
        print("  (n)ext decision")
        print("  (pd) previous decision")
        print("  (a)lternative expansion (will immediately ask for alt index)")
        print("  (r)eset to a specific step ID")
        print("  (h)elp (re-show commands)")
        print("  (q)uit")

        cmd = input("Enter command (or press Enter for default): ").strip().lower()

        # ---- If user just pressed Enter => "default path" ----
        if cmd == "":
            # If we're in alt-expansion mode, choose the default alt
            if explorer._in_alternative_expansion_mode:
                default_alt = 1
                if cur_node and cur_node.chosen_transition_index > 0:
                    default_alt = cur_node.chosen_transition_index
                try:
                    explorer.choose_alternative(default_alt)
                    print(f"Chose default alternative #{default_alt}")
                except Exception as e:
                    print(f"Error picking default alt: {e}")
                    explorer.cancel_alt_expansion()
            else:
                # Not in alt-expansion => step_forward(1)
                try:
                    explorer.step_forward(num_steps=1)
                except RuntimeError as e:
                    print(f"Error: {e}")
            continue

        # ---- Otherwise, interpret the typed command ----
        if cmd == "b":
            try:
                explorer.go_back_one_step()
            except RuntimeError as e:
                print(f"Error: {e}")

        elif cmd == "f":
            try:
                explorer.step_forward(num_steps=1)
            except RuntimeError as e:
                print(f"Error: {e}")

        elif cmd == "n":
            try:
                explorer.step_until_next_decision()
            except RuntimeError as e:
                print(f"Error: {e}")

        elif cmd == "pd":
            try:
                explorer.step_back_until_previous_decision()
            except RuntimeError as e:
                print(f"Error: {e}")

        elif cmd == "a":
            # 1) Attempt to expand all alternatives
            try:
                explorer.expand_alternatives()
            except RuntimeError as e:
                print(f"Error: {e}")
                continue

            # 2) Dump partial parse so user can see expansions
            print("\n--- Partial Tree after expansions ---")
            print(explorer.to_json(verbose))

            # 3) Prompt user for alt index
            alt_str = input("Enter alt index to choose (1-based), or press Enter for default: ").strip()
            if alt_str == "":
                # default alt
                default_alt = 1
                if cur_node and cur_node.chosen_transition_index > 0:
                    default_alt = cur_node.chosen_transition_index
                try:
                    explorer.choose_alternative(default_alt)
                    print(f"Chose default alternative #{default_alt}")
                except Exception as e:
                    print(f"Error picking alt: {e}")
                    explorer.cancel_alt_expansion()
            else:
                try:
                    alt_idx = int(alt_str)
                    explorer.choose_alternative(alt_idx)
                except ValueError:
                    print("Invalid integer  . Cancelling alt expansion.")
                    explorer.cancel_alt_expansion()
                except RuntimeError as e:
                    print(f"Error picking alt: {e}")
                    explorer.cancel_alt_expansion()

        elif cmd == "r":
            step_str = input("Which step ID to reset to? ").strip()
            try:
                step_id = int(step_str)
                explorer.reset_to_step_id(step_id)
            except ValueError:
                print("Invalid step ID.")
            except RuntimeError as e:
                print(f"Error: {e}")

        elif cmd == "h":
            print("\nHelp Menu:")
            print("  (b) go back one step")
            print("  (f) go forward one step")
            print("  (n) skip to the next decision node")
            print("  (pd) skip backwards to the previous decision node")
            print("  (a) expand alternatives and choose one immediately")
            print("  (r) reset to any numeric step ID")
            print("  (q) quit the REPL\n")

        elif cmd == "q":
            print("Exiting REPL. Goodbye.")
            break

        else:
            print("Unknown command. Type 'h' for help or 'q' to quit.")

if __name__ == "__main__":
    main()
