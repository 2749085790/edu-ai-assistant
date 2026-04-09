"""
个性化推荐系统 - 自适应学习引擎
动态调整学习难度、推荐学习资源、更新知识掌握度
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import KnowledgeState, TeachingMaterial, Student

logger = logging.getLogger(__name__)


class AdaptiveEngine:
    """
    自适应学习引擎

    核心功能：
    - adjust_difficulty: 根据表现动态调整难度
    - recommend_resources: 基于知识状态推荐学习资源
    - update_mastery: 根据练习结果更新掌握度
    - schedule_review: 基于间隔重复安排复习
    """

    # 间隔重复时间表（天）
    SPACED_INTERVALS = [1, 3, 7, 14, 30]

    # 心流区间
    FLOW_MIN = 0.60  # 最低成功率
    FLOW_MAX = 0.85  # 最高成功率

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def adjust_difficulty(
        self,
        student_id: str,
        subject: str,
        knowledge_point: str,
        recent_accuracy: float,
    ) -> Dict:
        """
        根据最近表现动态调整难度

        心流理论：保持成功率在 60%-85% 之间
        - 成功率 > 85%: 提高难度
        - 成功率 < 60%: 降低难度
        - 60%-85%: 保持当前难度

        Args:
            student_id: 学生ID
            subject: 学科
            knowledge_point: 知识点
            recent_accuracy: 最近准确率

        Returns:
            {
                "current_accuracy": 0.72,
                "recommended_difficulty": 0.6,
                "adjustment": "maintain",
                "message": "当前难度适中，保持挑战"
            }
        """
        # 获取当前知识状态
        kn_result = await self.db.execute(
            select(KnowledgeState).where(
                KnowledgeState.student_id == student_id,
                KnowledgeState.subject == subject,
                KnowledgeState.knowledge_point == knowledge_point,
            )
        )
        kn_state = kn_result.scalars().first()

        current_mastery = kn_state.mastery_level if kn_state else 0.5

        if recent_accuracy > self.FLOW_MAX:
            new_difficulty = min(current_mastery + 0.1, 0.95)
            adjustment = "increase"
            message = f"表现优秀！准确率 {recent_accuracy:.0%}，适当提高难度以保持挑战"
        elif recent_accuracy < self.FLOW_MIN:
            new_difficulty = max(current_mastery - 0.15, 0.2)
            adjustment = "decrease"
            message = f"当前难度偏高，准确率 {recent_accuracy:.0%}，降低难度帮助建立信心"
        else:
            new_difficulty = current_mastery
            adjustment = "maintain"
            message = f"难度适中，准确率 {recent_accuracy:.0%}，保持当前节奏"

        return {
            "current_accuracy": recent_accuracy,
            "current_mastery": current_mastery,
            "recommended_difficulty": round(new_difficulty, 2),
            "adjustment": adjustment,
            "message": message,
        }

    async def recommend_resources(
        self,
        student_id: str,
        subject: str,
        limit: int = 5,
    ) -> List[Dict]:
        """
        基于知识状态推荐学习资源

        优先推荐薄弱知识点相关的高质量资源

        Returns:
            推荐资源列表，按优先级排序
        """
        # 获取薄弱知识点
        kn_query = (
            select(KnowledgeState)
            .where(
                KnowledgeState.student_id == student_id,
                KnowledgeState.subject == subject,
            )
            .order_by(KnowledgeState.mastery_level.asc())
        )
        kn_result = await self.db.execute(kn_query)
        weak_states = kn_result.scalars().all()

        # 收集薄弱知识点
        weak_kps = [
            s.knowledge_point for s in weak_states
            if s.mastery_level < 0.8
        ][:5]

        if not weak_kps:
            # 如果没有薄弱点，推荐拓展资源
            query = (
                select(TeachingMaterial)
                .where(TeachingMaterial.subject == subject)
                .order_by(TeachingMaterial.quality_score.desc())
                .limit(limit)
            )
            result = await self.db.execute(query)
            materials = result.scalars().all()
        else:
            # 搜索与薄弱知识点相关的素材
            query = (
                select(TeachingMaterial)
                .where(TeachingMaterial.subject == subject)
                .order_by(TeachingMaterial.quality_score.desc())
                .limit(limit * 3)
            )
            result = await self.db.execute(query)
            all_materials = result.scalars().all()

            # 按相关性过滤和排序
            scored_materials = []
            for m in all_materials:
                if m.knowledge_points:
                    relevance = len(set(m.knowledge_points) & set(weak_kps))
                    if relevance > 0:
                        scored_materials.append((m, relevance))

            scored_materials.sort(key=lambda x: (-x[1], -x[0].quality_score))
            materials = [m for m, _ in scored_materials[:limit]]

            if not materials:
                materials = all_materials[:limit]

        recommendations = []
        for i, m in enumerate(materials):
            # 确定推荐原因
            related_weak = []
            if m.knowledge_points and weak_kps:
                related_weak = list(set(m.knowledge_points) & set(weak_kps))

            recommendations.append({
                "rank": i + 1,
                "material_id": m.id,
                "title": m.title,
                "type": m.material_type,
                "description": m.description,
                "quality_score": m.quality_score,
                "reason": (
                    f"针对薄弱知识点：{', '.join(related_weak)}"
                    if related_weak else "高质量拓展学习资源"
                ),
            })

        return recommendations

    async def update_mastery(
        self,
        student_id: str,
        subject: str,
        knowledge_point: str,
        correct: bool,
        difficulty: float = 0.5,
    ) -> Dict:
        """
        根据单次练习结果更新知识掌握度

        使用 ELO-like 评分更新算法：
        - 答对高难度题 → 掌握度大幅提升
        - 答错低难度题 → 掌握度明显下降

        Returns:
            {"previous_mastery": 0.6, "new_mastery": 0.65, "change": +0.05}
        """
        kn_result = await self.db.execute(
            select(KnowledgeState).where(
                KnowledgeState.student_id == student_id,
                KnowledgeState.subject == subject,
                KnowledgeState.knowledge_point == knowledge_point,
            )
        )
        kn_state = kn_result.scalars().first()

        if not kn_state:
            # 新知识点
            kn_state = KnowledgeState(
                student_id=student_id,
                subject=subject,
                knowledge_point=knowledge_point,
                mastery_level=0.5,
                practice_count=0,
                correct_rate=0.0,
            )
            self.db.add(kn_state)

        previous = kn_state.mastery_level

        # ELO-like 更新
        k_factor = 0.1  # 学习速率
        expected = kn_state.mastery_level  # 预期正确率
        actual = 1.0 if correct else 0.0
        difficulty_weight = 0.5 + difficulty  # 难度加权

        change = k_factor * difficulty_weight * (actual - expected)
        new_mastery = max(0.0, min(1.0, kn_state.mastery_level + change))

        # 更新数据
        kn_state.mastery_level = round(new_mastery, 4)
        kn_state.practice_count += 1
        total_correct = kn_state.correct_rate * (kn_state.practice_count - 1) + (1 if correct else 0)
        kn_state.correct_rate = round(total_correct / kn_state.practice_count, 4)
        kn_state.last_practice_at = datetime.utcnow()

        return {
            "knowledge_point": knowledge_point,
            "previous_mastery": round(previous, 4),
            "new_mastery": round(new_mastery, 4),
            "change": round(new_mastery - previous, 4),
            "practice_count": kn_state.practice_count,
            "correct_rate": kn_state.correct_rate,
        }

    async def schedule_review(
        self,
        student_id: str,
        subject: str,
    ) -> List[Dict]:
        """
        基于间隔重复原理安排复习计划

        Leitner 系统变体：
        - 掌握度越高，间隔越长
        - 掌握度越低，间隔越短

        Returns:
            需要复习的知识点列表及推荐复习时间
        """
        query = select(KnowledgeState).where(
            KnowledgeState.student_id == student_id,
            KnowledgeState.subject == subject,
        )
        result = await self.db.execute(query)
        states = result.scalars().all()

        now = datetime.utcnow()
        review_items = []

        for state in states:
            if state.mastery_level >= 0.95:
                continue  # 完全掌握的跳过

            # 根据掌握度确定复习间隔
            if state.mastery_level < 0.4:
                interval_idx = 0  # 1天
            elif state.mastery_level < 0.6:
                interval_idx = 1  # 3天
            elif state.mastery_level < 0.8:
                interval_idx = 2  # 7天
            else:
                interval_idx = 3  # 14天

            interval_days = self.SPACED_INTERVALS[interval_idx]
            next_review = (
                state.last_practice_at + timedelta(days=interval_days)
                if state.last_practice_at
                else now
            )

            # 检查是否到了复习时间
            if next_review <= now:
                urgency = "高" if state.mastery_level < 0.5 else ("中" if state.mastery_level < 0.7 else "低")
                review_items.append({
                    "knowledge_point": state.knowledge_point,
                    "current_mastery": state.mastery_level,
                    "last_practice": state.last_practice_at.isoformat() if state.last_practice_at else None,
                    "recommended_review_date": next_review.isoformat(),
                    "interval_days": interval_days,
                    "urgency": urgency,
                })

        # 按紧急度排序
        urgency_order = {"高": 0, "中": 1, "低": 2}
        review_items.sort(key=lambda x: urgency_order.get(x["urgency"], 3))

        return review_items
