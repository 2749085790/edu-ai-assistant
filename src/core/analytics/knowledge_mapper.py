"""
学情分析引擎 - 知识图谱诊断
构建学生知识掌握图谱，检测知识断点和前置知识缺失
"""

import json
import logging
from typing import List, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import KnowledgeState, Student
from src.services.ai_client import AIClient
from src.utils.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


# 知识依赖关系图（示例：初中数学）
MATH_KNOWLEDGE_GRAPH = {
    "一元二次方程": {
        "prerequisites": ["一元一次方程", "因式分解"],
        "category": "代数",
    },
    "二次函数": {
        "prerequisites": ["一元二次方程", "平面直角坐标系", "一次函数"],
        "category": "函数",
    },
    "相似三角形": {
        "prerequisites": ["三角形基础", "比例"],
        "category": "几何",
    },
    "勾股定理": {
        "prerequisites": ["三角形基础", "平方根"],
        "category": "几何",
    },
    "概率统计": {
        "prerequisites": ["分数", "比例"],
        "category": "统计与概率",
    },
    "圆的性质": {
        "prerequisites": ["角的概念", "三角形基础", "勾股定理"],
        "category": "几何",
    },
}


class KnowledgeMapper:
    """
    知识图谱诊断器

    核心功能：
    - build_knowledge_graph: 构建学生知识掌握图谱
    - diagnose_gaps: 检测知识断点
    - detect_prerequisite_gaps: 前置知识缺失检测
    - generate_ai_diagnosis: AI 辅助知识诊断
    """

    MASTERY_THRESHOLD = 0.6  # 掌握度阈值

    def __init__(
        self,
        db_session: AsyncSession,
        ai_client: Optional[AIClient] = None,
        prompt_manager: Optional[PromptManager] = None,
    ):
        self.db = db_session
        self.ai = ai_client
        self.pm = prompt_manager

    async def build_knowledge_graph(
        self, student_id: str, subject: str
    ) -> Dict:
        """
        构建学生知识掌握图谱

        Returns:
            {
                "student_id": "...",
                "subject": "...",
                "knowledge_points": {
                    "知识点名": {
                        "mastery": 0.85,
                        "status": "已掌握",
                        "practice_count": 42,
                        "category": "代数"
                    }
                },
                "overall_mastery": 0.68,
                "category_mastery": {"代数": 0.78, "几何": 0.55}
            }
        """
        query = select(KnowledgeState).where(
            KnowledgeState.student_id == student_id,
            KnowledgeState.subject == subject,
        )
        result = await self.db.execute(query)
        states = result.scalars().all()

        knowledge_points = {}
        category_scores = {}

        for state in states:
            status = self._classify_mastery(state.mastery_level)
            category = MATH_KNOWLEDGE_GRAPH.get(
                state.knowledge_point, {}
            ).get("category", "其他")

            knowledge_points[state.knowledge_point] = {
                "mastery": state.mastery_level,
                "status": status,
                "practice_count": state.practice_count,
                "correct_rate": state.correct_rate,
                "category": category,
            }

            # 按类别聚合
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(state.mastery_level)

        # 计算整体和分类掌握度
        all_masteries = [s.mastery_level for s in states]
        overall = sum(all_masteries) / len(all_masteries) if all_masteries else 0

        category_mastery = {
            cat: round(sum(scores) / len(scores), 2)
            for cat, scores in category_scores.items()
        }

        return {
            "student_id": student_id,
            "subject": subject,
            "knowledge_points": knowledge_points,
            "overall_mastery": round(overall, 2),
            "category_mastery": category_mastery,
        }

    async def diagnose_gaps(self, student_id: str, subject: str) -> Dict:
        """
        检测知识断点

        Returns:
            {
                "mastered": [{"name": "...", "mastery": 0.9}],
                "weak_points": [{"name": "...", "mastery": 0.3}],
                "gaps": ["严重薄弱的知识点"],
                "prerequisite_gaps": [...]
            }
        """
        graph = await self.build_knowledge_graph(student_id, subject)
        kps = graph["knowledge_points"]

        mastered = []
        weak_points = []
        gaps = []

        for name, info in kps.items():
            item = {"name": name, "mastery": info["mastery"], "category": info["category"]}
            if info["mastery"] >= 0.8:
                mastered.append(item)
            elif info["mastery"] >= self.MASTERY_THRESHOLD:
                weak_points.append(item)
            else:
                gaps.append(name)
                weak_points.append(item)

        # 检测前置知识缺失
        prerequisite_gaps = self._detect_prerequisite_gaps(kps)

        return {
            "mastered": sorted(mastered, key=lambda x: x["mastery"], reverse=True),
            "weak_points": sorted(weak_points, key=lambda x: x["mastery"]),
            "gaps": gaps,
            "prerequisite_gaps": prerequisite_gaps,
        }

    def _detect_prerequisite_gaps(self, knowledge_points: Dict) -> List[Dict]:
        """
        前置知识缺失检测
        如果某个知识点未掌握，检查其前置知识是否掌握
        """
        gaps = []

        for kp_name, kp_info in knowledge_points.items():
            if kp_info["mastery"] < self.MASTERY_THRESHOLD:
                # 检查该知识点的前置知识
                prerequisites = MATH_KNOWLEDGE_GRAPH.get(kp_name, {}).get("prerequisites", [])
                missing_prereqs = []

                for prereq in prerequisites:
                    prereq_info = knowledge_points.get(prereq)
                    if prereq_info is None or prereq_info["mastery"] < self.MASTERY_THRESHOLD:
                        missing_prereqs.append(prereq)

                if missing_prereqs:
                    gaps.append({
                        "knowledge_point": kp_name,
                        "current_mastery": kp_info["mastery"],
                        "missing_prerequisites": missing_prereqs,
                        "suggestion": f"建议先补充 {'、'.join(missing_prereqs)} 的基础知识",
                    })

        return gaps

    async def generate_ai_diagnosis(
        self, student_id: str, subject: str
    ) -> str:
        """
        调用 AI 生成知识诊断报告

        Returns:
            AI 生成的诊断摘要文本
        """
        if not self.ai:
            return "AI 客户端未配置"

        # 获取知识数据
        graph = await self.build_knowledge_graph(student_id, subject)
        gaps = await self.diagnose_gaps(student_id, subject)

        # 获取学生信息
        student_result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = student_result.scalars().first()
        student_name = student.name if student else "未知"

        system_prompt = (
            "你是教育诊断专家。根据学生的知识掌握数据，生成一份简洁的诊断报告。"
            "报告应包括：优势领域、薄弱环节、知识断点分析和改进建议。"
            "语言要亲切、鼓励性，适合教师和家长阅读。"
        )

        user_prompt = (
            f"学生：{student_name}\n"
            f"学科：{subject}\n"
            f"整体掌握度：{graph['overall_mastery']}\n"
            f"分类掌握度：{json.dumps(graph['category_mastery'], ensure_ascii=False)}\n"
            f"薄弱知识点：{json.dumps([w['name'] for w in gaps['weak_points']], ensure_ascii=False)}\n"
            f"知识断点：{json.dumps(gaps['gaps'], ensure_ascii=False)}\n"
            f"前置知识缺失：{json.dumps(gaps['prerequisite_gaps'], ensure_ascii=False, default=str)}\n"
        )

        return await self.ai.generate_with_system_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    @staticmethod
    def _classify_mastery(level: float) -> str:
        """根据掌握度分类"""
        if level >= 0.8:
            return "已掌握"
        elif level >= 0.6:
            return "待巩固"
        else:
            return "薄弱"
