"""
教培 AI 智能备课与学情分析系统 - FastAPI 应用入口
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.db.database import init_db, close_db
from src.api.routes import lesson_prep, analytics, personalization, students, paper_scan
from src.api.middleware.auth import APIKeyMiddleware

load_dotenv()

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("正在启动教培 AI 智能备课与学情分析系统...")
    await init_db()
    logger.info("数据库初始化完成")
    yield
    logger.info("正在关闭系统...")
    await close_db()
    logger.info("系统已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="教培 AI 智能备课与学情分析系统",
    description=(
        "面向教培行业的 AI 驱动备课工具与学情分析平台。\n\n"
        "核心功能模块：\n"
        "- **AI 智能备课系统** - 自动生成教案、课件、习题\n"
        "- **学情分析引擎** - 多维度学习数据洞察\n"
        "- **个性化推荐系统** - 精准学习路径规划"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key 认证中间件
app.add_middleware(APIKeyMiddleware)

# 注册路由
app.include_router(
    students.router,
    prefix="/api/v1/students",
    tags=["学生管理"],
)
app.include_router(
    lesson_prep.router,
    prefix="/api/v1/lesson-prep",
    tags=["智能备课"],
)
app.include_router(
    analytics.router,
    prefix="/api/v1/analytics",
    tags=["学情分析"],
)
app.include_router(
    personalization.router,
    prefix="/api/v1/personalization",
    tags=["个性化推荐"],
)
app.include_router(
    paper_scan.router,
    prefix="/api/v1/paper-scan",
    tags=["试卷扫描"],
)


@app.get("/", tags=["系统"])
async def root():
    """系统健康检查"""
    return {
        "name": "教培 AI 智能备课与学情分析系统",
        "version": "1.0.0",
        "status": "running",
        "modules": [
            "智能备课系统",
            "学情分析引擎",
            "个性化推荐系统",
        ],
    }


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
