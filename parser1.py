from dataclasses import dataclass
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from tabulate import tabulate  # Added for nicer table formatting

@dataclass
class Production:
    """Represents a production rule in the grammar"""
    left: str  # Left-hand side (non-terminal)
    right: List[str]  # Right-hand side (terminals and non-terminals)
    
    def __str__(self):
        return f"{self.left} -> {' '.join(self.right)}"

class CFGParser:
    def __init__(self):
        self.productions: List[Production] = []
        self.non_terminals: Set[str] = set()
        self.terminals: Set[str] = set()
        self.start_symbol: str = None
        
    def parse_grammar(self, grammar_text: str) -> None:
        """Parse grammar rules from text format"""
        lines = grammar_text.strip().split('\n')
        for line in lines:
            # Assume format: A -> B C | B D
            left, right = line.split('->')
            left = left.strip()
            self.non_terminals.add(left)
            
            if not self.start_symbol:
                self.start_symbol = left
                
            # Handle multiple productions with |
            for prod in right.split('|'):
                symbols = prod.strip().split()
                self.productions.append(Production(left, symbols))
                
                # Add terminals and non-terminals
                for symbol in symbols:
                    if symbol.isupper():
                        self.non_terminals.add(symbol)
                    else:
                        self.terminals.add(symbol)

