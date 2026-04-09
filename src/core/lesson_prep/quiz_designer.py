"""
AI 智能备课系统 - 分层习题设计器
基于 SOLO 分类理论生成难度递进、认知层次分明的习题
"""

import json
import logging
import uuid
from typing import List, Dict, Optional

from src.services.ai_client import AIClient
from src.utils.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class QuizDesigner:
    """
    分层习题设计器

    核心功能：
    - generate_layered_quiz: 生成分层习题集
    - generate_variations: 对指定题目生成变式
    - validate_difficulty_distribution: 验证难度分布
    """

    def __init__(self, ai_client: AIClient, prompt_manager: PromptManager):
        self.ai = ai_client
        self.pm = prompt_manager

    async def generate_layered_quiz(
        self,
        subject: str,
        knowledge_point: str,
        basic_percent: int = 40,
        intermediate_percent: int = 40,
        advanced_percent: int = 20,
        question_types: Optional[List[str]] = None,
        count: int = 5,
        difficulty_range: Optional[List[float]] = None,
        student_profile: Optional[str] = None,
    ) -> Dict:
        """
        生成分层习题集

        Args:
            subject: 学科
            knowledge_point: 目标知识点
            basic_percent: 基础层占比
            intermediate_percent: 提高层占比
            advanced_percent: 拓展层占比
            question_types: 题型列表
            count: 生成题目数量
            difficulty_range: 难度系数范围 [min, max]
            student_profile: 学生水平描述

        Returns:
            {
                "questions": [...],
                "total_count": 5,
                "difficulty_distribution": {"基础": 2, "提高": 2, "拓展": 1}
            }
        """
        logger.info(f"开始生成习题 | {subject} | {knowledge_point} | {count}题")

        if question_types is None:
            question_types = ["选择题", "填空题", "计算题"]
        if difficulty_range is None:
            difficulty_range = [0.3, 0.8]

        # 获取渲染后的提示词
        prompts = self.pm.get_full_prompt(
            category="lesson_prep",
            name="adaptive_quiz_generator",
            knowledge_point=knowledge_point,
            basic_percent=basic_percent,
            intermediate_percent=intermediate_percent,
            advanced_percent=advanced_percent,
            question_types=", ".join(question_types),
            difficulty_range=f"{difficulty_range[0]}-{difficulty_range[1]}",
            count=count,
            student_profile=student_profile or "",
        )

        # 调用 AI 生成 JSON 格式习题
        messages = [
            {"role": "system", "content": prompts["system"]},
            {"role": "user", "content": prompts["user"]},
        ]

        result = await self.ai.chat_json(messages)

        # 处理返回结果
        questions = self._parse_questions(result, subject, knowledge_point)
        difficulty_dist = self._compute_difficulty_distribution(questions)

        logger.info(
            f"习题生成完成 | {knowledge_point} | "
            f"共 {len(questions)} 题 | 分布: {difficulty_dist}"
        )

        return {
            "questions": questions,
            "total_count": len(questions),
            "difficulty_distribution": difficulty_dist,
        }

    async def generate_variations(
        self,
        original_question: str,
        subject: str,
        count: int = 3,
    ) -> List[Dict]:
        """
        对指定题目生成变式题

        Args:
            original_question: 原题内容
            subject: 学科
            count: 变式数量

        Returns:
            变式题列表
        """
        system_prompt = (
            f"你是{subject}学科出题专家。请基于给定的原题，生成{count}道变式题。\n"
            "变式题应保持核心考查点不变，但改变数值、情境或问法。\n"
            "每道变式题需包含：题目内容、标准答案、与原题的区别说明。\n"
            "以 JSON 数组格式输出。"
        )
        user_prompt = f"原题：{original_question}\n\n请生成 {count} 道变式题。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        result = await self.ai.chat_json(messages)

        if isinstance(result, list):
            return result
        elif "raw_content" in result:
            return [{"content": result["raw_content"], "answer": "", "difference": ""}]
        return result.get("variations", [result])

    def _parse_questions(
        self, raw_result: Dict | List, subject: str, knowledge_point: str
    ) -> List[Dict]:
        """解析 AI 返回的习题数据"""
        questions = []

        # 处理不同的返回格式
        if isinstance(raw_result, list):
            raw_questions = raw_result
        elif isinstance(raw_result, dict):
            if "questions" in raw_result:
                raw_questions = raw_result["questions"]
            elif "raw_content" in raw_result:
                return [{
                    "id": str(uuid.uuid4()),
                    "content": raw_result["raw_content"],
                    "answer": "",
                    "cognitive_level": "理解",
                    "difficulty": 0.5,
                    "knowledge_points": [knowledge_point],
                    "common_errors": [],
                    "variations": [],
                }]
            else:
                raw_questions = [raw_result]
        else:
            raw_questions = []

        for q in raw_questions:
            if isinstance(q, dict):
                questions.append({
                    "id": q.get("id", str(uuid.uuid4())),
                    "content": q.get("content", ""),
                    "question_type": q.get("question_type", ""),
                    "answer": q.get("answer", ""),
                    "scoring_criteria": q.get("scoring_criteria", ""),
                    "cognitive_level": q.get("cognitive_level", "理解"),
                    "difficulty": float(q.get("difficulty", 0.5)),
                    "knowledge_points": q.get("knowledge_points", [knowledge_point]),
                    "common_errors": q.get("common_errors", []),
                    "variations": q.get("variations", []),
                })

        return questions

    @staticmethod
    def _compute_difficulty_distribution(questions: List[Dict]) -> Dict[str, int]:
        """计算题目难度分布"""
        dist = {"基础": 0, "提高": 0, "拓展": 0}
        for q in questions:
            diff = q.get("difficulty", 0.5)
            if diff < 0.4:
                dist["基础"] += 1
            elif diff < 0.7:
                dist["提高"] += 1
            else:
                dist["拓展"] += 1
        return dist
