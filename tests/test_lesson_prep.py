"""
测试 - AI 智能备课模块
测试 ContentGenerator、QuizDesigner 的核心逻辑
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.core.lesson_prep.content_generator import ContentGenerator
from src.core.lesson_prep.quiz_designer import QuizDesigner


class TestContentGenerator:
    """教案内容生成器测试"""

    def setup_method(self):
        self.mock_ai = AsyncMock()
        self.mock_pm = MagicMock()
        self.generator = ContentGenerator(self.mock_ai, self.mock_pm)

    def test_parse_lesson_plan_extracts_sections(self):
        """测试教案解析能正确提取各个部分"""
        content = """
# 一元二次方程教案

## 一、教学目标
### 知识与技能
- 掌握一元二次方程的求根公式法
### 过程与方法
- 通过推导过程培养逻辑思维
### 情感态度与价值观
- 感受数学的严谨之美

## 二、教学重难点
### 重点
- 求根公式的推导与应用
### 难点
- 判别式的理解

## 三、教学过程
### 1. 导入环节（5分钟）
- 复习配方法
### 2. 新课讲授（20分钟）
- 推导求根公式

## 四、差异化教学策略
| 层次 | 策略 |
|------|------|
| 基础 | 重点练习公式代入 |

## 五、板书设计
- 左侧：公式推导过程
- 右侧：例题

## 六、分层作业设计
### 基础层
- 直接代入公式求解
### 提高层
- 含参方程
"""
        result = self.generator._parse_lesson_plan(content)

        assert "objectives" in result
        assert "key_points" in result
        assert "teaching_process" in result
        assert len(result["teaching_process"]) >= 2

    def test_extract_subsection(self):
        """测试子段落提取"""
        text = """
### 知识与技能
- 掌握基本概念
- 能够运用公式
### 过程与方法
- 通过探索发现规律
"""
        result = self.generator._extract_subsection(text, "知识")
        assert "掌握基本概念" in result

    def test_parse_teaching_process(self):
        """测试教学过程解析"""
        section = """
### 1. 导入环节（5分钟）
复习上节课内容
### 2. 新课讲授（20分钟）
讲解新知识
### 3. 巩固练习（15分钟）
学生做练习
"""
        steps = self.generator._parse_teaching_process(section)
        assert len(steps) == 3
        assert "导入" in steps[0]["title"]

    @pytest.mark.asyncio
    async def test_generate_lesson_plan_calls_ai(self):
        """测试教案生成调用 AI"""
        self.mock_pm.get_full_prompt.return_value = {
            "system": "你是教研专家",
            "user": "请生成教案",
        }
        self.mock_ai.generate_with_system_prompt.return_value = (
            "# 教案\n\n## 一、教学目标\n### 知识与技能\n- 目标1"
        )

        result = await self.generator.generate_lesson_plan(
            subject="数学",
            grade="八年级",
            topic="一元二次方程",
        )

        assert "id" in result
        assert "full_content" in result
        assert result["ai_confidence"] == 0.85
        self.mock_ai.generate_with_system_prompt.assert_called_once()


class TestQuizDesigner:
    """习题设计器测试"""

    def setup_method(self):
        self.mock_ai = AsyncMock()
        self.mock_pm = MagicMock()
        self.designer = QuizDesigner(self.mock_ai, self.mock_pm)

    def test_compute_difficulty_distribution(self):
        """测试难度分布计算"""
        questions = [
            {"difficulty": 0.2},
            {"difficulty": 0.3},
            {"difficulty": 0.5},
            {"difficulty": 0.6},
            {"difficulty": 0.8},
        ]
        dist = self.designer._compute_difficulty_distribution(questions)
        assert dist["基础"] == 2
        assert dist["提高"] == 2
        assert dist["拓展"] == 1

    def test_parse_questions_from_list(self):
        """测试从列表解析习题"""
        raw = [
            {
                "id": "Q1",
                "content": "求解 x² - 5x + 6 = 0",
                "answer": "x=2 或 x=3",
                "cognitive_level": "应用",
                "difficulty": 0.4,
            },
            {
                "id": "Q2",
                "content": "判断方程 x² + 1 = 0 是否有实数根",
                "answer": "无实数根",
                "cognitive_level": "分析",
                "difficulty": 0.6,
            },
        ]
        result = self.designer._parse_questions(raw, "数学", "一元二次方程")
        assert len(result) == 2
        assert result[0]["difficulty"] == 0.4
        assert result[1]["cognitive_level"] == "分析"

    def test_parse_questions_from_dict_with_questions_key(self):
        """测试从字典格式解析"""
        raw = {
            "questions": [
                {"content": "题目1", "answer": "答案1", "difficulty": 0.3}
            ]
        }
        result = self.designer._parse_questions(raw, "数学", "测试")
        assert len(result) == 1

    def test_parse_questions_fallback(self):
        """测试解析降级处理"""
        raw = {"raw_content": "AI 返回的非结构化文本"}
        result = self.designer._parse_questions(raw, "数学", "测试")
        assert len(result) == 1
        assert "AI 返回的非结构化文本" in result[0]["content"]
