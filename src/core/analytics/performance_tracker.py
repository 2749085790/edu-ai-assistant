"""
学情分析引擎 - 成绩追踪与趋势分析
对学生历史成绩进行趋势检测、百分位排名、进退步判断
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import StudentPerformance, Student

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """
    成绩追踪器

    核心功能：
    - track_performance: 获取学生成绩历史及趋势
    - compute_percentile: 计算百分位排名
    - detect_trend: 检测进步/退步趋势
    - get_class_comparison: 班级对比分析
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def track_performance(
        self,
        student_id: str,
        subject: str,
        limit: int = 10,
    ) -> Dict:
        """
        获取学生成绩历史及趋势分析

        Returns:
            {
                "student_id": "...",
                "subject": "...",
                "current_score": 82,
                "average_score": 75,
                "trend": "上升",
                "trend_slope": 2.5,
                "percentile": 78.5,
                "history": [...]
            }
        """
        # 查询成绩记录
        query = (
            select(StudentPerformance)
            .where(
                StudentPerformance.student_id == student_id,
                StudentPerformance.subject == subject,
            )
            .order_by(StudentPerformance.exam_date.asc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        records = result.scalars().all()

        if not records:
            return {
                "student_id": student_id,
                "subject": subject,
                "current_score": 0,
                "average_score": 0,
                "trend": "无数据",
                "trend_slope": 0,
                "percentile": 0,
                "history": [],
            }

        scores = [r.score for r in records]
        current_score = scores[-1]
        average_score = sum(scores) / len(scores)

        # 趋势检测
        trend, slope = self._detect_trend(scores)

        # 百分位排名（使用最新一次考试）
        latest_record = records[-1]
        percentile = await self._compute_percentile(
            subject, latest_record.exam_name, current_score
        )

        history = [
            {
                "exam_name": r.exam_name,
                "score": r.score,
                "total_score": r.total_score,
                "percentile": r.percentile,
                "exam_date": r.exam_date.isoformat() if r.exam_date else None,
            }
            for r in records
        ]

        return {
            "student_id": student_id,
            "subject": subject,
            "current_score": current_score,
            "average_score": round(average_score, 1),
            "trend": trend,
            "trend_slope": round(slope, 2),
            "percentile": round(percentile, 1),
            "history": history,
        }

    async def _compute_percentile(
        self, subject: str, exam_name: str, score: float
    ) -> float:
        """
        计算特定考试中该分数的百分位排名
        percentile = (低于该分数的人数 / 总人数) * 100
        """
        # 该次考试的所有成绩
        query = select(StudentPerformance.score).where(
            StudentPerformance.subject == subject,
            StudentPerformance.exam_name == exam_name,
        )
        result = await self.db.execute(query)
        all_scores = [r[0] for r in result.all()]

        if not all_scores:
            return 0.0

        below_count = sum(1 for s in all_scores if s < score)
        return (below_count / len(all_scores)) * 100

    def _detect_trend(self, scores: List[float], window: int = 5) -> tuple:
        """
        检测成绩趋势

        使用最小二乘法计算线性回归斜率

        Returns:
            (trend_label, slope)
            trend_label: "上升" / "下降" / "稳定"
            slope: 斜率值
        """
        if len(scores) < 2:
            return "无数据", 0.0

        # 取最近 window 次成绩
        recent = scores[-window:] if len(scores) >= window else scores
        n = len(recent)
        x = list(range(n))

        # 最小二乘法
        x_mean = sum(x) / n
        y_mean = sum(recent) / n
        numerator = sum((x[i] - x_mean) * (recent[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return "稳定", 0.0

        slope = numerator / denominator

        # 判断趋势（斜率阈值 ±1.0）
        if slope > 1.0:
            return "上升", slope
        elif slope < -1.0:
            return "下降", slope
        else:
            return "稳定", slope

    async def get_class_comparison(
        self,
        student_id: str,
        subject: str,
        exam_name: str,
    ) -> Dict:
        """
        获取班级对比数据

        Returns:
            {
                "student_score": 82,
                "class_avg": 75,
                "class_max": 98,
                "class_min": 35,
                "rank": 8,
                "total_students": 45
            }
        """
        # 获取学生所在班级
        student_result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = student_result.scalars().first()
        if not student or not student.class_id:
            return {}

        # 获取同班同学的成绩
        query = (
            select(StudentPerformance.score)
            .join(Student, Student.id == StudentPerformance.student_id)
            .where(
                Student.class_id == student.class_id,
                StudentPerformance.subject == subject,
                StudentPerformance.exam_name == exam_name,
            )
        )
        result = await self.db.execute(query)
        class_scores = sorted([r[0] for r in result.all()], reverse=True)

        # 获取该学生的成绩
        student_perf = await self.db.execute(
            select(StudentPerformance.score).where(
                StudentPerformance.student_id == student_id,
                StudentPerformance.subject == subject,
                StudentPerformance.exam_name == exam_name,
            )
        )
        student_score_row = student_perf.first()
        student_score = student_score_row[0] if student_score_row else 0

        rank = class_scores.index(student_score) + 1 if student_score in class_scores else 0

        return {
            "student_score": student_score,
            "class_avg": round(sum(class_scores) / len(class_scores), 1) if class_scores else 0,
            "class_max": max(class_scores) if class_scores else 0,
            "class_min": min(class_scores) if class_scores else 0,
            "rank": rank,
            "total_students": len(class_scores),
        }
