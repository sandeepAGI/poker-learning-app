"""
SQLAlchemy ORM models for MVP database schema.
Matches alembic/versions/001_mvp_schema.py structure.
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    """User accounts table."""
    __tablename__ = 'users'

    user_id = Column(String(50), primary_key=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    last_login = Column(TIMESTAMP)

class Game(Base):
    """Game sessions table."""
    __tablename__ = 'games'

    game_id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    started_at = Column(TIMESTAMP, server_default=func.current_timestamp(), index=True)
    completed_at = Column(TIMESTAMP)
    num_ai_players = Column(Integer)
    starting_stack = Column(Integer)
    final_stack = Column(Integer)
    profit_loss = Column(Integer)
    total_hands = Column(Integer, server_default='0')
    status = Column(String(20), server_default='active')

class Hand(Base):
    """Individual hands table."""
    __tablename__ = 'hands'

    hand_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    game_id = Column(String(50), ForeignKey('games.game_id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, index=True)
    hand_number = Column(Integer, nullable=False)
    hand_data = Column(JSONB, nullable=False)
    user_hole_cards = Column(String(10))
    user_won = Column(Boolean)
    pot = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

class AnalysisCache(Base):
    """AI analysis cache table."""
    __tablename__ = 'analysis_cache'
    __table_args__ = (
        UniqueConstraint('user_id', 'hand_id', 'analysis_type', name='idx_analysis_user_hand'),
    )

    cache_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    user_id = Column(String(50), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    hand_id = Column(UUID(as_uuid=True), ForeignKey('hands.hand_id', ondelete='CASCADE'), nullable=False)
    analysis_type = Column(String(20), nullable=False)
    model_used = Column(String(50), nullable=False)
    cost = Column(Float, nullable=False)
    analysis_data = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
