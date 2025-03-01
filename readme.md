# ANTLR4 Grammar Parser with Lookahead Visualization

This tool helps visualize ANTLR4 parser lookahead and decision-making process for a custom grammar.

## Prerequisites

- Python 3.10.15
- ANTLR4 (4.13.2)
- Java Runtime Environment (JRE)

## Setup and Usage

1. First, compile the grammar file using ANTLR4:

```sh
antlr4 -Dlanguage=Python3 MyGrammar.g4
```

2. Modify the generated parser to use our custom error handling:

```sh
python modify_grammar_parser_file.py
```

3. Run the visualization tool: 
```sh
python verbose.py
```

The tool will:

- Read input from input.txt
- Parse it according to the grammar rules in MyGrammar.g4
- Display detailed information about parser decisions and lookahead
## Input Format
Your input text should be placed in `input.txt` and follow the grammar rules defined in `MyGrammar.g4`. The current grammar is designed to parse structured text with head and sublemma tags.