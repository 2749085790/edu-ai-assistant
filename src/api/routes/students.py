"""
API 路由 - 学生管理
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_ai_client, get_prompt_manager
from src.api.models.schemas import (
    StudentCreate, StudentResponse, StudentProfile, APIResponse,
)
from src.db.models import Student, KnowledgeState
from src.core.analytics.performance_tracker import PerformanceTracker
from src.core.analytics.knowledge_mapper import KnowledgeMapper
from src.services.ai_client import AIClient
from src.utils.prompt_manager import PromptManager

import uuid

router = APIRouter()


@router.post("", response_model=StudentResponse, summary="创建学生")
async def create_student(
    data: StudentCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建新学生记录"""
    student = Student(
        id=str(uuid.uuid4()),
        name=data.name,
        grade=data.grade,
        class_id=data.class_id,
        school=data.school,
        learning_style=data.learning_style,
    )
    db.add(student)
    await db.flush()
    return student


@router.get("/{student_id}", response_model=StudentResponse, summary="获取学生信息")
async def get_student(
    student_id: str,
    db: AsyncSession = Depends(get_db),
):
    """根据 ID 获取学生信息"""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    return student


@router.get("", summary="获取学生列表")
async def list_students(
    grade: str = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """获取学生列表，支持按年级筛选"""
    query = select(Student)
    if grade:
        query = query.where(Student.grade == grade)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    students = result.scalars().all()

    return {
        "items": [
            {
                "id": s.id,
                "name": s.name,
                "grade": s.grade,
                "school": s.school,
                "learning_style": s.learning_style,
            }
            for s in students
        ],
        "page": page,
        "page_size": page_size,
    }


@router.get("/{student_id}/profile", summary="获取学习画像")
async def get_student_profile(
    student_id: str,
    subject: str = "数学",
    db: AsyncSession = Depends(get_db),
    ai_client: AIClient = Depends(get_ai_client),
    pm: PromptManager = Depends(get_prompt_manager),
):
    """获取学生完整学习画像，包含知识图谱、成绩趋势、能力评估"""
    # 验证学生存在
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 成绩分析
    tracker = PerformanceTracker(db)
    performance = await tracker.track_performance(student_id, subject)

    # 知识图谱
    mapper = KnowledgeMapper(db, ai_client, pm)
    knowledge_graph = await mapper.build_knowledge_graph(student_id, subject)
    gaps = await mapper.diagnose_gaps(student_id, subject)

    # 构建能力雷达图
    ability_radar = knowledge_graph.get("category_mastery", {})

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "grade": student.grade,
            "school": student.school,
            "learning_style": student.learning_style,
        },
        "knowledge_state": {
            kp: info["mastery"]
            for kp, info in knowledge_graph.get("knowledge_points", {}).items()
        },
        "ability_radar": ability_radar,
        "overall_mastery": knowledge_graph.get("overall_mastery", 0),
        "performance_trend": performance,
        "knowledge_gaps": gaps,
    }
