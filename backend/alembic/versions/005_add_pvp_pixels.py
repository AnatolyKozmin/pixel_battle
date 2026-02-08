"""Add PvP pixels fields

Revision ID: 005_add_pvp_pixels
Revises: 004_change_game_enums_to_string
Create Date: 2024-01-16 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_pvp_pixels'
down_revision = '004_change_game_enums_to_string'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Добавляем поля для новой механики PvP
    op.add_column('game_sessions', sa.Column('player1_pixels', sa.JSON(), nullable=True))
    op.add_column('game_sessions', sa.Column('player2_pixels', sa.JSON(), nullable=True))
    op.add_column('game_sessions', sa.Column('pixels_to_place', sa.Integer(), nullable=True))
    op.add_column('game_sessions', sa.Column('winner_id', sa.Integer(), nullable=True))
    
    # Создаём внешний ключ для winner_id
    op.create_foreign_key(
        'fk_game_sessions_winner_id',
        'game_sessions', 'users',
        ['winner_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Устанавливаем значения по умолчанию
    op.execute("UPDATE game_sessions SET player1_pixels = '[]' WHERE player1_pixels IS NULL")
    op.execute("UPDATE game_sessions SET player2_pixels = '[]' WHERE player2_pixels IS NULL")
    op.execute("UPDATE game_sessions SET pixels_to_place = 5 WHERE pixels_to_place IS NULL AND mode = 'pvp'")


def downgrade() -> None:
    op.drop_constraint('fk_game_sessions_winner_id', 'game_sessions', type_='foreignkey')
    op.drop_column('game_sessions', 'winner_id')
    op.drop_column('game_sessions', 'pixels_to_place')
    op.drop_column('game_sessions', 'player2_pixels')
    op.drop_column('game_sessions', 'player1_pixels')
