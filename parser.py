from dataclasses import dataclass
from typing import List, Dict, Set, Tuple
from collections import defaultdict

@dataclass
class Production:
    """Represents a production rule in the grammar"""
    left: str  # Left-hand side (non-terminal)
    right: List[str]  # Right-hand side (terminals and non-terminals)

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
                # Implementation of FIRST set computation
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
    
    def parse(self, input_string: str) -> bool:
        """Parse input string using LL(1) parsing table"""
        input_string = input_string.split()
        input_string.append('$')
        
        stack = ['$', self.cfg.start_symbol]
        index = 0
        
        while stack:
            top = stack.pop()
            current_input = input_string[index]
            
            if top in self.cfg.terminals or top == '$':
                if top == current_input:
                    index += 1
                else:
                    return False
            else:
                if (top, current_input) not in self.parsing_table:
                    return False
                    
                production = self.parsing_table[(top, current_input)]
                if production.right != ['ε']:
                    for symbol in reversed(production.right):
                        stack.append(symbol)
        
        return True