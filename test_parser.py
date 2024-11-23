
from parser import CFGParser, LL1Parser

# set the grammar (CFG)
grammar_text = """
E -> T EREST
EREST -> + T EREST | ε
T -> F TREST
TREST -> * F TREST | ε
F -> ( E ) | num
"""

# initialize the generated parser
cfg = CFGParser()
cfg.parse_grammar(grammar_text)
parser = LL1Parser(cfg)

# prepare the parser
parser.compute_first_sets()
parser.compute_follow_sets()
parser.build_parsing_table()

# test some expressions
test_expressions = [
    "num + num * num",        # Valid expression
    "( num + num ) * num",    # Valid expression
    "num * num +",            # Invalid expression (incomplete)
]

# parse each expression
for expr in test_expressions:
    result = parser.parse(expr)
    print(f"Expression: {expr}")
    print(f"Valid: {result}\n")