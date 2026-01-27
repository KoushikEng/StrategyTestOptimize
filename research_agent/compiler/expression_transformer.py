"""
Expression transformation utilities for converting old-style expressions to enhanced framework patterns.
"""

import re
from typing import Set, List
from research_agent.schema import Condition


class ExpressionTransformer:
    """Handles transformation of condition expressions to enhanced framework patterns."""
    
    def __init__(self):
        self.time_functions = {
            'is_market_hours', 'extract_hour', 'extract_minute', 'is_opening_hour', 
            'is_closing_hour', 'extract_day_of_week', 'is_in_time_range', 'timestamp',
            'current_timestamp'
        }
        
        self.data_names = {'closes', 'opens', 'highs', 'lows', 'volume', 'timestamps', 'close', 'open', 'high', 'low'}
        
        self.reserved_keywords = {
            'and', 'or', 'not', 'True', 'False', 'if', 'else', 'elif', 'in', 'is',
            'None', 'self', 'data', 'Close', 'Open', 'High', 'Low', 'Volume', 'i'
        }
    
    def extract_indicator_names(self, conditions: List[Condition]) -> Set[str]:
        """Extract indicator names referenced in conditions."""
        indicator_names = set()
        
        for condition in conditions:
            # Find potential indicator names, but exclude composite parts
            # First, find composite patterns (indicator.attribute) and extract just the indicator part
            composite_matches = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)', condition.expression)
            for indicator_name, attribute in composite_matches:
                if (indicator_name not in self.time_functions and 
                    indicator_name not in self.data_names and 
                    indicator_name not in self.reserved_keywords):
                    indicator_names.add(indicator_name)
            
            # Then find simple indicator names (not part of composite patterns)
            # Remove composite patterns first to avoid extracting attributes as indicators
            temp_expr = re.sub(r'\b[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*', '', condition.expression)
            matches = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', temp_expr)
            for match in matches:
                if (match not in self.time_functions and 
                    match not in self.data_names and 
                    match not in self.reserved_keywords):
                    indicator_names.add(match)
        
        return indicator_names
    
    def transform_data_access(self, expression: str) -> str:
        """Transform data access patterns from old to new format."""
        transformations = [
            # Handle indexed access first - transform [i] to [-1] for current bar
            (r'\[i\]', r'[-1]'),
            (r'\[i-1\]', r'[-2]'),
            (r'\[i-2\]', r'[-3]'),
            (r'\[i\+1\]', r'[0]'),  # Future bar (rarely used)
            
            # Handle data access patterns
            (r'\bclose\[([^\]]+)\]', r'self.data.Close[\1]'),
            (r'\bopen\[([^\]]+)\]', r'self.data.Open[\1]'),
            (r'\bhigh\[([^\]]+)\]', r'self.data.High[\1]'),
            (r'\blow\[([^\]]+)\]', r'self.data.Low[\1]'),
            (r'\bvolume\[([^\]]+)\]', r'self.data.Volume[\1]'),
            (r'\bcloses\[([^\]]+)\]', r'self.data.Close[\1]'),
            (r'\bopens\[([^\]]+)\]', r'self.data.Open[\1]'),
            (r'\bhighs\[([^\]]+)\]', r'self.data.High[\1]'),
            (r'\blows\[([^\]]+)\]', r'self.data.Low[\1]'),
            
            # Handle bare names (without indexing)
            (r'\bclose\b(?!\[)', r'self.data.Close[-1]'),
            (r'\bopen\b(?!\[)', r'self.data.Open[-1]'),
            (r'\bhigh\b(?!\[)', r'self.data.High[-1]'),
            (r'\blow\b(?!\[)', r'self.data.Low[-1]'),
            (r'\bvolume\b(?!\[)', r'self.data.Volume[-1]'),
            (r'\bcloses\b(?!\[)', r'self.data.Close[-1]'),
            (r'\bopens\b(?!\[)', r'self.data.Open[-1]'),
            (r'\bhighs\b(?!\[)', r'self.data.High[-1]'),
            (r'\blows\b(?!\[)', r'self.data.Low[-1]'),
        ]
        
        result = expression
        for pattern, replacement in transformations:
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def transform_indicator_access(self, expression: str, indicator_names: Set[str]) -> str:
        """Transform indicator access patterns to use self.indicator_name[-1]."""
        result = expression
        
        # Filter out time functions and data names
        actual_indicator_names = indicator_names - self.time_functions - self.data_names
        
        for indicator_name in actual_indicator_names:
            # Handle composite indicators first (e.g., kc.upper[i-1] -> self.kc.upper[i-1])
            composite_pattern = rf'\b{indicator_name}\.([a-zA-Z_][a-zA-Z0-9_]*)\[([^\]]+)\]'
            composite_replacement = rf'self.{indicator_name}.\1[\2]'
            result = re.sub(composite_pattern, composite_replacement, result)
            
            # Handle simple indexed access (e.g., sma[i] -> self.sma[i])
            # Use negative lookbehind to avoid matching already transformed patterns
            indexed_pattern = rf'(?<!self\.)\b{indicator_name}\[([^\]]+)\]'
            indexed_replacement = rf'self.{indicator_name}[\1]'
            result = re.sub(indexed_pattern, indexed_replacement, result)
            
            # Handle bare indicator names (e.g., sma -> self.sma[-1])
            # Use negative lookbehind and lookahead to avoid conflicts
            bare_pattern = rf'(?<!self\.)\b{indicator_name}\b(?!\[|\.)'
            bare_replacement = rf'self.{indicator_name}[-1]'
            result = re.sub(bare_pattern, bare_replacement, result)
        
        return result
    
    def transform_time_expressions(self, expression: str) -> str:
        """Transform time-based expressions to use current timestamp."""
        transformations = [
            (r'\bself\.data\.timestamps\[-1\]', 'current_timestamp'),
            (r'\btimestamps\[-1\]', 'current_timestamp'),
            (r'\btimestamp\b(?!\[)', 'current_timestamp'),
            (r'\bis_market_hours\(timestamp\)', 'is_market_hours(current_timestamp)'),
            (r'\bextract_hour\(timestamp\)', 'extract_hour(current_timestamp)'),
            (r'\bis_opening_hour\(timestamp\)', 'is_opening_hour(current_timestamp)'),
            (r'\bis_closing_hour\(timestamp\)', 'is_closing_hour(current_timestamp)'),
            (r'\bextract_minute\(timestamp\)', 'extract_minute(current_timestamp)'),
            (r'\bextract_day_of_week\(timestamp\)', 'extract_day_of_week(current_timestamp)'),
        ]
        
        result = expression
        for pattern, replacement in transformations:
            result = re.sub(pattern, replacement, result)
        
        return result
    
    def transform_expression(self, expression: str, indicator_names: Set[str]) -> str:
        """Apply all transformations to an expression."""
        # Apply transformations in order
        result = self.transform_data_access(expression)
        result = self.transform_indicator_access(result, indicator_names)
        result = self.transform_time_expressions(result)
        
        return result