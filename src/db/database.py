"""
教培 AI 智能备课与学情分析系统 - 数据库连接配置
SQLAlchemy 异步引擎 + 会话管理
支持 PostgreSQL（生产）和 SQLite（本地开发）
"""

import os
from pathlib import Path
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# 构建数据库 URL —— 优先读取 DATABASE_URL，其次组装 PG，兜底 SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "edu_ai_assistant")

    if DB_HOST and DB_USER:
        DATABASE_URL = (
            f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
    else:
        # 本地开发降级为 SQLite（aiosqlite 异步驱动）
        _db_path = Path(__file__).resolve().parent.parent.parent / "data" / "dev.db"
        _db_path.parent.mkdir(parents=True, exist_ok=True)
        DATABASE_URL = f"sqlite+aiosqlite:///{_db_path}"

_is_sqlite = DATABASE_URL.startswith("sqlite")

# 创建异步引擎
_engine_kwargs = dict(
    echo=os.getenv("DEBUG", "false").lower() == "true",
)
if not _is_sqlite:
    _engine_kwargs.update(pool_size=10, max_overflow=20, pool_pre_ping=True)

engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

# 创建异步会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass


async def get_db_session() -> AsyncSession:
    """获取数据库会话（用于依赖注入）"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接池"""
    await engine.dispose()
