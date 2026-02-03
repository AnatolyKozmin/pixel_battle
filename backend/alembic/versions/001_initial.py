"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создание таблицы users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('pixels_placed', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_pixel_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)
    
    # Создание таблицы pixels
    op.create_table(
        'pixels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('x', sa.Integer(), nullable=False),
        sa.Column('y', sa.Integer(), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pixels_id'), 'pixels', ['id'], unique=False)
    op.create_index(op.f('ix_pixels_x'), 'pixels', ['x'], unique=False)
    op.create_index(op.f('ix_pixels_y'), 'pixels', ['y'], unique=False)
    op.create_index(op.f('ix_pixels_user_id'), 'pixels', ['user_id'], unique=False)
    op.create_index('idx_pixel_coords', 'pixels', ['x', 'y'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_pixel_coords', table_name='pixels')
    op.drop_index(op.f('ix_pixels_user_id'), table_name='pixels')
    op.drop_index(op.f('ix_pixels_y'), table_name='pixels')
    op.drop_index(op.f('ix_pixels_x'), table_name='pixels')
    op.drop_index(op.f('ix_pixels_id'), table_name='pixels')
    op.drop_table('pixels')
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
