import random
from typing import List


class DeckManager:
    """Simple deck management."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Create and shuffle a new deck."""
        self.deck = [rank + suit for rank in "23456789TJQKA" for suit in "shdc"]
        random.shuffle(self.deck)

    def deal_cards(self, num_cards: int) -> List[str]:
        """Deal specified number of cards."""
        if num_cards > len(self.deck):
            raise ValueError(f"Not enough cards: need {num_cards}, have {len(self.deck)}")

        cards = self.deck[:num_cards]
        self.deck = self.deck[num_cards:]
        return cards
