"""
Настройка подключения к базе данных
Поддержка master/replica через pgbouncer
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings


# Master engine (для записи)
master_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=False,
    pool_label="master"
)

# Replica engine (для чтения)
# Если DATABASE_REPLICA_URL не указан, используем master для всех операций
replica_url = settings.DATABASE_REPLICA_URL or settings.DATABASE_URL
replica_engine = create_async_engine(
    replica_url,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=False,
    pool_label="replica"
)

# Сессии для master и replica
MasterSessionLocal = async_sessionmaker(
    master_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

ReplicaSessionLocal = async_sessionmaker(
    replica_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Для обратной совместимости используем master как основной engine
engine = master_engine
AsyncSessionLocal = MasterSessionLocal

Base = declarative_base()


async def get_db():
    """
    Dependency для получения сессии БД (master - для записи)
    Используется для операций записи (размещение пикселей, обновление статистики)
    """
    async with MasterSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_read():
    """
    Dependency для получения сессии БД (replica - для чтения)
    Используется для операций чтения (получение холста, статистики)
    """
    async with ReplicaSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
