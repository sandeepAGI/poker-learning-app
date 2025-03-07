# backend/utils/formatters.py
from typing import List, Dict, Any

def format_card(card_code: str) -> Dict[str, str]:
    """
    Format a card code into a frontend-friendly format with 
    separate rank and suit properties.
    
    Args:
        card_code: A card code like "Ah" for Ace of hearts
        
    Returns:
        Dict with rank and suit information
    """
    if not card_code or len(card_code) < 2:
        return {"code": "", "rank": "", "suit": "", "name": "Unknown Card"}
    
    # Extract rank and suit
    rank_code = card_code[0:-1]
    suit_code = card_code[-1].lower()
    
    # Map rank codes to display values
    rank_map = {
        "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", 
        "8": "8", "9": "9", "10": "10", "T": "10", "J": "Jack", 
        "Q": "Queen", "K": "King", "A": "Ace"
    }
    
    # Map suit codes to display values and symbols
    suit_map = {
        "s": {"name": "spades", "symbol": "♠", "color": "black"},
        "h": {"name": "hearts", "symbol": "♥", "color": "red"},
        "d": {"name": "diamonds", "symbol": "♦", "color": "red"},
        "c": {"name": "clubs", "symbol": "♣", "color": "black"}
    }
    
    # Get display values
    rank_display = rank_map.get(rank_code, rank_code)
    suit_info = suit_map.get(suit_code, {"name": suit_code, "symbol": suit_code, "color": "black"})
    
    # Create the formatted card
    formatted_card = {
        "code": card_code,
        "rank": rank_code,
        "rank_display": rank_display,
        "suit": suit_code,
        "suit_name": suit_info["name"],
        "suit_symbol": suit_info["symbol"],
        "suit_color": suit_info["color"],
        "name": f"{rank_display} of {suit_info['name'].capitalize()}"
    }
    
    return formatted_card

def format_cards(cards: List[str]) -> List[Dict[str, str]]:
    """
    Format a list of card codes into frontend-friendly format.
    
    Args:
        cards: List of card codes
        
    Returns:
        List of formatted cards
    """
    if not cards:
        return []
        
    return [format_card(card) for card in cards]

def format_money(amount: int) -> str:
    """
    Format a chip amount into a readable string.
    
    Args:
        amount: Chip amount
        
    Returns:
        Formatted string
    """
    if amount is None:
        return "$0"
    
    if amount >= 1000000:
        return f"${amount / 1000000:.1f}M"
    elif amount >= 1000:
        return f"${amount / 1000:.1f}K"
    else:
        return f"${amount}"

def format_timestamp(timestamp: str) -> str:
    """
    Format a timestamp into a readable string.
    
    Args:
        timestamp: ISO format timestamp
        
    Returns:
        Formatted date/time string
    """
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp