from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict

@dataclass
class Production:
    """Represents a production rule in the grammar"""
    left: str  # Left-hand side (non-terminal)
    right: List[str]  # Right-hand side (terminals and non-terminals)

    def __str__(self):
        return f"{self.left} → {' '.join(self.right)}"

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
        changed = True
        while changed:
            changed = False
            for prod in self.cfg.productions:
                first_before = len(self.first[prod.left])
                
                if not prod.right:  # Empty production
                    self.first[prod.left].add('ε')
                    continue
                    
                first_symbol = prod.right[0]
                if first_symbol in self.cfg.terminals:
                    self.first[prod.left].add(first_symbol)
                else:  # Non-terminal
                    self.first[prod.left].update(
                        self.first[first_symbol] - {'ε'}
                    )
                
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
                self.parsing_table[(prod.left, terminal)] = prod
            
            if 'ε' in first_string:
                for terminal in self.follow[prod.left]:
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
    
    def display_parsing_table(self) -> None:
        """Display the LL(1) parsing table with proper formatting."""
        print("\n--- LL(1) Parsing Table ---")

        # Collect all terminals and add '$' for end-of-input marker
        terminals = sorted(self.cfg.terminals) + ['$']
        non_terminals = sorted(self.cfg.non_terminals)

        # Determine column width dynamically based on longest terminal/non-terminal or production
        column_width = max(
            10,  # Minimum width for readability
            max(len(str(nt)) for nt in non_terminals + terminals),
            max(len(str(prod)) for prod in self.parsing_table.values()) if self.parsing_table else 0
        )
        
        # Print the header row
        print(f"{'NT/T'.ljust(column_width)}", end="")
        for terminal in terminals:
            print(f"{terminal.ljust(column_width)}", end="")
        print()

        # Print the table rows for each non-terminal
        for nt in non_terminals:
            print(f"{nt.ljust(column_width)}", end="")
            for terminal in terminals:
                production = self.parsing_table.get((nt, terminal), None)
                cell = str(production) if production else "-"
                print(f"{cell.ljust(column_width)}", end="")
            print()  # New line

    
    def parse_with_trace(self, input_string: str) -> None:
        """Parse input string with detailed tracing"""
        input_string = input_string.split()
        input_string.append('$')
        
        stack = ['$', self.cfg.start_symbol]
        index = 0
        
        print("\n--- Parsing Trace ---")
        print(f"{'Stack':30} {'Input':30} {'Action':30}")
        print("-" * 90)
        
        while stack:
            # Print current state
            current_stack = ' '.join(reversed(stack))
            current_input = ' '.join(input_string[index:])
            print(f"{current_stack:30} {current_input:30}", end="")
            
            top = stack.pop()
            current_input_symbol = input_string[index]
            
            if top in self.cfg.terminals or top == '$':
                if top == current_input_symbol:
                    print(f"{'Match ' + top:30}")
                    index += 1
                    if index >= len(input_string):
                        print("\nParse successful!")
                        return
                else:
                    print(f"{'ERROR: Terminal mismatch':30}")
                    return
            else:
                if (top, current_input_symbol) not in self.parsing_table:
                    print(f"{'ERROR: No matching production':30}")
                    return
                    
                production = self.parsing_table[(top, current_input_symbol)]
                print(f"{'Expand ' + str(production):30}")
                
                if production.right != ['ε']:
                    for symbol in reversed(production.right):
                        stack.append(symbol)
        
        print("\nParse unsuccessful!")

    def validate_grammar(self) -> bool:
        """
        Comprehensive grammar validation to detect:
        1. Left Recursion
        2. Ambiguity in LL(1) Parsing
        
        Returns:
        - True if grammar is valid for LL(1) parsing
        - False with error messages if invalid
        """
        # Detect Direct Left Recursion
        def detect_direct_left_recursion():
            direct_left_recursive = []
            for prod in self.cfg.productions:
                # Check if the first symbol of the production's right side 
                # is the same as the left-hand non-terminal
                if prod.right and prod.right[0] == prod.left:
                    direct_left_recursive.append(prod)
            return direct_left_recursive

        # Detect Indirect Left Recursion
        def detect_indirect_left_recursion():
            indirect_left_recursive = []
            
            # Create a derivation graph
            derivation_graph = defaultdict(set)
            for prod in self.cfg.productions:
                left = prod.left
                for symbol in prod.right:
                    if symbol in self.cfg.non_terminals and symbol != left:
                        derivation_graph[left].add(symbol)
            
            # Check for cycles that can lead to left recursion
            def has_path_to_self(start, current, visited=None):
                if visited is None:
                    visited = set()
                
                if current == start:
                    return True
                
                visited.add(current)
                
                for next_symbol in derivation_graph[current]:
                    if next_symbol not in visited:
                        if has_path_to_self(start, next_symbol, visited):
                            return True
                
                return False
            
            # Check each non-terminal for potential indirect left recursion
            for nt in self.cfg.non_terminals:
                if has_path_to_self(nt, nt):
                    indirect_left_recursive.append(nt)
            
            return indirect_left_recursive

        # Detect Ambiguity in Parsing Table
        def detect_parsing_table_ambiguity():
            ambiguous_entries = {}
            
            # Compute First and Follow sets if not already computed
            if not self.first:
                self.compute_first_sets()
            if not self.follow:
                self.compute_follow_sets()
            
            # Detect conflicts during parsing table construction
            for prod in self.cfg.productions:
                first_string = self.compute_first_of_string(prod.right)
                
                # Check conflicts for terminals in FIRST set
                for terminal in first_string - {'ε'}:
                    key = (prod.left, terminal)
                    if key in self.parsing_table:
                        # Conflict detected if different productions exist for same (NT, Terminal)
                        if self.parsing_table[key] != prod:
                            if key not in ambiguous_entries:
                                ambiguous_entries[key] = [self.parsing_table[key], prod]
                            else:
                                ambiguous_entries[key].append(prod)
                
                # Check conflicts for FOLLOW set when production can derive ε
                if 'ε' in first_string:
                    for terminal in self.follow[prod.left]:
                        key = (prod.left, terminal)
                        if key in self.parsing_table:
                            # Conflict detected if different productions exist for same (NT, Terminal)
                            if self.parsing_table[key] != prod:
                                if key not in ambiguous_entries:
                                    ambiguous_entries[key] = [self.parsing_table[key], prod]
                                else:
                                    ambiguous_entries[key].append(prod)
            
            return ambiguous_entries

        try:
            # 1. Check Direct Left Recursion
            direct_left_recursive = detect_direct_left_recursion()
            if direct_left_recursive:
                error_msg = "Direct Left Recursion Detected:\n"
                error_msg += "\n".join(str(prod) for prod in direct_left_recursive)
                print(error_msg)
                return False
            
            # 2. Check Indirect Left Recursion
            #indirect_left_recursive = detect_indirect_left_recursion()
            #if indirect_left_recursive:
            #    error_msg = "Indirect Left Recursion Detected in Non-Terminals:\n"
            #    error_msg += ", ".join(indirect_left_recursive)
            #    print(error_msg)
            #    return False
            
            # 3. Check for ambiguity
            ambiguous_entries = detect_parsing_table_ambiguity()
            if ambiguous_entries:
                error_msg = "Grammar Ambiguity Detected:\n"
                for (nt, terminal), prods in ambiguous_entries.items():
                    error_msg += f"Conflict at ({nt}, {terminal}): {prods}\n"
                print(error_msg)
                return False
            
            print("\nGrammar is valid for LL(1) parsing.")
            return True
        
        except Exception as e:
            print(f"\nGrammar Validation Failed: {e}")
            return False

    def prepare_parser(self) -> bool:
        """
        Prepares the parser by validating grammar and computing necessary sets.
        
        Returns:
        - True if parser is ready for parsing
        - False if grammar validation fails
        """
        if not self.validate_grammar():
            return False
        
        try:
            self.compute_first_sets()
            self.compute_follow_sets()
            self.build_parsing_table()
            return True
        except Exception as e:
            print(f"Error preparing parser: {e}")
            return False
