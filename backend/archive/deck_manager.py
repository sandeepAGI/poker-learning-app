import random
from typing import List, Optional, Tuple
from treys import Card


class DeckManager:
    """
    Encapsulates all deck operations for poker games.
    Ensures safe handling of the deck with proper shuffling, dealing,
    and tracking of dealt cards.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the deck manager with an optional random seed.
        
        Args:
            seed (Optional[int]): Random seed for reproducible shuffling (useful for testing)
        """
        self._random = random.Random(seed) if seed is not None else random.Random()
        self._deck: List[str] = []
        self._burnt_cards: List[str] = []
        self._dealt_hole_cards: List[str] = []
        self._dealt_community_cards: List[str] = []
        self.reset()
    
    def reset(self) -> None:
        """
        Resets the deck to a full 52-card deck and shuffles it.
        Clears all tracking of dealt and burnt cards.
        """
        self._deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]
        self._random.shuffle(self._deck)
        self._burnt_cards = []
        self._dealt_hole_cards = []
        self._dealt_community_cards = []
    
    def get_deck(self) -> List[str]:
        """
        Returns a copy of the current deck (cards not yet dealt).
        
        Returns:
            List[str]: Copy of remaining cards in the deck
        """
        return self._deck.copy()
    
    def deal_hole_cards(self, num_players: int) -> List[List[str]]:
        """
        Deals 2 hole cards to each player.
        
        Args:
            num_players (int): Number of players to deal to
            
        Returns:
            List[List[str]]: List of 2-card hands for each player
        """
        if num_players * 2 > len(self._deck):
            raise ValueError(f"Not enough cards to deal to {num_players} players")
        
        hole_cards = []
        for _ in range(num_players):
            cards = [self._deck.pop(0), self._deck.pop(0)]
            self._dealt_hole_cards.extend(cards)
            hole_cards.append(cards)
            
        return hole_cards
    
    def deal_to_player(self, num_cards: int = 2) -> List[str]:
        """
        Deal specific number of cards to a player.
        
        Args:
            num_cards (int): Number of cards to deal (default 2 for Texas Hold'em)
            
        Returns:
            List[str]: The dealt cards
            
        Raises:
            ValueError: If num_cards is negative or exceeds the deck size
        """
        if num_cards < 0:
            raise ValueError(f"Cannot deal a negative number of cards: {num_cards}")
            
        if num_cards == 0:
            return []
            
        if num_cards > len(self._deck):
            raise ValueError(f"Not enough cards to deal {num_cards} cards")
            
        cards = self._deck[:num_cards]
        self._deck = self._deck[num_cards:]
        self._dealt_hole_cards.extend(cards)
        return cards
    
    def deal_flop(self) -> List[str]:
        """
        Deals the flop (3 community cards), burning one card first.
        
        Returns:
            List[str]: The 3 flop cards
        """
        if len(self._deck) < 4:  # 1 burn + 3 flop
            raise ValueError("Not enough cards to deal the flop")
            
        self._burn_card()
        flop = [self._deck.pop(0), self._deck.pop(0), self._deck.pop(0)]
        self._dealt_community_cards.extend(flop)
        return flop
    
    def deal_turn(self) -> str:
        """
        Deals the turn card, burning one card first.
        
        Returns:
            str: The turn card
        """
        if len(self._deck) < 2:  # 1 burn + 1 turn
            raise ValueError("Not enough cards to deal the turn")
            
        self._burn_card()
        turn = self._deck.pop(0)
        self._dealt_community_cards.append(turn)
        return turn
    
    def deal_river(self) -> str:
        """
        Deals the river card, burning one card first.
        
        Returns:
            str: The river card
        """
        if len(self._deck) < 2:  # 1 burn + 1 river
            raise ValueError("Not enough cards to deal the river")
            
        self._burn_card()
        river = self._deck.pop(0)
        self._dealt_community_cards.append(river)
        return river
    
    def _burn_card(self) -> None:
        """
        Burns a card (removes it from play).
        """
        if self._deck:
            burnt = self._deck.pop(0)
            self._burnt_cards.append(burnt)
    
    def get_community_cards(self) -> List[str]:
        """
        Returns the current community cards.
        
        Returns:
            List[str]: Copy of current community cards
        """
        return self._dealt_community_cards.copy()
    
    def get_stats(self) -> Tuple[int, int, int, int]:
        """
        Returns statistics about the current deck state.
        
        Returns:
            Tuple[int, int, int, int]: (remaining_cards, hole_cards, community_cards, burnt_cards)
        """
        return (
            len(self._deck),
            len(self._dealt_hole_cards),
            len(self._dealt_community_cards),
            len(self._burnt_cards)
        )
    
    @staticmethod
    def convert_to_treys_cards(card_strings: List[str]) -> List[int]:
        """
        Converts string representation of cards to treys Card integers.
        Useful for hand evaluation with the treys library.
        
        Args:
            card_strings (List[str]): Cards in string format (e.g., "Ah", "Tc")
            
        Returns:
            List[int]: Cards in treys integer format
        """
        return [Card.new(card.replace("10", "T")) for card in card_strings]