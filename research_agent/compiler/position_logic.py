"""
Position logic generation for different position types (long, short, both).
"""

from typing import List, Set
from research_agent.schema import Condition
from .expression_transformer import ExpressionTransformer


class PositionLogicGenerator:
    """Generates position management logic based on position type."""
    
    def __init__(self):
        self.transformer = ExpressionTransformer()
    
    def generate_next_method(self, entry_conditions: List[Condition], exit_conditions: List[Condition], 
                           indicator_names: Set[str], position_type: str = "long") -> str:
        """Generate next() method with appropriate position logic."""
        
        method_parts = [
            '    def next(self):',
            '        """Process the current bar."""'
        ]
        
        # Handle different position types
        if position_type.lower() == "both":
            return self._generate_both_positions_logic(entry_conditions, exit_conditions, indicator_names, method_parts)
        elif position_type.lower() == "short":
            return self._generate_short_only_logic(entry_conditions, exit_conditions, indicator_names, method_parts)
        else:  # default to long
            return self._generate_long_only_logic(entry_conditions, exit_conditions, indicator_names, method_parts)
    
    def _generate_long_only_logic(self, entry_conditions: List[Condition], exit_conditions: List[Condition], 
                                indicator_names: Set[str], method_parts: List[str]) -> str:
        """Generate logic for long-only positions."""
        
        if not entry_conditions and not exit_conditions:
            method_parts.extend([
                '        # No trading conditions specified',
                '        pass'
            ])
        elif not entry_conditions:
            exit_logic = self._transform_conditions(exit_conditions, indicator_names)
            method_parts.extend([
                '        # No entry conditions - only exit logic',
                f'        if self.position[\'position_size\'] > 0 and ({exit_logic}):',
                '            self.sell()'
            ])
        elif not exit_conditions:
            entry_logic = self._transform_conditions(entry_conditions, indicator_names)
            method_parts.extend([
                '        # No exit conditions - only entry logic',
                f'        if not self.position[\'in_position\'] and ({entry_logic}):',
                '            self.buy()'
            ])
        else:
            entry_logic = self._transform_conditions(entry_conditions, indicator_names)
            exit_logic = self._transform_conditions(exit_conditions, indicator_names)
            method_parts.extend([
                '        # Entry conditions',
                f'        if not self.position[\'in_position\'] and ({entry_logic}):',
                '            self.buy()',
                '',
                '        # Exit conditions',
                f'        elif self.position[\'position_size\'] > 0 and ({exit_logic}):',
                '            self.sell()'
            ])
        
        return '\n'.join(method_parts)
    
    def _generate_short_only_logic(self, entry_conditions: List[Condition], exit_conditions: List[Condition], 
                                 indicator_names: Set[str], method_parts: List[str]) -> str:
        """Generate logic for short-only positions."""
        
        if not entry_conditions and not exit_conditions:
            method_parts.extend([
                '        # No trading conditions specified',
                '        pass'
            ])
        elif not entry_conditions:
            exit_logic = self._transform_conditions(exit_conditions, indicator_names)
            method_parts.extend([
                '        # No entry conditions - only exit logic',
                f'        if self.position[\'position_size\'] < 0 and ({exit_logic}):',
                '            self.buy()'
            ])
        elif not exit_conditions:
            entry_logic = self._transform_conditions(entry_conditions, indicator_names)
            method_parts.extend([
                '        # No exit conditions - only entry logic',
                f'        if not self.position[\'in_position\'] and ({entry_logic}):',
                '            self.sell()'
            ])
        else:
            entry_logic = self._transform_conditions(entry_conditions, indicator_names)
            exit_logic = self._transform_conditions(exit_conditions, indicator_names)
            method_parts.extend([
                '        # Entry conditions',
                f'        if not self.position[\'in_position\'] and ({entry_logic}):',
                '            self.sell()',
                '',
                '        # Exit conditions',
                f'        elif self.position[\'position_size\'] < 0 and ({exit_logic}):',
                '            self.buy()'
            ])
        
        return '\n'.join(method_parts)
    
    def _generate_both_positions_logic(self, entry_conditions: List[Condition], exit_conditions: List[Condition], indicator_names: Set[str], method_parts: List[str]) -> str:
        """Generate logic for both long and short positions."""
        
        if not entry_conditions and not exit_conditions:
            method_parts.extend([
                '        # No trading conditions specified',
                '        pass'
            ])
            return '\n'.join(method_parts)
        
        # Separate conditions by position type
        long_entry_conditions = []
        short_entry_conditions = []
        long_exit_conditions = []
        short_exit_conditions = []
        
        # Split entry conditions based on position_type or index
        for i, condition in enumerate(entry_conditions):
            if hasattr(condition, 'position_type') and condition.position_type:
                if condition.position_type == "long":
                    long_entry_conditions.append(condition)
                elif condition.position_type == "short":
                    short_entry_conditions.append(condition)
            else:
                # Fallback: alternate by index (even = long, odd = short)
                if i % 2 == 0:
                    long_entry_conditions.append(condition)
                else:
                    short_entry_conditions.append(condition)
        
        # Split exit conditions based on position_type or index
        for i, condition in enumerate(exit_conditions):
            if hasattr(condition, 'position_type') and condition.position_type:
                if condition.position_type == "long":
                    long_exit_conditions.append(condition)
                elif condition.position_type == "short":
                    short_exit_conditions.append(condition)
            else:
                # Fallback: alternate by index (even = long, odd = short)
                if i % 2 == 0:
                    long_exit_conditions.append(condition)
                else:
                    short_exit_conditions.append(condition)
        
        # Generate long logic
        if long_entry_conditions:
            long_entry_logic = self._transform_conditions(long_entry_conditions, indicator_names)
            method_parts.extend([
                '        # Long entry conditions',
                f'        if not self.position[\'in_position\'] and ({long_entry_logic}):',
                '            self.buy()'
            ])
        
        # Generate short logic
        if short_entry_conditions:
            short_entry_logic = self._transform_conditions(short_entry_conditions, indicator_names)
            method_parts.extend([
                '',
                '        # Short entry conditions',
                f'        elif not self.position[\'in_position\'] and ({short_entry_logic}):',
                '            self.sell()'
            ])
        
        # Generate exit logic
        if long_exit_conditions:
            long_exit_logic = self._transform_conditions(long_exit_conditions, indicator_names)
            method_parts.extend([
                '',
                '        # Long exit conditions',
                f'        elif self.position[\'position_size\'] > 0 and ({long_exit_logic}):',
                '            self.sell()'
            ])
        
        if short_exit_conditions:
            short_exit_logic = self._transform_conditions(short_exit_conditions, indicator_names)
            method_parts.extend([
                '',
                '        # Short exit conditions',
                f'        elif self.position[\'position_size\'] < 0 and ({short_exit_logic}):',
                '            self.buy()'
            ])
        
        return '\n'.join(method_parts)
    
    def _transform_conditions(self, conditions: List[Condition], indicator_names: Set[str]) -> str:
        """Transform a list of conditions into a single expression."""
        if not conditions:
            return "True"
        
        transformed_exprs = []
        for condition in conditions:
            transformed_expr = self.transformer.transform_expression(condition.expression, indicator_names)
            transformed_exprs.append(f"({transformed_expr})")
        
        return " and ".join(transformed_exprs)