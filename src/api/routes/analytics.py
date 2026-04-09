"""
API 路由 - 学情分析
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_ai_client, get_prompt_manager
from src.api.models.schemas import PerformanceRecord
from src.db.models import Student, StudentPerformance
from src.core.analytics.performance_tracker import PerformanceTracker
from src.core.analytics.knowledge_mapper import KnowledgeMapper
from src.core.analytics.risk_predictor import RiskPredictor
from src.services.ai_client import AIClient
from src.utils.prompt_manager import PromptManager

import uuid

router = APIRouter()


@router.get("/student/{student_id}/portrait", summary="学习画像")
async def get_learning_portrait(
    student_id: str,
    subject: str = "数学",
    db: AsyncSession = Depends(get_db),
    ai_client: AIClient = Depends(get_ai_client),
    pm: PromptManager = Depends(get_prompt_manager),
):
    """
    获取学生完整学习画像分析报告

    包含：学业成就、知识诊断、能力评估、行为洞察、风险预警、个性化建议
    """
    # 验证学生
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalars().first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 各模块分析
    tracker = PerformanceTracker(db)
    mapper = KnowledgeMapper(db, ai_client, pm)
    predictor = RiskPredictor(db, ai_client, pm)

    performance = await tracker.track_performance(student_id, subject)
    knowledge_graph = await mapper.build_knowledge_graph(student_id, subject)
    gaps = await mapper.diagnose_gaps(student_id, subject)
    risk = await predictor.predict_risk(student_id, subject)

    # AI 诊断摘要
    ai_summary = ""
    if ai_client:
        try:
            ai_summary = await mapper.generate_ai_diagnosis(student_id, subject)
        except Exception:
            ai_summary = "AI 诊断暂不可用"

    return {
        "student_id": student_id,
        "student_name": student.name,
        "subject": subject,
        "academic_achievement": {
            "current_score": performance.get("current_score", 0),
            "average_score": performance.get("average_score", 0),
            "trend": performance.get("trend", "无数据"),
            "percentile": performance.get("percentile", 0),
        },
        "knowledge_diagnosis": {
            "overall_mastery": knowledge_graph.get("overall_mastery", 0),
            "category_mastery": knowledge_graph.get("category_mastery", {}),
            "mastered": gaps.get("mastered", []),
            "weak_points": gaps.get("weak_points", []),
            "gaps": gaps.get("gaps", []),
            "prerequisite_gaps": gaps.get("prerequisite_gaps", []),
        },
        "risk_warning": risk,
        "ai_summary": ai_summary,
    }


@router.get("/student/{student_id}/performance", summary="成绩趋势")
async def get_performance_trend(
    student_id: str,
    subject: str = "数学",
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """获取学生成绩趋势分析"""
    tracker = PerformanceTracker(db)
    return await tracker.track_performance(student_id, subject, limit)


@router.post("/student/performance", summary="录入成绩")
async def record_performance(
    data: PerformanceRecord,
    db: AsyncSession = Depends(get_db),
):
    """录入学生考试成绩"""
    record = StudentPerformance(
        id=str(uuid.uuid4()),
        student_id=data.student_id,
        subject=data.subject,
        exam_name=data.exam_name,
        score=data.score,
        total_score=data.total_score,
        knowledge_detail=data.knowledge_detail,
        exam_date=data.exam_date,
    )
    db.add(record)
    return {"success": True, "id": record.id}


@router.get("/student/{student_id}/knowledge-map", summary="知识图谱")
async def get_knowledge_map(
    student_id: str,
    subject: str = "数学",
    db: AsyncSession = Depends(get_db),
    ai_client: AIClient = Depends(get_ai_client),
    pm: PromptManager = Depends(get_prompt_manager),
):
    """获取学生知识图谱诊断"""
    mapper = KnowledgeMapper(db, ai_client, pm)
    graph = await mapper.build_knowledge_graph(student_id, subject)
    gaps = await mapper.diagnose_gaps(student_id, subject)

    return {
        "knowledge_graph": graph,
        "diagnosis": gaps,
    }


@router.get("/risk-alerts", summary="风险预警列表")
async def get_risk_alerts(
    risk_level: str = None,
    is_resolved: bool = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """获取学生学习风险预警列表"""
    predictor = RiskPredictor(db)
    alerts = await predictor.get_risk_alerts(
        is_resolved=is_resolved,
        risk_level=risk_level,
        limit=limit,
    )
    return {"items": alerts, "total": len(alerts)}


@router.post("/student/{student_id}/risk-predict", summary="触发风险评估")
async def trigger_risk_prediction(
    student_id: str,
    subject: str = "数学",
    db: AsyncSession = Depends(get_db),
    ai_client: AIClient = Depends(get_ai_client),
    pm: PromptManager = Depends(get_prompt_manager),
):
    """手动触发学生风险评估"""
    predictor = RiskPredictor(db, ai_client, pm)
    result = await predictor.predict_risk(student_id, subject)
    return {"success": True, "data": result}
