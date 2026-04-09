"""
教培 AI 智能备课与学情分析系统 - 依赖注入
FastAPI 依赖项：DB Session、AI Client、Config、PromptManager
"""

import os
import yaml
from typing import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_db_session
from src.services.ai_client import AIClient
from src.utils.prompt_manager import PromptManager


# --------------- 配置加载 ---------------

@lru_cache()
def get_config() -> dict:
    """加载并缓存全局配置"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config.yaml",
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# --------------- 数据库会话 ---------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """依赖注入：获取异步数据库会话"""
    async for session in get_db_session():
        yield session


# --------------- AI 客户端 ---------------

_ai_client: AIClient | None = None


def get_ai_client() -> AIClient:
    """依赖注入：获取 AI 客户端单例"""
    global _ai_client
    if _ai_client is None:
        config = get_config()
        _ai_client = AIClient(
            api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            model=config.get("ai", {}).get("model", "qwen-plus"),
            temperature=config.get("ai", {}).get("temperature", 0.7),
            max_tokens=config.get("ai", {}).get("max_tokens", 4096),
        )
    return _ai_client


# --------------- 提示词管理器 ---------------

_prompt_manager: PromptManager | None = None


def get_prompt_manager() -> PromptManager:
    """依赖注入：获取提示词管理器单例"""
    global _prompt_manager
    if _prompt_manager is None:
        config = get_config()
        base_dir = config.get("prompts", {}).get("base_dir", "src/prompts")
        _prompt_manager = PromptManager(base_dir=base_dir)
    return _prompt_manager
