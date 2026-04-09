"""
个性化推荐系统 - 学习路径规划
基于知识依赖关系和掌握学习理论规划最优学习路径
"""

import json
import logging
import uuid
from typing import Dict, Optional, List
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Student, KnowledgeState, LearningPath as LearningPathModel
from src.services.ai_client import AIClient
from src.utils.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class LearningPathPlanner:
    """
    学习路径规划器

    核心功能：
    - plan_path: 基于知识依赖关系规划学习路径
    - generate_milestones: 设计阶段里程碑
    - get_active_path: 获取当前活跃的学习路径
    - update_progress: 更新学习进度
    """

    MASTERY_REQUIRED = 0.8  # 进入下阶段的掌握度要求

    def __init__(
        self,
        db_session: AsyncSession,
        ai_client: Optional[AIClient] = None,
        prompt_manager: Optional[PromptManager] = None,
    ):
        self.db = db_session
        self.ai = ai_client
        self.pm = prompt_manager

    async def plan_path(
        self,
        student_id: str,
        subject: str,
        learning_objective: str,
        time_constraint: Optional[str] = None,
        learning_style: Optional[str] = None,
    ) -> Dict:
        """
        生成个性化学习路径

        Args:
            student_id: 学生ID
            subject: 学科
            learning_objective: 学习目标
            time_constraint: 时间约束
            learning_style: 学习偏好

        Returns:
            完整学习路径数据
        """
        logger.info(f"开始规划学习路径 | student_id={student_id} | obj={learning_objective}")

        # 获取学生当前知识状态
        knowledge_state = await self._get_knowledge_state(student_id, subject)

        # 获取学生信息
        student_result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = student_result.scalars().first()
        style = learning_style or (student.learning_style if student else "视觉型")

        # 使用 AI 生成路径
        if self.ai and self.pm:
            path_data = await self._ai_generate_path(
                student_id=student_id,
                subject=subject,
                knowledge_state=knowledge_state,
                learning_objective=learning_objective,
                time_constraint=time_constraint,
                learning_style=style,
            )
        else:
            # 规则引擎生成基础路径
            path_data = self._rule_generate_path(
                knowledge_state=knowledge_state,
                learning_objective=learning_objective,
            )

        # 持久化学习路径
        path_id = str(uuid.uuid4())
        path_record = LearningPathModel(
            id=path_id,
            student_id=student_id,
            subject=subject,
            learning_objective=learning_objective,
            stages=path_data.get("milestones", []),
            current_stage=0,
            adaptive_rules=path_data.get("adaptive_rules", {}),
            estimated_duration=path_data.get("estimated_duration", ""),
            estimated_completion=datetime.utcnow() + timedelta(days=30),
            alternative_paths=path_data.get("alternative_paths", []),
            motivation_design=path_data.get("motivation_design", {}),
            progress_percent=0.0,
            is_active=True,
        )
        self.db.add(path_record)

        result = {
            "id": path_id,
            "student_id": student_id,
            "subject": subject,
            "learning_objective": learning_objective,
            "estimated_duration": path_data.get("estimated_duration", "约4周"),
            "stages": path_data.get("milestones", []),
            "current_stage": 0,
            "progress_percent": 0.0,
            "alternative_paths": path_data.get("alternative_paths", []),
            "motivation_design": path_data.get("motivation_design", {}),
        }

        logger.info(f"学习路径规划完成 | path_id={path_id}")
        return result

    async def _get_knowledge_state(
        self, student_id: str, subject: str
    ) -> Dict[str, float]:
        """获取学生知识掌握状态"""
        query = select(KnowledgeState).where(
            KnowledgeState.student_id == student_id,
            KnowledgeState.subject == subject,
        )
        result = await self.db.execute(query)
        states = result.scalars().all()
        return {s.knowledge_point: s.mastery_level for s in states}

    async def _ai_generate_path(
        self,
        student_id: str,
        subject: str,
        knowledge_state: Dict[str, float],
        learning_objective: str,
        time_constraint: Optional[str],
        learning_style: str,
    ) -> Dict:
        """使用 AI 生成学习路径"""
        # 能力评估摘要
        masteries = list(knowledge_state.values())
        avg_mastery = sum(masteries) / len(masteries) if masteries else 0
        weak_points = [k for k, v in knowledge_state.items() if v < 0.6]

        ability_assessment = (
            f"整体掌握度: {avg_mastery:.0%}\n"
            f"薄弱知识点: {', '.join(weak_points) if weak_points else '无'}"
        )

        prompts = self.pm.get_full_prompt(
            category="personalization",
            name="learning_path",
            student_id=student_id,
            subject=subject,
            knowledge_state=json.dumps(knowledge_state, ensure_ascii=False),
            ability_assessment=ability_assessment,
            learning_objective=learning_objective,
            time_constraint=time_constraint or "无限制",
            learning_style=learning_style,
        )

        messages = [
            {"role": "system", "content": prompts["system"]},
            {"role": "user", "content": prompts["user"]},
        ]

        result = await self.ai.chat_json(messages)
        return result if isinstance(result, dict) else {}

    def _rule_generate_path(
        self,
        knowledge_state: Dict[str, float],
        learning_objective: str,
    ) -> Dict:
        """基于规则的路径生成（无 AI 时的降级方案）"""
        weak_points = sorted(
            [(k, v) for k, v in knowledge_state.items() if v < self.MASTERY_REQUIRED],
            key=lambda x: x[1],
        )

        stages = []
        for i, (kp, mastery) in enumerate(weak_points, 1):
            stages.append({
                "stage": i,
                "objective": f"巩固知识点：{kp}（当前掌握度 {mastery:.0%}）",
                "content_sequence": [
                    {
                        "type": "reading",
                        "title": f"{kp} 知识梳理",
                        "estimated_time": "20分钟",
                        "mastery_threshold": 0.8,
                    },
                    {
                        "type": "practice",
                        "title": f"{kp} 专项练习",
                        "estimated_time": "30分钟",
                        "mastery_threshold": 0.8,
                    },
                ],
                "checkpoint": "完成专项测试，正确率达到 80%",
                "estimated_time": "50分钟",
            })

        return {
            "estimated_duration": f"约 {len(stages)} 天",
            "milestones": stages,
            "alternative_paths": [],
            "motivation_design": {
                "micro_rewards": ["完成每个阶段获得进度勋章"],
                "progress_visualization": "进度条 + 知识图谱解锁动画",
            },
        }

    async def get_active_path(
        self, student_id: str, subject: Optional[str] = None
    ) -> Optional[Dict]:
        """获取学生当前活跃的学习路径"""
        conditions = [
            LearningPathModel.student_id == student_id,
            LearningPathModel.is_active == True,
        ]
        if subject:
            conditions.append(LearningPathModel.subject == subject)

        query = (
            select(LearningPathModel)
            .where(*conditions)
            .order_by(LearningPathModel.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        path = result.scalars().first()

        if not path:
            return None

        return {
            "id": path.id,
            "student_id": path.student_id,
            "subject": path.subject,
            "learning_objective": path.learning_objective,
            "estimated_duration": path.estimated_duration,
            "stages": path.stages or [],
            "current_stage": path.current_stage,
            "progress_percent": path.progress_percent,
            "is_active": path.is_active,
            "created_at": path.created_at.isoformat() if path.created_at else None,
        }

    async def update_progress(
        self,
        path_id: str,
        current_stage: int,
        progress_percent: float,
        mastery_scores: Optional[Dict[str, float]] = None,
    ) -> Dict:
        """更新学习路径进度"""
        query = select(LearningPathModel).where(LearningPathModel.id == path_id)
        result = await self.db.execute(query)
        path = result.scalars().first()

        if not path:
            return {"error": "路径不存在"}

        path.current_stage = current_stage
        path.progress_percent = progress_percent

        # 如果有掌握度更新，同步更新知识状态
        if mastery_scores:
            for kp, score in mastery_scores.items():
                kn_result = await self.db.execute(
                    select(KnowledgeState).where(
                        KnowledgeState.student_id == path.student_id,
                        KnowledgeState.knowledge_point == kp,
                    )
                )
                kn_state = kn_result.scalars().first()
                if kn_state:
                    kn_state.mastery_level = max(kn_state.mastery_level, score)

        # 检查是否完成
        stages = path.stages or []
        if current_stage >= len(stages):
            path.is_active = False
            path.progress_percent = 100.0

        return {
            "id": path.id,
            "current_stage": path.current_stage,
            "progress_percent": path.progress_percent,
            "is_active": path.is_active,
        }
