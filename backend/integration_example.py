from typing import Dict, List, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from game_engine import PokerGame, Player, GameState
from game_engine_hooks import get_game_engine_hooks
from logger import get_logger

# Create a logger for the integration example
logger = get_logger("integration_example")

class HumanPlayer(Player):
    """Human player extension for the game engine."""
    
    def make_decision(self, game_state: Dict[str, Any], deck: List[str], 
                     spr: float, pot_size: int) -> str:
        """
        Gets player decision and tracks it for learning.
        
        Args:
            game_state: Current game state information
            deck: Current deck state
            spr: Stack-to-pot ratio
            pot_size: Current pot size
            
        Returns:
            Decision string: "fold", "call", or "raise"
        """
        # In a real implementation, this would get input from the UI
        # For this example, we'll simulate a decision
        
        # Here we would show options to the player and get their choice
        # ...
        
        # For demo purposes, we'll just return "call"
        decision = "call"
        
        # Track the decision for learning statistics
        hooks = get_game_engine_hooks()
        decision_data = hooks.track_human_decision(
            player_id=self.player_id,
            decision=decision,
            hole_cards=self.hole_cards,
            game_state=game_state,
            deck=deck,
            pot_size=pot_size,
            spr=spr
        )
        
        # Log the decision analysis
        logger.info(f"Decision analysis: {decision_data['matching_strategy']} - " +
                   f"Optimal: {decision_data['was_optimal']}")
        
        return decision

def patch_poker_game():
    """
    Patch the PokerGame class to add hooks for learning statistics.
    This is a non-intrusive way to add functionality without heavily
    modifying the original code.
    """
    original_init = PokerGame.__init__
    original_play_hand = PokerGame.play_hand
    original_betting_round = PokerGame.betting_round
    
    def patched_init(self, *args, **kwargs):
        """Patched initialization method."""
        original_init(self, *args, **kwargs)
        self.hooks = get_game_engine_hooks()
        self.current_session_id = self.hooks.start_session()
        
    def patched_play_hand(self):
        """Patched play_hand method to track hands."""
        # Start tracking the hand
        hand_id = self.hooks.start_hand()
        
        # Call original method
        result = original_play_hand(self)
        
        # End tracking with winners
        winners = {}
        for player in self.players:
            if player.is_active:
                winners[player.player_id] = player.stack
                
        self.hooks.end_hand(winners)
        
        return result
        
    def patched_betting_round(self):
        """Patched betting_round method to capture game state."""
        # Update the hand data with current state
        if self.hooks.current_hand_id:
            self.hooks.hand_data["community_cards"] = self.community_cards
            self.hooks.hand_data["pot_size"] = self.pot
            self.hooks.hand_data["current_bet"] = self.current_bet
            
        # Call original method
        return original_betting_round(self)
    
    # Apply the patches
    PokerGame.__init__ = patched_init
    PokerGame.play_hand = patched_play_hand
    PokerGame.betting_round = patched_betting_round
    
    logger.info("Poker game patched with learning statistics hooks")

def show_learning_feedback(player_id: str):
    """Display learning feedback for a player."""
    hooks = get_game_engine_hooks()
    feedback = hooks.get_learning_feedback(player_id)
    
    print("\n=== Learning Feedback ===")
    for i, msg in enumerate(feedback, 1):
        print(f"{i}. {msg}")
    
    profile = hooks.get_strategy_profile(player_id)
    
    print("\n=== Strategy Profile ===")
    print(f"Dominant strategy: {profile['dominant_strategy']}")
    print(f"Recommended strategy: {profile['recommended_strategy']}")
    print(f"Decision accuracy: {profile['decision_accuracy']:.1f}%")
    print(f"Positive EV decisions: {profile['ev_ratio']:.1f}%")
    print(f"Total decisions analyzed: {profile['total_decisions']}")
    
    print("\nStrategy distribution:")
    for strategy, percentage in profile['strategy_distribution'].items():
        print(f"  {strategy}: {percentage:.1f}%")

def main():
    """Example of integrating learning statistics with the game engine."""
    # Patch the PokerGame class
    patch_poker_game()
    
    # Create a game with a human player and AI players
    human_player = HumanPlayer(player_id="human_player")
    
    # In a real implementation, you would:
    # 1. Create AI players
    # 2. Initialize a PokerGame with all players
    # 3. Play multiple hands
    # 4. Show learning statistics at the end
    
    # Here's a simplified example:
    from ai.ai_manager import AIDecisionMaker
    from deck_manager import DeckManager
    import config
    from ai.strategies.conservative import ConservativeStrategy
    
    # Simulate a decision analysis
    hooks = get_game_engine_hooks()
    deck_manager = DeckManager()
    deck = deck_manager.get_deck()
    
    # Simulate a hand
    human_hole_cards = ["Ah", "Kh"]
    community_cards = ["7s", "8d", "Qc"]
    
    # Create a game state similar to what would be in the real game
    game_state = {
        "hand_id": "sample_hand_1",
        "community_cards": community_cards,
        "current_bet": 20,
        "game_state": "flop"
    }
    
    # Track a sample human decision
    decision_data = hooks.track_human_decision(
        player_id="human_player",
        decision="call",
        hole_cards=human_hole_cards,
        game_state=game_state,
        deck=deck,
        pot_size=100,
        spr=5.0
    )
    
    # Show feedback
    print("\nDecision Analysis:")
    print(f"Your decision: call")
    print(f"Hole cards: {', '.join(human_hole_cards)}")
    print(f"Community cards: {', '.join(community_cards)}")
    print(f"Your play style matches: {decision_data['matching_strategy']}")
    print(f"Optimal strategy: {decision_data['optimal_strategy']}")
    print(f"Was optimal: {'Yes' if decision_data['was_optimal'] else 'No'}")
    
    # After the game, show learning feedback
    show_learning_feedback("human_player")
    
    # In a real implementation, you would end the session
    hooks.end_session(hooks.stats_manager.current_session_id)

if __name__ == "__main__":
    main()