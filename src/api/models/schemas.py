"""
教培 AI 智能备课与学情分析系统 - Pydantic 请求/响应数据模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class CognitiveLevel(str, Enum):
    REMEMBER = "记忆"
    UNDERSTAND = "理解"
    APPLY = "应用"
    ANALYZE = "分析"
    EVALUATE = "评价"
    CREATE = "创造"


class LessonTypeEnum(str, Enum):
    NEW = "新授课"
    REVIEW = "复习课"
    EXPERIMENT = "实验课"
    PROJECT = "项目式"


class StudentLevelEnum(str, Enum):
    WEAK = "基础薄弱"
    MEDIUM = "中等"
    EXCELLENT = "优秀"
    MIXED = "混合"


class RiskLevelEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskTypeEnum(str, Enum):
    KNOWLEDGE_GAP = "knowledge_gap"
    MOTIVATION = "motivation"
    METHODOLOGY = "methodology"
    EXTERNAL = "external"


# ==================== 学生相关 Schema ====================

class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="学生姓名")
    grade: str = Field(..., description="年级，如 '八年级'")
    class_id: Optional[str] = Field(None, description="班级ID")
    school: Optional[str] = Field(None, description="学校名称")
    learning_style: Optional[str] = Field(None, description="学习风格")


class StudentResponse(BaseModel):
    id: str
    name: str
    grade: str
    school: Optional[str] = None
    learning_style: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class StudentProfile(BaseModel):
    """完整学习画像"""
    student: StudentResponse
    knowledge_state: Dict[str, float] = Field(default_factory=dict, description="知识点掌握度")
    ability_radar: Dict[str, float] = Field(default_factory=dict, description="能力雷达图")
    learning_style: Optional[str] = None
    risk_factors: List[Dict] = Field(default_factory=list)
    recommended_path: Optional[str] = None
    overall_score: float = 0.0
    percentile: float = 0.0


# ==================== 备课相关 Schema ====================

class LessonPlanRequest(BaseModel):
    """教案生成请求"""
    subject: str = Field(..., description="学科名称")
    grade: str = Field(..., description="年级")
    topic: str = Field(..., description="课题名称")
    duration: int = Field(45, ge=20, le=120, description="课时(分钟)")
    lesson_type: LessonTypeEnum = Field(LessonTypeEnum.NEW, description="课型")
    student_level: StudentLevelEnum = Field(StudentLevelEnum.MEDIUM, description="学生基础")
    special_requirements: Optional[str] = Field(None, description="特殊要求")
    existing_materials: Optional[str] = Field(None, description="已有资源")
    teacher_id: Optional[str] = Field(None, description="教师ID")


class LessonPlanResponse(BaseModel):
    """教案响应"""
    id: str
    subject: str
    grade: str
    topic: str
    duration: int
    lesson_type: str
    objectives: Optional[Dict[str, str]] = None
    key_points: Optional[Dict] = None
    teaching_process: Optional[List[Dict]] = None
    differentiated_strategies: Optional[Dict[str, str]] = None
    board_design: Optional[str] = None
    homework_design: Optional[Dict] = None
    full_content: Optional[str] = None
    ai_confidence: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True


class QuizGenerateRequest(BaseModel):
    """习题生成请求"""
    subject: str = Field(..., description="学科")
    knowledge_point: str = Field(..., description="知识点")
    basic_percent: int = Field(40, ge=0, le=100, description="基础层占比")
    intermediate_percent: int = Field(40, ge=0, le=100, description="提高层占比")
    advanced_percent: int = Field(20, ge=0, le=100, description="拓展层占比")
    question_types: List[str] = Field(
        default=["选择题", "填空题", "计算题"],
        description="题型要求",
    )
    count: int = Field(5, ge=1, le=20, description="生成题目数量")
    difficulty_range: List[float] = Field(
        default=[0.3, 0.8],
        description="难度系数范围 [min, max]",
    )
    student_profile: Optional[str] = Field(None, description="学生水平描述")


class QuestionResponse(BaseModel):
    """单道题目响应"""
    id: str
    content: str
    answer: str
    scoring_criteria: Optional[str] = None
    cognitive_level: str
    difficulty: float
    knowledge_points: List[str] = Field(default_factory=list)
    common_errors: List[str] = Field(default_factory=list)
    variations: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class QuizResponse(BaseModel):
    """习题集响应"""
    questions: List[QuestionResponse]
    total_count: int
    difficulty_distribution: Dict[str, int]


# ==================== 学情分析相关 Schema ====================

class PerformanceRecord(BaseModel):
    """成绩记录输入"""
    student_id: str
    subject: str
    exam_name: str
    score: float = Field(..., ge=0)
    total_score: float = Field(100.0, gt=0)
    knowledge_detail: Optional[Dict[str, float]] = None
    exam_date: Optional[datetime] = None


class PerformanceTrend(BaseModel):
    """成绩趋势"""
    exam_name: str
    score: float
    total_score: float
    percentile: Optional[float] = None
    exam_date: datetime


class PerformanceAnalysis(BaseModel):
    """成绩分析结果"""
    student_id: str
    subject: str
    current_score: float
    average_score: float
    trend: str  # "上升" / "下降" / "稳定"
    trend_slope: float
    percentile: float
    history: List[PerformanceTrend]


class KnowledgeMapResponse(BaseModel):
    """知识图谱诊断结果"""
    student_id: str
    subject: str
    mastered: List[Dict[str, float]]     # 已掌握知识点
    weak_points: List[Dict[str, float]]  # 薄弱环节
    gaps: List[str]                       # 知识断点
    prerequisite_gaps: List[Dict]         # 前置知识缺失
    ai_summary: str


class LearningPortrait(BaseModel):
    """完整学习画像分析报告"""
    student_id: str
    academic_achievement: Dict          # 学业成就分析
    knowledge_diagnosis: Dict           # 知识图谱诊断
    ability_assessment: Dict            # 学习能力评估
    behavior_insights: Dict             # 学习行为洞察
    risk_warning: Dict                  # 风险预警
    personalized_suggestions: Dict      # 个性化建议


class RiskAlertResponse(BaseModel):
    """风险预警响应"""
    id: str
    student_id: str
    student_name: Optional[str] = None
    risk_level: str
    risk_type: str
    severity: float
    indicators: List[str] = Field(default_factory=list)
    threshold_breach: Optional[str] = None
    intervention_suggestions: List[Dict] = Field(default_factory=list)
    confidence_score: float = 0.0
    is_resolved: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class RiskPredictionResult(BaseModel):
    """风险预测结果（AI 输出格式）"""
    risk_level: RiskLevelEnum
    risk_factors: List[Dict] = Field(default_factory=list)
    intervention_suggestions: List[Dict] = Field(default_factory=list)
    confidence_score: float = 0.0


# ==================== 个性化推荐相关 Schema ====================

class LearningPathRequest(BaseModel):
    """学习路径生成请求"""
    student_id: str = Field(..., description="学生ID")
    subject: str = Field(..., description="学科")
    learning_objective: str = Field(..., description="学习目标")
    time_constraint: Optional[str] = Field(None, description="时间约束")
    learning_style: Optional[str] = Field(None, description="学习偏好")


class PathMilestone(BaseModel):
    """路径里程碑"""
    stage: int
    objective: str
    content_sequence: List[Dict]
    checkpoint: str
    estimated_time: Optional[str] = None


class LearningPathResponse(BaseModel):
    """学习路径响应"""
    id: str
    student_id: str
    subject: str
    learning_objective: Optional[str] = None
    estimated_duration: Optional[str] = None
    stages: List[Dict] = Field(default_factory=list)
    current_stage: int = 0
    progress_percent: float = 0.0
    alternative_paths: Optional[List[str]] = None
    motivation_design: Optional[Dict] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class PathProgressUpdate(BaseModel):
    """学习路径进度更新"""
    current_stage: int = Field(..., ge=0)
    progress_percent: float = Field(..., ge=0.0, le=100.0)
    mastery_scores: Optional[Dict[str, float]] = None


# ==================== 试卷扫描 Schema ====================

class PaperTypeEnum(str, Enum):
    """试卷类型"""
    EXAM = "考试"
    HOMEWORK = "晚自习作业"
    WEEKLY = "周测"
    MONTHLY = "月考"
    MIDTERM = "期中"
    FINAL = "期末"


class TestPaperScanUpload(BaseModel):
    """试卷上传/录入请求"""
    class_id: str
    subject: str
    paper_name: str
    paper_type: PaperTypeEnum = PaperTypeEnum.EXAM
    exam_date: Optional[str] = None
    ocr_text: Optional[str] = None  # OCR 识别后的文本（如果前端已做 OCR）
    file_path: Optional[str] = None
    file_type: Optional[str] = None  # image/pdf


class StudentAnswerSubmit(BaseModel):
    """学生答题提交"""
    scan_id: str
    student_id: str
    answers: Dict[int, dict]  # {question_idx: {student_answer, is_correct}}


class TargetedQuizGenerate(BaseModel):
    """生成针对性强化试卷"""
    source_scan_id: str
    class_id: str
    quiz_name: str
    quiz_type: PaperTypeEnum = PaperTypeEnum.EXAM
    question_count: int = 20
    difficulty_distribution: Optional[Dict[str, float]] = None  # {easy: 0.4, medium: 0.4, hard: 0.2}
    focus_knowledge_points: Optional[List[str]] = None  # 重点知识点（留空则自动分析薄弱点）


class TestPaperScanResponse(BaseModel):
    """试卷扫描记录响应"""
    id: str
    class_id: str
    subject: str
    paper_name: str
    paper_type: str
    exam_date: Optional[str]
    total_questions: int
    questions_parsed: Optional[List]
    knowledge_breakdown: Optional[Dict]
    difficulty_distribution: Optional[Dict]
    ai_analysis: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


# ==================== 通用响应 Schema ====================

class APIResponse(BaseModel):
    """统一 API 响应格式"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Dict] = None


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[Dict]
    total: int
    page: int
    page_size: int
    total_pages: int
