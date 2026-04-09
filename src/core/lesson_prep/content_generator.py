"""
AI 智能备课系统 - 教案/课件内容生成器
调用 AI 生成完整结构化教案，支持多课型、分层教学设计
"""

import json
import logging
import uuid
from typing import Optional, Dict

from src.services.ai_client import AIClient
from src.utils.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class ContentGenerator:
    """
    教案内容生成器

    核心功能：
    - generate_lesson_plan: 生成完整教案（Markdown）
    - generate_courseware_outline: 生成课件大纲
    - parse_lesson_plan: 解析 AI 输出为结构化数据
    """

    def __init__(self, ai_client: AIClient, prompt_manager: PromptManager):
        self.ai = ai_client
        self.pm = prompt_manager

    async def generate_lesson_plan(
        self,
        subject: str,
        grade: str,
        topic: str,
        duration: int = 45,
        lesson_type: str = "新授课",
        student_level: str = "中等",
        special_requirements: Optional[str] = None,
        existing_materials: Optional[str] = None,
    ) -> Dict:
        """
        生成完整教案

        Returns:
            {
                "id": "uuid",
                "full_content": "Markdown 教案全文",
                "objectives": {...},
                "key_points": {...},
                "teaching_process": [...],
                "differentiated_strategies": {...},
                "board_design": "...",
                "homework_design": {...},
                "ai_confidence": 0.85
            }
        """
        logger.info(f"开始生成教案 | {subject} {grade} {topic}")

        # 获取渲染后的提示词
        prompts = self.pm.get_full_prompt(
            category="lesson_prep",
            name="master_lesson_planner",
            subject=subject,
            grade=grade,
            topic=topic,
            duration=duration,
            lesson_type=lesson_type,
            student_level=student_level,
            special_requirements=special_requirements or "无",
            existing_materials=existing_materials or "无",
        )

        # 调用 AI 生成
        full_content = await self.ai.generate_with_system_prompt(
            system_prompt=prompts["system"],
            user_prompt=prompts["user"],
            temperature=0.7,
        )

        # 解析结构化内容
        parsed = self._parse_lesson_plan(full_content)
        parsed["id"] = str(uuid.uuid4())
        parsed["full_content"] = full_content
        parsed["ai_confidence"] = 0.85

        logger.info(f"教案生成完成 | id={parsed['id']} | topic={topic}")
        return parsed

    async def generate_courseware_outline(
        self,
        subject: str,
        grade: str,
        topic: str,
        duration: int = 45,
    ) -> str:
        """
        生成课件（PPT）大纲

        Returns:
            课件大纲 Markdown 文本
        """
        system_prompt = (
            f"你是一位{subject}学科课件设计专家。请为{grade}学生设计一份关于\u201c{topic}\u201d的课件大纲。\n"
            "课件应包含：封面页、学习目标页、知识讲解页（分知识点）、互动环节页、"
            "练习页、总结回顾页。每页注明标题、核心内容、视觉设计建议。"
        )
        user_prompt = (
            f"课题：{topic}\n课时：{duration}分钟\n"
            "请生成 PPT 课件大纲，按页码编排，每页包含标题、内容要点和设计建议。"
        )

        return await self.ai.generate_with_system_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

    def _parse_lesson_plan(self, content: str) -> Dict:
        """
        解析 Markdown 教案为结构化字典
        通过标题标识提取各个部分
        """
        result = {
            "objectives": {},
            "key_points": {},
            "teaching_process": [],
            "differentiated_strategies": {},
            "board_design": "",
            "homework_design": {},
        }

        sections = content.split("\n## ")
        for section in sections:
            section_lower = section.strip().lower()

            if "教学目标" in section:
                result["objectives"] = {
                    "knowledge_skills": self._extract_subsection(section, "知识"),
                    "process_methods": self._extract_subsection(section, "过程"),
                    "emotion_attitude": self._extract_subsection(section, "情感"),
                }
            elif "重难点" in section:
                result["key_points"] = {
                    "key_point": self._extract_subsection(section, "重点"),
                    "difficult_point": self._extract_subsection(section, "难点"),
                    "raw": section.strip(),
                }
            elif "教学过程" in section:
                result["teaching_process"] = self._parse_teaching_process(section)
            elif "差异化" in section or "分层" in section:
                result["differentiated_strategies"] = {
                    "raw": section.strip(),
                }
            elif "板书" in section:
                result["board_design"] = section.strip()
            elif "作业" in section:
                result["homework_design"] = {
                    "raw": section.strip(),
                }

        return result

    def _extract_subsection(self, text: str, keyword: str) -> str:
        """从文本中提取包含关键词的子段落"""
        lines = text.split("\n")
        capturing = False
        result_lines = []
        for line in lines:
            if keyword in line and ("###" in line or "**" in line):
                capturing = True
                continue
            elif capturing and line.strip().startswith("###"):
                break
            elif capturing and line.strip():
                result_lines.append(line.strip())
        return "\n".join(result_lines) if result_lines else ""

    def _parse_teaching_process(self, section: str) -> list:
        """解析教学过程为环节列表"""
        steps = []
        current_step = None
        lines = section.split("\n")

        for line in lines:
            if line.strip().startswith("### "):
                if current_step:
                    steps.append(current_step)
                current_step = {
                    "title": line.strip().replace("### ", ""),
                    "content": "",
                }
            elif current_step:
                current_step["content"] += line + "\n"

        if current_step:
            steps.append(current_step)

        return steps
