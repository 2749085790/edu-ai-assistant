"""
API 路由 - 个性化推荐
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_ai_client, get_prompt_manager
from src.api.models.schemas import LearningPathRequest, PathProgressUpdate
from src.core.personalization.learning_path import LearningPathPlanner
from src.core.personalization.adaptive_engine import AdaptiveEngine
from src.services.ai_client import AIClient
from src.utils.prompt_manager import PromptManager

router = APIRouter()


@router.post("/path", summary="生成学习路径")
async def create_learning_path(
    req: LearningPathRequest,
    db: AsyncSession = Depends(get_db),
    ai_client: AIClient = Depends(get_ai_client),
    pm: PromptManager = Depends(get_prompt_manager),
):
    """
    AI 生成个性化学习路径

    基于学生知识状态和学习目标，规划最优学习路径。
    遵循掌握学习理论和最近发展区原则。
    """
    planner = LearningPathPlanner(db, ai_client, pm)

    result = await planner.plan_path(
        student_id=req.student_id,
        subject=req.subject,
        learning_objective=req.learning_objective,
        time_constraint=req.time_constraint,
        learning_style=req.learning_style,
    )

    return {"success": True, "data": result}


@router.get("/path/{path_id}", summary="获取路径详情")
async def get_learning_path(
    path_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取学习路径详情"""
    from sqlalchemy import select
    from src.db.models import LearningPath

    result = await db.execute(select(LearningPath).where(LearningPath.id == path_id))
    path = result.scalars().first()
    if not path:
        raise HTTPException(status_code=404, detail="学习路径不存在")

    return {
        "id": path.id,
        "student_id": path.student_id,
        "subject": path.subject,
        "learning_objective": path.learning_objective,
        "estimated_duration": path.estimated_duration,
        "stages": path.stages or [],
        "current_stage": path.current_stage,
        "progress_percent": path.progress_percent,
        "alternative_paths": path.alternative_paths,
        "motivation_design": path.motivation_design,
        "is_active": path.is_active,
        "created_at": path.created_at.isoformat() if path.created_at else None,
    }


@router.put("/path/{path_id}/progress", summary="更新路径进度")
async def update_path_progress(
    path_id: str,
    data: PathProgressUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新学习路径进度"""
    planner = LearningPathPlanner(db)
    result = await planner.update_progress(
        path_id=path_id,
        current_stage=data.current_stage,
        progress_percent=data.progress_percent,
        mastery_scores=data.mastery_scores,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return {"success": True, "data": result}


@router.get("/student/{student_id}/active-path", summary="获取活跃路径")
async def get_active_path(
    student_id: str,
    subject: str = None,
    db: AsyncSession = Depends(get_db),
):
    """获取学生当前活跃的学习路径"""
    planner = LearningPathPlanner(db)
    path = await planner.get_active_path(student_id, subject)
    if not path:
        return {"data": None, "message": "暂无活跃学习路径"}
    return {"data": path}


@router.get("/student/{student_id}/recommendations", summary="资源推荐")
async def get_resource_recommendations(
    student_id: str,
    subject: str = "数学",
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """基于学生知识状态推荐学习资源"""
    engine = AdaptiveEngine(db)
    recommendations = await engine.recommend_resources(student_id, subject, limit)
    return {"items": recommendations, "total": len(recommendations)}


@router.get("/student/{student_id}/review-schedule", summary="复习计划")
async def get_review_schedule(
    student_id: str,
    subject: str = "数学",
    db: AsyncSession = Depends(get_db),
):
    """获取基于间隔重复的复习计划"""
    engine = AdaptiveEngine(db)
    schedule = await engine.schedule_review(student_id, subject)
    return {"items": schedule, "total": len(schedule)}


@router.post("/student/{student_id}/adjust-difficulty", summary="难度调整")
async def adjust_difficulty(
    student_id: str,
    subject: str = "数学",
    knowledge_point: str = "",
    recent_accuracy: float = 0.7,
    db: AsyncSession = Depends(get_db),
):
    """根据最近表现动态调整难度"""
    engine = AdaptiveEngine(db)
    result = await engine.adjust_difficulty(
        student_id=student_id,
        subject=subject,
        knowledge_point=knowledge_point,
        recent_accuracy=recent_accuracy,
    )
    return {"success": True, "data": result}