class LL1Parser:
    def __init__(self, cfg: CFGParser):
        self.cfg = cfg
        self.first: Dict[str, Set[str]] = defaultdict(set)
        self.follow: Dict[str, Set[str]] = defaultdict(set)
        self.parsing_table: Dict[Tuple[str, str], Production] = {}
        
    def compute_first_sets(self) -> None:
        """Compute FIRST sets for all symbols"""
        # Initialize with terminals
        for terminal in self.cfg.terminals:
            self.first[terminal].add(terminal)
        
        # Repeated iterations until no changes
        changed = True
        while changed:
            changed = False
            for prod in self.cfg.productions:
                first_before = len(self.first[prod.left])
                
                # Empty production
                if not prod.right or prod.right == ['ε']:
                    self.first[prod.left].add('ε')
                    continue
                    
                first_symbol = prod.right[0]
                if first_symbol in self.cfg.terminals:
                    self.first[prod.left].add(first_symbol)
                else:  # Non-terminal
                    # Recursive FIRST set computation
                    new_first = set()
                    all_nullable = True
                    for symbol in prod.right:
                        if symbol in self.cfg.terminals:
                            new_first.add(symbol)
                            all_nullable = False
                            break
                        
                        symbol_first = self.first[symbol]
                        new_first.update(symbol_first - {'ε'})
                        
                        if 'ε' not in symbol_first:
                            all_nullable = False
                            break
                    
                    if all_nullable:
                        new_first.add('ε')
                    
                    self.first[prod.left].update(new_first)
                
                if len(self.first[prod.left]) > first_before:
                    changed = True
    
    def compute_follow_sets(self) -> None:
        """Compute FOLLOW sets for all non-terminals"""
        # Add $ to follow set of start symbol
        self.follow[self.cfg.start_symbol].add('$')
        
        changed = True
        while changed:
            changed = False
            for prod in self.cfg.productions:
                for i, symbol in enumerate(prod.right):
                    if symbol in self.cfg.non_terminals:
                        follow_before = len(self.follow[symbol])
                        
                        # If it's not the last symbol
                        if i < len(prod.right) - 1:
                            next_symbol = prod.right[i + 1]
                            if next_symbol in self.cfg.terminals:
                                self.follow[symbol].add(next_symbol)
                            else:
                                self.follow[symbol].update(
                                    self.first[next_symbol] - {'ε'}
                                )
                        
                        # If it's the last symbol or next can derive ε
                        if i == len(prod.right) - 1 or 'ε' in self.first[prod.right[i + 1]]:
                            self.follow[symbol].update(self.follow[prod.left])
                        
                        if len(self.follow[symbol]) > follow_before:
                            changed = True
    
    def build_parsing_table(self) -> None:
        """Build LL(1) parsing table"""
        for prod in self.cfg.productions:
            first_string = self.compute_first_of_string(prod.right)
            
            for terminal in first_string - {'ε'}:
                # Check for conflicts
                if (prod.left, terminal) in self.parsing_table:
                    print(f"Warning: Parsing table conflict for ({prod.left}, {terminal})")
                self.parsing_table[(prod.left, terminal)] = prod
            
            if 'ε' in first_string:
                for terminal in self.follow[prod.left]:
                    # Check for conflicts
                    if (prod.left, terminal) in self.parsing_table:
                        print(f"Warning: Parsing table conflict for ({prod.left}, {terminal})")
                    self.parsing_table[(prod.left, terminal)] = prod
    
    def compute_first_of_string(self, symbols: List[str]) -> Set[str]:
        """Compute FIRST set of a string of symbols"""
        if not symbols:
            return {'ε'}
            
        result = set()
        all_nullable = True
        
        for symbol in symbols:
            if symbol in self.cfg.terminals:
                result.add(symbol)
                all_nullable = False
                break
            else:
                symbol_first = self.first[symbol]
                result.update(symbol_first - {'ε'})
                if 'ε' not in symbol_first:
                    all_nullable = False
                    break
        
        if all_nullable:
            result.add('ε')
        return result
    
    def display_details(self):
        """Display detailed parsing information"""
        print("\n--- FIRST SETS ---")
        for symbol, first_set in sorted(self.first.items()):
            print(f"FIRST({symbol}) = {first_set}")
        
        print("\n--- FOLLOW SETS ---")
        for symbol, follow_set in sorted(self.follow.items()):
            print(f"FOLLOW({symbol}) = {follow_set}")
        
        print("\n--- PARSING TABLE ---")
        # Prepare table headers
        headers = [''] + sorted(list(self.cfg.terminals) + ['$'])
        table_data = []
        
        # Create table rows
        for non_terminal in sorted(self.cfg.non_terminals):
            row = [non_terminal]
            for terminal in headers[1:]:
                # Find production for this (non-terminal, terminal) pair
                prod = self.parsing_table.get((non_terminal, terminal), None)
                row.append(str(prod) if prod else '-')
            table_data.append(row)
        
        # Print table using tabulate for nice formatting
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def parse(self, input_string: str, verbose: bool = False) -> bool:
        """Parse input string using LL(1) parsing table"""
        input_string = input_string.split()
        input_string.append('$')
        
        stack = ['$', self.cfg.start_symbol]
        index = 0
        
        if verbose:
            print(f"\n--- Parsing: {' '.join(input_string[:-1])} ---")
            print(f"Initial Stack: {stack}")
        
        derivation_steps = []
        
        while stack:
            top = stack.pop()
            current_input = input_string[index]
            
            if verbose:
                print(f"Top of stack: {top}, Current input: {current_input}")
            
            if top in self.cfg.terminals or top == '$':
                if top == current_input:
                    index += 1
                    if verbose:
                        print(f"Matched terminal: {top}")
                else:
                    if verbose:
                        print(f"Parsing failed: Expected {top}, got {current_input}")
                    return False
            else:
                if (top, current_input) not in self.parsing_table:
                    if verbose:
                        print(f"No parsing rule for ({top}, {current_input})")
                    return False
                    
                production = self.parsing_table[(top, current_input)]
                
                if verbose:
                    print(f"Applied production: {production}")
                
                # Record derivation step
                if production.right != ['ε']:
                    for symbol in reversed(production.right):
                        stack.append(symbol)
                
                if verbose:
                    print(f"Updated Stack: {stack}")
        
        return True

# Example usage script
if __name__ == "__main__":
    # Arithmetic expression grammar
    grammar_text = """
    E -> T EREST
    EREST -> + T EREST | ε
    T -> F TREST
    TREST -> * F TREST | ε
    F -> ( E ) | num
    """

    # Initialize the parser
    cfg = CFGParser()
    cfg.parse_grammar(grammar_text)

    # Create LL(1) parser
    parser = LL1Parser(cfg)

    # Compute parsing artifacts
    parser.compute_first_sets()
    parser.compute_follow_sets()
    parser.build_parsing_table()

    # Display parsing details
    parser.display_details()

    # Test expressions
    test_expressions = [
        "num + num * num",        # Valid expression
        "( num + num ) * num",    # Valid expression
        "num * num +",            # Invalid expression (incomplete)
    ]

    # Parse and display details for each expression
    for expr in test_expressions:
        print(f"\n=== Parsing Expression: {expr} ===")
        result = parser.parse(expr, verbose=True)
        print(f"Parsing Result: {'Valid' if result else 'Invalid'}\n")
