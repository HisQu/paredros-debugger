from dataclasses import dataclass
from typing import Optional

@dataclass
class TokenInfo:
    """Represents a token with both its lexical and literal information"""
    index: int                      # Position in token stream
    lexeme_name: str                # The token type name (e.g., 'EINS', 'ZWEI')
    literal_value: str              # The actual text value (e.g., '1', '2')
    start_index: Optional[int]      # Character position in input
    stop_index: Optional[int]       # End character position
    
    def __str__(self) -> str:
        # Same representation as before but now with acutal values instead of just strings
        return f"{self.lexeme_name} ('{self.literal_value}')"