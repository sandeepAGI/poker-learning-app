"""
Database session management and utilities.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sandeepmangaraj@localhost:5432/poker_dev")

# Create engine with connection timeout for Azure
# pool_pre_ping=True validates connections, connect_timeout prevents hanging
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "connect_timeout": 10,  # 10 second timeout for initial connection
        "options": "-c statement_timeout=30000"  # 30s query timeout
    },
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600  # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI dependency for database sessions.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """
    Context manager for database sessions.
    Usage: with get_db_context() as db:
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database (create tables)."""
    from models import Base
    Base.metadata.create_all(bind=engine)

# Hand persistence
from dataclasses import asdict
from typing import TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from game.poker_engine import CompletedHand

logger = logging.getLogger(__name__)

def save_completed_hand(game_id: str, completed_hand: "CompletedHand", user_id: str, db: Session = None) -> None:
    """
    Save completed hand to database.

    Args:
        game_id: Game ID
        completed_hand: CompletedHand dataclass from poker_engine
        user_id: User ID who played the hand
        db: Optional database session (for testing). If None, creates new session.
    """
    try:
        from models import Hand, Game

        # Use provided session or create new one
        if db is not None:
            # Check if hand already saved (deduplication)
            existing = db.query(Hand).filter(
                Hand.game_id == game_id,
                Hand.hand_number == completed_hand.hand_number
            ).first()
            if existing:
                return  # Already saved, skip

            # Use provided session (for testing)
            hand_data = asdict(completed_hand)

            hand = Hand(
                game_id=game_id,
                user_id=user_id,
                hand_number=completed_hand.hand_number,
                hand_data=hand_data,
                user_hole_cards=",".join(completed_hand.human_cards) if completed_hand.human_cards else None,
                user_won="human" in completed_hand.winner_ids,
                pot=completed_hand.pot_size
            )
            db.add(hand)

            # Update game total_hands
            game = db.query(Game).filter(Game.game_id == game_id).first()
            if game:
                game.total_hands = (game.total_hands or 0) + 1

            db.commit()
        else:
            # Create new session (production)
            with get_db_context() as db:
                # Check if hand already saved (deduplication)
                existing = db.query(Hand).filter(
                    Hand.game_id == game_id,
                    Hand.hand_number == completed_hand.hand_number
                ).first()
                if existing:
                    return  # Already saved, skip

                hand_data = asdict(completed_hand)

                hand = Hand(
                    game_id=game_id,
                    user_id=user_id,
                    hand_number=completed_hand.hand_number,
                    hand_data=hand_data,
                    user_hole_cards=",".join(completed_hand.human_cards) if completed_hand.human_cards else None,
                    user_won="human" in completed_hand.winner_ids,
                    pot=completed_hand.pot_size
                )
                db.add(hand)

                # Update game total_hands
                game = db.query(Game).filter(Game.game_id == game_id).first()
                if game:
                    game.total_hands = (game.total_hands or 0) + 1

                db.commit()
    except Exception as e:
        # Don't crash game if database save fails
        logger.error(f"Failed to save hand to database: {e}")
        logger.exception(e)
