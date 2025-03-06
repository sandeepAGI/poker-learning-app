# test_ai_strategy_bug.py
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the relevant modules
from ai.strategies.conservative import ConservativeStrategy
from treys import Card

def main():
    """Test function to demonstrate the AI strategy bug."""
    print("Testing AI Strategy Bug...")
    
    # Create an instance of one of the strategy classes
    strategy = ConservativeStrategy()
    
    # Set up test data
    hole_cards = ["Ah", "Kh"]  # Ace and King of hearts
    community_cards = ["Qh", "Jh", "Th"]  # Royal flush draw
    deck = ["2h", "3h", "4h", "5h", "6h", "7h", "8h", "9h", "2d", "3d", "4d", "5d"]
    
    # Set up a simple game state
    game_state = {
        "community_cards": community_cards,
        "current_bet": 100,
        "pot_size": 500,
        "game_state": "flop"
    }
    
    # This should trigger the error because super().make_decision() is called
    # but the BaseAI class doesn't have this method
    try:
        decision = strategy.make_decision(
            hole_cards=hole_cards,
            game_state=game_state,
            deck=deck,
            pot_size=500,
            spr=5.0
        )
        print(f"Decision: {decision}")
        print("ERROR: The test didn't catch the bug. This should not happen.")
    except AttributeError as e:
        print(f"SUCCESS: Caught the expected error: {e}")
        print("This confirms the bug exists: BaseAI doesn't have a make_decision method")
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("This may indicate a different issue.")

if __name__ == "__main__":
    main()