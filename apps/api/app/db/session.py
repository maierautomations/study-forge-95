"""Database session management using asyncpg"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import asyncpg

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def create_db_pool() -> asyncpg.Pool:
    """Create database connection pool"""
    try:
        pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=1,
            max_size=10,
            max_queries=50000,
            max_inactive_connection_lifetime=300,
            command_timeout=60,
        )
        logger.info("Database connection pool created successfully")
        return pool
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        raise


async def close_db_pool() -> None:
    """Close database connection pool"""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("Database connection pool closed")


async def get_db_pool() -> asyncpg.Pool:
    """Get database connection pool"""
    global _pool
    if not _pool:
        _pool = await create_db_pool()
    return _pool


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get database connection from pool"""
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise


async def test_db_connection() -> bool:
    """Test database connectivity"""
    try:
        async with get_db_connection() as conn:
            result = await conn.fetchval("SELECT 1")
            return result == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


async def execute_query(
    query: str, 
    *args, 
    fetch_one: bool = False,
    fetch_all: bool = False
) -> Optional[any]:
    """Execute database query with connection from pool"""
    async with get_db_connection() as conn:
        if fetch_one:
            return await conn.fetchrow(query, *args)
        elif fetch_all:
            return await conn.fetch(query, *args)
        else:
            return await conn.execute(query, *args)


async def execute_many(query: str, args_list: list) -> None:
    """Execute many queries with same statement"""
    async with get_db_connection() as conn:
        await conn.executemany(query, args_list)


# Database initialization for FastAPI lifespan
async def init_database():
    """Initialize database connections"""
    global _pool
    try:
        # Only initialize if DATABASE_URL is properly configured
        from app.core.config import get_settings
        settings = get_settings()
        
        if not settings.database_url or settings.database_url.startswith("postgresql://postgres:password@"):
            logger.warning("Database not configured, skipping database initialization")
            return
            
        _pool = await create_db_pool()
        
        # Test connection
        is_connected = await test_db_connection()
        if not is_connected:
            raise Exception("Database connection test failed")
            
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Continuing without database connection for testing purposes")
        # Don't raise in development - allow server to start


async def cleanup_database():
    """Cleanup database connections"""
    await close_db_pool()
    logger.info("Database cleanup completed")