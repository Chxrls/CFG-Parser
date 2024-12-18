from parser import CFGParser, LL1Parser

#identify Left recursion & ambiguity.

# Set the grammar (CFG)
grammar = """
S -> a S b | b S a | S S | e
"""

# Initialize the generated parser
cfg = CFGParser()
cfg.parse_grammar(grammar)
parser = LL1Parser(cfg)

# Validate and prepare the parser
if parser.prepare_parser():
    # Display FIRST sets
    print("\n--- FIRST Sets ---")
    for nt in cfg.non_terminals:
        print(f"FIRST({nt}): {parser.first[nt]}")

    # Display FOLLOW sets
    print("\n--- FOLLOW Sets ---")
    for nt in cfg.non_terminals:
        print(f"FOLLOW({nt}): {parser.follow[nt]}")

    # Display Parsing Table
    parser.display_parsing_table()

    # Test parsing with trace
    test_expressions = ["a b b b"]

    for expr in test_expressions:
        print(f"\n=== Parsing: {expr} ===")
        parser.parse_with_trace(expr)
else:
    print("Parser preparation failed. Cannot proceed with parsing.")
