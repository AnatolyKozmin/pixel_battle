"""Change game enums to string type

Revision ID: 004_change_game_enums_to_string
Revises: 003_add_games
Create Date: 2024-01-16 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_change_game_enums_to_string'
down_revision = '003_add_games'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Изменяем тип колонки mode с enum на VARCHAR
    op.execute("ALTER TABLE game_sessions ALTER COLUMN mode TYPE VARCHAR USING mode::text")
    
    # Изменяем тип колонки status с enum на VARCHAR
    op.execute("ALTER TABLE game_sessions ALTER COLUMN status TYPE VARCHAR USING status::text")
    
    # Удаляем типы enum (опционально, можно оставить для отката)
    # op.execute('DROP TYPE IF EXISTS gamemode')
    # op.execute('DROP TYPE IF EXISTS gamestatus')


def downgrade() -> None:
    # Восстанавливаем enum типы
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE gamemode AS ENUM ('solo', 'pvp');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE gamestatus AS ENUM ('waiting', 'in_progress', 'finished', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Изменяем тип колонки mode обратно на enum
    op.execute("ALTER TABLE game_sessions ALTER COLUMN mode TYPE gamemode USING mode::gamemode")
    
    # Изменяем тип колонки status обратно на enum
    op.execute("ALTER TABLE game_sessions ALTER COLUMN status TYPE gamestatus USING status::gamestatus")
