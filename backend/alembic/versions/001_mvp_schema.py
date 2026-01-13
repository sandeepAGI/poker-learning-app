"""MVP schema: users, games, hands, analysis_cache

Revision ID: 001
Revises:
Create Date: 2026-01-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users table
    op.create_table('users',
        sa.Column('user_id', sa.String(50), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.TIMESTAMP()),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('username')
    )
    op.create_index('idx_users_username', 'users', ['username'])

    # Games table
    op.create_table('games',
        sa.Column('game_id', sa.String(50), nullable=False),
        sa.Column('user_id', sa.String(50), nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.TIMESTAMP()),
        sa.Column('num_ai_players', sa.Integer()),
        sa.Column('starting_stack', sa.Integer()),
        sa.Column('final_stack', sa.Integer()),
        sa.Column('profit_loss', sa.Integer()),
        sa.Column('total_hands', sa.Integer(), server_default='0'),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.PrimaryKeyConstraint('game_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE')
    )
    op.create_index('idx_games_user_started', 'games', ['user_id', 'started_at'])

    # Hands table
    op.create_table('hands',
        sa.Column('hand_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('game_id', sa.String(50), nullable=False),
        sa.Column('user_id', sa.String(50), nullable=False),
        sa.Column('hand_number', sa.Integer(), nullable=False),
        sa.Column('hand_data', postgresql.JSONB(), nullable=False),
        sa.Column('user_hole_cards', sa.String(10)),
        sa.Column('user_won', sa.Boolean()),
        sa.Column('pot', sa.Integer()),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('hand_id'),
        sa.ForeignKeyConstraint(['game_id'], ['games.game_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE')
    )
    op.create_index('idx_hands_game', 'hands', ['game_id', 'hand_number'])
    op.create_index('idx_hands_user', 'hands', ['user_id', 'created_at'])

    # Analysis cache table
    op.create_table('analysis_cache',
        sa.Column('cache_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(50), nullable=False),
        sa.Column('hand_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_type', sa.String(20), nullable=False),
        sa.Column('model_used', sa.String(50), nullable=False),
        sa.Column('cost', sa.Float(), nullable=False),
        sa.Column('analysis_data', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('cache_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['hand_id'], ['hands.hand_id'], ondelete='CASCADE')
    )
    op.create_index('idx_analysis_user_hand', 'analysis_cache', ['user_id', 'hand_id', 'analysis_type'], unique=True)


def downgrade():
    op.drop_table('analysis_cache')
    op.drop_table('hands')
    op.drop_table('games')
    op.drop_table('users')
