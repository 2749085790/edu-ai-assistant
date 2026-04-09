"""
API 路由 - 智能备课
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_ai_client, get_prompt_manager
from src.api.models.schemas import (
    LessonPlanRequest, LessonPlanResponse, QuizGenerateRequest, QuizResponse,
)
from src.db.models import LessonPlan, Question
from src.core.lesson_prep.content_generator import ContentGenerator
from src.core.lesson_prep.quiz_designer import QuizDesigner
from src.core.lesson_prep.material_curator import MaterialCurator
from src.services.ai_client import AIClient
from src.utils.prompt_manager import PromptManager

router = APIRouter()


@router.post("/generate", summary="生成教案")
async def generate_lesson_plan(
    req: LessonPlanRequest,
    db: AsyncSession = Depends(get_db),
    ai_client: AIClient = Depends(get_ai_client),
    pm: PromptManager = Depends(get_prompt_manager),
):
    """
    AI 生成完整教案

    输入课题信息，自动生成包含教学目标、教学过程、分层作业的完整教案。
    """
    generator = ContentGenerator(ai_client, pm)

    result = await generator.generate_lesson_plan(
        subject=req.subject,
        grade=req.grade,
        topic=req.topic,
        duration=req.duration,
        lesson_type=req.lesson_type.value,
        student_level=req.student_level.value,
        special_requirements=req.special_requirements,
        existing_materials=req.existing_materials,
    )

    # 持久化教案
    plan = LessonPlan(
        id=result["id"],
        teacher_id=req.teacher_id,
        subject=req.subject,
        grade=req.grade,
        topic=req.topic,
        duration=req.duration,
        lesson_type=req.lesson_type.value,
        student_level=req.student_level.value,
        objectives=result.get("objectives"),
        key_points=result.get("key_points"),
        teaching_process=result.get("teaching_process"),
        differentiated_strategies=result.get("differentiated_strategies"),
        board_design=result.get("board_design", ""),
        homework_design=result.get("homework_design"),
        full_content=result.get("full_content", ""),
        ai_confidence=result.get("ai_confidence", 0),
        special_requirements=req.special_requirements,
    )
    db.add(plan)

    return {
        "success": True,
        "data": result,
    }


@router.post("/quiz", summary="生成习题")
async def generate_quiz(
    req: QuizGenerateRequest,
    db: AsyncSession = Depends(get_db),
    ai_client: AIClient = Depends(get_ai_client),
    pm: PromptManager = Depends(get_prompt_manager),
):
    """
    AI 生成分层习题

    基于 SOLO 分类理论，生成难度递进的多层次习题集。
    """
    designer = QuizDesigner(ai_client, pm)

    result = await designer.generate_layered_quiz(
        subject=req.subject,
        knowledge_point=req.knowledge_point,
        basic_percent=req.basic_percent,
        intermediate_percent=req.intermediate_percent,
        advanced_percent=req.advanced_percent,
        question_types=req.question_types,
        count=req.count,
        difficulty_range=req.difficulty_range,
        student_profile=req.student_profile,
    )

    return {
        "success": True,
        "data": result,
    }


@router.get("/plans", summary="获取教案列表")
async def list_lesson_plans(
    subject: str = None,
    grade: str = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """获取已生成的教案列表"""
    query = select(LessonPlan).order_by(LessonPlan.created_at.desc())
    if subject:
        query = query.where(LessonPlan.subject == subject)
    if grade:
        query = query.where(LessonPlan.grade == grade)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    plans = result.scalars().all()

    return {
        "items": [
            {
                "id": p.id,
                "subject": p.subject,
                "grade": p.grade,
                "topic": p.topic,
                "duration": p.duration,
                "lesson_type": p.lesson_type.value if p.lesson_type else "",
                "ai_confidence": p.ai_confidence,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in plans
        ],
        "page": page,
        "page_size": page_size,
    }


@router.get("/plans/{plan_id}", summary="获取教案详情")
async def get_lesson_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取指定教案的完整内容"""
    result = await db.execute(select(LessonPlan).where(LessonPlan.id == plan_id))
    plan = result.scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="教案不存在")

    return {
        "id": plan.id,
        "subject": plan.subject,
        "grade": plan.grade,
        "topic": plan.topic,
        "duration": plan.duration,
        "lesson_type": plan.lesson_type.value if plan.lesson_type else "",
        "objectives": plan.objectives,
        "key_points": plan.key_points,
        "teaching_process": plan.teaching_process,
        "differentiated_strategies": plan.differentiated_strategies,
        "board_design": plan.board_design,
        "homework_design": plan.homework_design,
        "full_content": plan.full_content,
        "ai_confidence": plan.ai_confidence,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
    }


@router.get("/materials", summary="搜索教学素材")
async def search_materials(
    subject: str,
    grade: str = None,
    material_type: str = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """搜索教学素材资源"""
    curator = MaterialCurator(db)
    materials = await curator.search_materials(
        subject=subject,
        grade=grade,
        material_type=material_type,
        limit=limit,
    )
    return {"items": materials, "total": len(materials)}
