# Paredros-Debugger 

A tool for visualizing and analyzing the parsing process of ANTLR4 grammars, with a focus on lookahead decisions and state transitions.

## Prerequisites

- Python 3.10 or higher (developed with 3.10.15)
- ANTLR4 4.13.2
- Java Runtime Environment (JRE) 11 or higher

### Setup

1. Create a virtual environment:
```bash
python -m venv my_venv
```
Where my_venv is the name of the folder for your virtual environment.

2. Activate the virtual environment:
```bash
# On Linux/macOS
source my_venv/bin/activate

# On Windows
.\my_venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## CLI Debugger

The CLI debugger provides an interactive way to explore how ANTLR4 processes your input, showing:
- Current parsing state
- Available alternatives at each decision point
- Token consumption
- Rule entry/exit points
- Detailed lookahead information

### Key Concepts

The debugger visualizes ANTLR's parsing process through the Augmented Transition Network (ATN):

- **ATN**: ANTLR's internal state machine that defines all possible paths through your grammar
- **Parser Traversal Graph**: Our custom data structure that captures the parser's path through the ATN as a connected network of nodes
- **Node**: A point in the parsing process representing a parser state (rule entry, token match, etc.)
- **Child Node**: The next sequential step in the parsing process
- **Previous Node**: The previous step in the parsing process
- **Alternatives**: Different possible paths the parser could take from a given state
- **Parse Path**: The actual sequence of states the parser follows to process your input

The debugger creates a navigable graph of these nodes, allowing you to explore both the actual parse path and other potential paths ANTLR considered.

### Basic Usage

```bash
python -m paredros_debugger.cli <path_to_main_grammar.g4> <path_to_input.txt>
```

### Interactive Commands

The debugger operates in a REPL mode with two main navigation options:

1. **Direction Selection**
   - `c` (or Enter): Move to child node
   - `p`: Move to parent node

2. **Alternative Exploration**
   - `0` (or Enter): Follow the actual parse path
   - `1-N`: Explore different parsing alternatives

At each step, you'll see:
- Current state and rule information
- Token being processed
- Available alternatives
- Input context


## How It Works

### The Parsing Process

During grammar compilation, ANTLR creates the ATN which is essentially a roadmap for parsing any input that matches the grammar. The ATN is a state machine where: 
 1. Each grammar rule is a directed graph of states and transitions
 2. States represent parsing operations like: 
    - Matching tokens
    - Entering/exiting rules
    - Making decisions between alternatives
 3. Transitions show how to move between states based on the input

Since this is the baseline for larger structures like parsetrees we use the ATN as foundation for our visualizer. We track how decisions are made, why certain paths are taken, which rules are entered and what tokens were consumed during parsing. The ATN states and transitions are captured in our visualizer using a node-based data structure. Each node represents a specific point in the parsing process. Since ANTLR always chooses to take one concrete path through the ATN and we build our datastructure upon this decisionmaking, the result is a linked list of nodes. A node contains information about the current ATN state, the next token to be consumed, the already processed input and it's alternative nodes. 


### Decision making

Alternative nodes represent possible transitions from the current ATN state to the next reachable one. While a node can have multiple alternatives, consider this grammar rule example:

```antlr4
rule: subrule_1 | subrule_2
```

During parsing, ANTLR must choose exactly one of these alternatives to continue. This chosen path becomes the next node in our data structure. However, our visualizer also maintains information about the unchosen alternatives. If one wants to see what could have been if the parser had chosen a different alternative there are also methods to expand those in order to view other paths than the one that was actually taken. This allows us to examine the chosen path in a linear view but also lets us explore other parsing choices on each decision point in a branching view. Each node also has a chosen marker that has the number of the alternative that was taken by the parser. For some states this can be extracted from ANTLR directly and for others we have to calculate it manually. 

### State Termination

State processing and node creation terminates in two cases: either when the input has been successfully consumed or when the error recovery handler is called. In the case of an error, we deliberately stop tracking at the first occurrence rather than attempting recovery. This is due to the fact that the user of this tool needs their grammars to process input completly and correctly. For those users, partial results from error recovery would not be usefull as they need to identify and fix the underlying grammar or input issues rather than work with partial parses. 


## Implementation Details

### State Tracking

The tool implements a `ParseTraversal` class that:
- Maintains a list of parse steps
- Records state transitions
- Captures decision points
- Tracks token consumption

The main interfacing with the frontend is done through the `Parseinformation` class, containing all necessary information and functions to start and analyze a parse. It contains a parse tree, that can be interacted with throug the `ParseTreeExplorer` by:
- Moving through the parseprocess step by step
- Moving between the steps that represent decisions in the parse process
- Exploring alternatives at decision steps
- Jumping to specified steps of the parsing process

### Ensuring Visibility

To make the parsing process transparent, we:

1. Log all state transitions with context
2. Record all available alternatives at decision points
3. Track lookahead token sequences
4. Maintain input position information
5. Preserve rule entry/exit relationships

### Node Structure

Each parse node contains:
- Current state information
- Available alternatives
- Chosen path
- Input context
- Rule information
- Parent-child relationships


## Installing for development
The package can be installed to be editable, which is quite handy.

+ Source your virtual environment
+ run the following command (and of course replace `~/paredros-debugger` with your package location)

```shell
python3 -m pip install --editable ~/paredros-debugger
```
