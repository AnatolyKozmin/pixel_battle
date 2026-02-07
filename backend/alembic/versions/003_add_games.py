"""Add games and game results

Revision ID: 003_add_games
Revises: 002_add_teams
Create Date: 2024-01-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_games'
down_revision = '002_add_teams'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание таблицы game_sessions
    op.create_table(
        'game_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('mode', sa.Enum('solo', 'pvp', name='gamemode'), nullable=False),
        sa.Column('status', sa.Enum('waiting', 'in_progress', 'finished', 'cancelled', name='gamestatus'), nullable=False),
        sa.Column('player1_id', sa.Integer(), nullable=False),
        sa.Column('player2_id', sa.Integer(), nullable=True),
        sa.Column('current_level', sa.Integer(), nullable=True),
        sa.Column('grid_size', sa.Integer(), nullable=True),
        sa.Column('sequence', sa.JSON(), nullable=True),
        sa.Column('show_delay_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['player1_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['player2_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_sessions_id'), 'game_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_game_sessions_code'), 'game_sessions', ['code'], unique=True)
    
    # Создание таблицы game_results
    op.create_table(
        'game_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_session_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('level_reached', sa.Integer(), nullable=False),
        sa.Column('correct_answers', sa.Integer(), nullable=True),
        sa.Column('errors', sa.Integer(), nullable=True),
        sa.Column('play_time_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['game_session_id'], ['game_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_results_id'), 'game_results', ['id'], unique=False)
    op.create_index('ix_game_results_user_level', 'game_results', ['user_id', 'level_reached'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_game_results_user_level', table_name='game_results')
    op.drop_index(op.f('ix_game_results_id'), table_name='game_results')
    op.drop_table('game_results')
    op.drop_index(op.f('ix_game_sessions_code'), table_name='game_sessions')
    op.drop_index(op.f('ix_game_sessions_id'), table_name='game_sessions')
    op.drop_table('game_sessions')
    op.execute('DROP TYPE IF EXISTS gamestatus')
    op.execute('DROP TYPE IF EXISTS gamemode')
