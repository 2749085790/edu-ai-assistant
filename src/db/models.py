"""
教培 AI 智能备课与学情分析系统 - SQLAlchemy ORM 模型
包含：学生、教师、班级、教案、习题、成绩、知识状态、学习路径、风险预警
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, JSON, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from src.db.database import Base
import enum


# ==================== 枚举类型 ====================

class CognitiveLevel(str, enum.Enum):
    REMEMBER = "记忆"
    UNDERSTAND = "理解"
    APPLY = "应用"
    ANALYZE = "分析"
    EVALUATE = "评价"
    CREATE = "创造"


class LessonType(str, enum.Enum):
    NEW = "新授课"
    REVIEW = "复习课"
    EXPERIMENT = "实验课"
    PROJECT = "项目式"


class StudentLevel(str, enum.Enum):
    WEAK = "基础薄弱"
    MEDIUM = "中等"
    EXCELLENT = "优秀"
    MIXED = "混合"


class RiskLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskType(str, enum.Enum):
    KNOWLEDGE_GAP = "knowledge_gap"
    MOTIVATION = "motivation"
    METHODOLOGY = "methodology"
    EXTERNAL = "external"


class QuestionType(str, enum.Enum):
    CHOICE = "选择题"
    FILL_BLANK = "填空题"
    SHORT_ANSWER = "简答题"
    CALCULATION = "计算题"
    PROOF = "证明题"
    COMPREHENSIVE = "综合题"


def generate_uuid() -> str:
    return str(uuid.uuid4())


# ==================== 基础信息模型 ====================

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), nullable=False)
    subject = Column(String(20), nullable=False)
    school = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    lesson_plans = relationship("LessonPlan", back_populates="teacher")
    classes = relationship("ClassGroup", back_populates="teacher")


class ClassGroup(Base):
    __tablename__ = "class_groups"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), nullable=False)
    grade = Column(String(20), nullable=False)
    teacher_id = Column(String(36), ForeignKey("teachers.id"))
    school = Column(String(100))
    student_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    teacher = relationship("Teacher", back_populates="classes")
    students = relationship("Student", back_populates="class_group")


class Student(Base):
    __tablename__ = "students"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), nullable=False)
    grade = Column(String(20), nullable=False)
    class_id = Column(String(36), ForeignKey("class_groups.id"), nullable=True)
    school = Column(String(100))
    avatar = Column(String(255))
    learning_style = Column(String(50))
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    class_group = relationship("ClassGroup", back_populates="students")
    performances = relationship("StudentPerformance", back_populates="student")
    knowledge_states = relationship("KnowledgeState", back_populates="student")
    error_records = relationship("ErrorRecord", back_populates="student")
    learning_paths = relationship("LearningPath", back_populates="student")
    risk_alerts = relationship("RiskAlert", back_populates="student")


# ==================== 备课模块模型 ====================

class LessonPlan(Base):
    __tablename__ = "lesson_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    teacher_id = Column(String(36), ForeignKey("teachers.id"))
    subject = Column(String(20), nullable=False)
    grade = Column(String(20), nullable=False)
    topic = Column(String(200), nullable=False)
    duration = Column(Integer, default=45)  # 分钟
    lesson_type = Column(SAEnum(LessonType), default=LessonType.NEW)
    student_level = Column(SAEnum(StudentLevel), default=StudentLevel.MEDIUM)

    # 教案内容（JSON 存储结构化内容）
    objectives = Column(JSON)        # 三维教学目标
    key_points = Column(JSON)        # 重难点分析
    teaching_process = Column(JSON)  # 详细教学过程
    differentiated_strategies = Column(JSON)  # 分层策略
    board_design = Column(Text)      # 板书设计要点
    homework_design = Column(JSON)   # 分层作业设计
    reflection_framework = Column(Text)  # 教学反思框架
    full_content = Column(Text)      # 完整 Markdown 教案

    # 元数据
    ai_confidence = Column(Float, default=0.0)
    special_requirements = Column(Text)
    existing_materials = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    teacher = relationship("Teacher", back_populates="lesson_plans")
    questions = relationship("Question", back_populates="lesson_plan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    lesson_plan_id = Column(String(36), ForeignKey("lesson_plans.id"), nullable=True)
    subject = Column(String(20), nullable=False)
    knowledge_points = Column(JSON)  # 关联知识点列表
    content = Column(Text, nullable=False)  # 题目内容（支持 LaTeX）
    answer = Column(Text, nullable=False)  # 标准答案
    scoring_criteria = Column(Text)  # 评分标准
    question_type = Column(SAEnum(QuestionType), default=QuestionType.CHOICE)
    cognitive_level = Column(SAEnum(CognitiveLevel), default=CognitiveLevel.UNDERSTAND)
    difficulty = Column(Float, default=0.5)  # 0-1
    common_errors = Column(JSON)     # 常见错误分析
    variations = Column(JSON)        # 变式拓展建议
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    lesson_plan = relationship("LessonPlan", back_populates="questions")


class TeachingMaterial(Base):
    __tablename__ = "teaching_materials"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    subject = Column(String(20), nullable=False)
    grade = Column(String(20))
    knowledge_points = Column(JSON)
    material_type = Column(String(50))  # video/document/image/interactive
    content_url = Column(String(500))
    description = Column(Text)
    tags = Column(JSON)
    quality_score = Column(Float, default=0.0)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== 学情分析模型 ====================

class StudentPerformance(Base):
    __tablename__ = "student_performances"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    subject = Column(String(20), nullable=False)
    exam_name = Column(String(100))
    score = Column(Float, nullable=False)
    total_score = Column(Float, default=100.0)
    percentile = Column(Float)        # 百分位排名
    class_rank = Column(Integer)
    grade_rank = Column(Integer)
    knowledge_detail = Column(JSON)   # 各知识点得分详情
    exam_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    student = relationship("Student", back_populates="performances")


class KnowledgeState(Base):
    __tablename__ = "knowledge_states"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    subject = Column(String(20), nullable=False)
    knowledge_point = Column(String(100), nullable=False)
    mastery_level = Column(Float, default=0.0)  # 0-1 掌握度
    practice_count = Column(Integer, default=0)
    correct_rate = Column(Float, default=0.0)
    last_practice_at = Column(DateTime)
    next_review_at = Column(DateTime)  # 间隔重复下次复习时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    student = relationship("Student", back_populates="knowledge_states")


class ErrorRecord(Base):
    __tablename__ = "error_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    subject = Column(String(20), nullable=False)
    question_content = Column(Text, nullable=False)
    student_answer = Column(Text)
    correct_answer = Column(Text)
    error_type = Column(String(50))  # 概念不清/计算失误/审题错误/时间不足
    ai_analysis = Column(Text)       # AI 错因解析
    knowledge_points = Column(JSON)
    difficulty = Column(Float)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    student = relationship("Student", back_populates="error_records")


# ==================== 个性化推荐模型 ====================

class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    subject = Column(String(20), nullable=False)
    learning_objective = Column(Text)
    stages = Column(JSON)             # 阶段列表
    current_stage = Column(Integer, default=0)
    adaptive_rules = Column(JSON)     # 自适应规则
    estimated_duration = Column(String(50))  # 预估总时长
    estimated_completion = Column(DateTime)
    alternative_paths = Column(JSON)  # 备用路径
    motivation_design = Column(JSON)  # 激励设计
    progress_percent = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    student = relationship("Student", back_populates="learning_paths")


class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)
    risk_level = Column(SAEnum(RiskLevel), nullable=False)
    risk_type = Column(SAEnum(RiskType), nullable=False)
    severity = Column(Float, default=0.0)  # 严重程度 0-1
    indicators = Column(JSON)         # 具体表现
    threshold_breach = Column(Text)   # 触发条件
    intervention_suggestions = Column(JSON)  # 干预建议
    confidence_score = Column(Float, default=0.0)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    student = relationship("Student", back_populates="risk_alerts")


# ==================== 试卷扫描模型 ====================

class TestPaperScan(Base):
    """试卷扫描记录（拍照上传/文件上传）"""
    __tablename__ = "test_paper_scans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    class_id = Column(String(36), ForeignKey("class_groups.id"), nullable=False)
    subject = Column(String(20), nullable=False)
    paper_name = Column(String(200), nullable=False)  # 试卷名称
    paper_type = Column(String(50), default="考试")  # 类型：考试/晚自习作业/周测/月考/期中/期末
    exam_date = Column(DateTime, nullable=True)

    # 原始文件
    file_path = Column(String(500))  # 上传文件路径
    file_type = Column(String(20))  # image/pdf
    ocr_raw_text = Column(Text)  # OCR 原始文本

    # AI 识别结果（题目列表）
    questions_parsed = Column(JSON)  # AI识别的题目列表 [{content, answer, knowledge_point, difficulty, ...}]
    total_questions = Column(Integer, default=0)  # 题目总数

    # 统计结果
    knowledge_breakdown = Column(JSON)  # 各知识点统计 {kp: {count, avg_difficulty, error_count}}
    difficulty_distribution = Column(JSON)  # 难度分布 {easy: n, medium: n, hard: n}
    ai_analysis = Column(Text)  # AI 分析摘要

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    class_group = relationship("ClassGroup")


class StudentAnswerRecord(Base):
    """学生答题记录（关联试卷扫描）"""
    __tablename__ = "student_answer_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    scan_id = Column(String(36), ForeignKey("test_paper_scans.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False)

    # 答题结果
    answers = Column(JSON)  # {question_idx: {student_answer, is_correct, score}}
    total_score = Column(Float)
    correct_count = Column(Integer)
    error_count = Column(Integer)

    # 错题知识点
    error_knowledge_points = Column(JSON)  # 错误题目对应的知识点列表

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    scan = relationship("TestPaperScan")
    student = relationship("Student")


class TargetedQuiz(Base):
    """针对性强化试卷（基于扫描统计生成）"""
    __tablename__ = "targeted_quizzes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_scan_id = Column(String(36), ForeignKey("test_paper_scans.id"), nullable=False)
    class_id = Column(String(36), ForeignKey("class_groups.id"), nullable=False)
    quiz_name = Column(String(200), nullable=False)
    quiz_type = Column(String(50), default="强化练习")

    # 生成参数
    focus_knowledge_points = Column(JSON)  # 重点知识点
    difficulty_distribution = Column(JSON)  # 难度分布
    question_count = Column(Integer, default=20)

    # 生成结果
    questions = Column(JSON)  # 生成的题目列表
    full_content = Column(Text)  # 完整试卷内容（Markdown）

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    source_scan = relationship("TestPaperScan")
    class_group = relationship("ClassGroup")
