# ANTLR4 Grammar Parser with Lookahead Visualization

This tool helps visualize ANTLR4 parser lookahead and decision-making process for a custom grammar.

## Prerequisites

- Python 3.10.15
- ANTLR4 (4.13.2)
- Java Runtime Environment (JRE)

## Setup and Usage CLI Tool

1. Run the Command line tool with specified path to main grammar file and a path to a text file contaning
   your Input Text:

```sh
python -m paredros_debugger.new_cli <path_to_main_grammar.g4> <path_to_input.txt>
```


The tool will:

- Read the specified input
- Parse it according to the grammar rules in your Grammar
- Display detailed information about parser decisions and lookahead
- Displays a Parse Tree
- Display a Interactive REPL to interact with the ATN representation of your grammar and your Input text
  
## REPL Usage
For every step of the grammar you get first prompted if you want to visit a child *c* or a parent *p* of your current node.
Choose accordingly. Hitting Return without input will step to a child by default.
Then you get prompted to choose between to dive into an alternative node, then you have to enter a number in the range 1-X.
if you want the next node of the parse based on input enter 0. Hitting Return without input will step into the next node on the parsetree on default.

## Installing for development
The package can be installed to be editable, which is quite handy.

+ Source your virtual environment
+ run the following command (and of course replace `~/paredros-debugger` with your package location)

```shell
python3 -m pip install --editable ~/paredros-debugger
```
