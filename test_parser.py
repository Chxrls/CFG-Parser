# Create a test file (test_parser.py)
from parser import CFGParser, LL1Parser

# Define your grammar
grammar_text = """
E -> T EREST
EREST -> + T EREST | ε
T -> F TREST
TREST -> * F TREST | ε
F -> ( E ) | num
"""

# Initialize the parsers
cfg = CFGParser()
cfg.parse_grammar(grammar_text)
parser = LL1Parser(cfg)

# Prepare the parser
parser.compute_first_sets()
parser.compute_follow_sets()
parser.build_parsing_table()

# Test some expressions
test_expressions = [
    "num + num * num",        # Valid expression
    "( num + num ) * num",    # Valid expression
    "num * num +",            # Invalid expression (incomplete)
]

# Parse each expression
for expr in test_expressions:
    result = parser.parse(expr)
    print(f"Expression: {expr}")
    print(f"Valid: {result}\n")