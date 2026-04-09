"""
API 路由 - 试卷扫描（拍照上传 → OCR识别 → 题目分析 → 强化试卷生成）
"""

import uuid
import json
import logging
import base64
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_ai_client, get_prompt_manager
from src.api.models.schemas import (
    TestPaperScanUpload,
    StudentAnswerSubmit,
    TargetedQuizGenerate,
    TestPaperScanResponse,
    APIResponse,
)
from src.db.models import (
    TestPaperScan, StudentAnswerRecord, TargetedQuiz,
    ClassGroup, Student,
)
from src.services.ai_client import AIClient
from src.utils.prompt_manager import PromptManager

logger = logging.getLogger(__name__)

router = APIRouter()

# 上传目录
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", summary="上传试卷图片/PDF")
async def upload_paper_file(
    file: UploadFile = File(...),
):
    """
    上传试卷文件（图片/PDF）
    返回文件路径供后续 OCR 识别使用
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名为空")

    # 保存文件
    ext = Path(file.filename).suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png", ".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/PDF 格式")

    file_id = str(uuid.uuid4())[:8]
    save_path = UPLOAD_DIR / f"{file_id}{ext}"

    content = await file.read()
    save_path.write_bytes(content)

    return APIResponse(
        success=True,
        message="文件上传成功",
        data={
            "file_id": file_id,
            "file_path": str(save_path),
            "file_type": "image" if ext in (".jpg", ".jpeg", ".png") else "pdf",
        },
    )


@router.post("/scans", summary="录入试卷并 AI 识别题目")
async def create_paper_scan(
    data: TestPaperScanUpload,
    db: AsyncSession = Depends(get_db),
    ai_client: AIClient = Depends(get_ai_client),
):
    """
    录入试卷数据 + AI 自动识别题目、分析知识点和难度
    流程：
    1. 接收 OCR 文本（或从上传文件读取）
    2. 调用 AI 识别题目列表、知识点、难度
    3. 统计知识点分布和难度分布
    """
    # 验证班级
    class_result = await db.execute(
        select(ClassGroup).where(ClassGroup.id == data.class_id)
    )
    class_group = class_result.scalars().first()
    if not class_group:
        raise HTTPException(status_code=404, detail="班级不存在")

    ocr_text = data.ocr_text or ""
    if not ocr_text:
        raise HTTPException(status_code=400, detail="请提供 OCR 识别文本或上传试卷文件")

    # AI 识别题目
    questions_parsed = await _ai_parse_questions(ai_client, ocr_text, data.subject)

    # 统计分析
    knowledge_breakdown = _analyze_knowledge_distribution(questions_parsed)
    difficulty_distribution = _analyze_difficulty_distribution(questions_parsed)

    # AI 分析摘要
    ai_summary = await _ai_analyze_paper(
        ai_client, data.paper_name, data.paper_type,
        questions_parsed, knowledge_breakdown, difficulty_distribution
    )

    scan = TestPaperScan(
        id=str(uuid.uuid4()),
        class_id=data.class_id,
        subject=data.subject,
        paper_name=data.paper_name,
        paper_type=data.paper_type.value if hasattr(data.paper_type, 'value') else data.paper_type,
        exam_date=datetime.fromisoformat(data.exam_date) if data.exam_date else None,
        file_path=data.file_path,
        file_type=data.file_type,
        ocr_raw_text=ocr_text[:5000] if ocr_text else None,  # 只保存前 5000 字符
        questions_parsed=questions_parsed,
        total_questions=len(questions_parsed),
        knowledge_breakdown=knowledge_breakdown,
        difficulty_distribution=difficulty_distribution,
        ai_analysis=ai_summary,
    )
    db.add(scan)
    await db.flush()

    return APIResponse(
        success=True,
        message="试卷录入成功，AI 已识别题目并分析知识点",
        data={
            "id": scan.id,
            "paper_name": scan.paper_name,
            "total_questions": scan.total_questions,
            "knowledge_breakdown": knowledge_breakdown,
            "difficulty_distribution": difficulty_distribution,
        },
    )


@router.get("/scans", summary="获取试卷扫描列表")
async def list_paper_scans(
    class_id: Optional[str] = None,
    subject: Optional[str] = None,
    paper_type: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """获取试卷扫描记录列表"""
    conditions = []
    if class_id:
        conditions.append(TestPaperScan.class_id == class_id)
    if subject:
        conditions.append(TestPaperScan.subject == subject)
    if paper_type:
        conditions.append(TestPaperScan.paper_type == paper_type)

    query = select(TestPaperScan)
    if conditions:
        query = query.where(*conditions)
    query = query.order_by(TestPaperScan.created_at.desc()).limit(limit)

    result = await db.execute(query)
    scans = result.scalars().all()

    items = []
    for s in scans:
        items.append({
            "id": s.id,
            "class_id": s.class_id,
            "subject": s.subject,
            "paper_name": s.paper_name,
            "paper_type": s.paper_type,
            "exam_date": s.exam_date.isoformat() if s.exam_date else None,
            "total_questions": s.total_questions,
            "knowledge_breakdown": s.knowledge_breakdown,
            "difficulty_distribution": s.difficulty_distribution,
            "ai_analysis": s.ai_analysis,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return {"items": items, "total": len(items)}


@router.get("/scans/{scan_id}", summary="获取试卷详情（含题目列表）")
async def get_paper_scan_detail(
    scan_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取试卷详情，包含识别出的题目列表"""
    result = await db.execute(
        select(TestPaperScan).where(TestPaperScan.id == scan_id)
    )
    scan = result.scalars().first()
    if not scan:
        raise HTTPException(status_code=404, detail="试卷记录不存在")

    return {
        "id": scan.id,
        "paper_name": scan.paper_name,
        "paper_type": scan.paper_type,
        "subject": scan.subject,
        "total_questions": scan.total_questions,
        "questions": scan.questions_parsed or [],
        "knowledge_breakdown": scan.knowledge_breakdown,
        "difficulty_distribution": scan.difficulty_distribution,
        "ai_analysis": scan.ai_analysis,
    }


@router.post("/students/submit-answers", summary="学生提交答题结果")
async def submit_student_answers(
    data: StudentAnswerSubmit,
    db: AsyncSession = Depends(get_db),
):
    """
    学生提交答题结果（可用于统计错题）
    answers 格式: {question_idx: {student_answer, is_correct}}
    """
    record = StudentAnswerRecord(
        id=str(uuid.uuid4()),
        scan_id=data.scan_id,
        student_id=data.student_id,
        answers=data.answers,
        correct_count=sum(1 for v in data.answers.values() if v.get("is_correct")),
        error_count=sum(1 for v in data.answers.values() if not v.get("is_correct")),
    )
    record.total_score = record.correct_count  # 简化计分

    # 收集错题知识点
    scan_result = await db.execute(
        select(TestPaperScan).where(TestPaperScan.id == data.scan_id)
    )
    scan = scan_result.scalars().first()
    if scan and scan.questions_parsed:
        error_kps = []
        for idx, ans in data.answers.items():
            if not ans.get("is_correct") and idx < len(scan.questions_parsed):
                q = scan.questions_parsed[idx]
                if q.get("knowledge_point"):
                    error_kps.append(q["knowledge_point"])
        record.error_knowledge_points = list(set(error_kps))

    db.add(record)
    await db.flush()

    return APIResponse(
        success=True,
        message="答题结果已提交",
        data={
            "correct": record.correct_count,
            "wrong": record.error_count,
        },
    )


@router.post("/generate-targeted-quiz", summary="基于扫描统计生成针对性强化试卷")
async def generate_targeted_quiz(
    data: TargetedQuizGenerate,
    db: AsyncSession = Depends(get_db),
    ai_client: AIClient = Depends(get_ai_client),
):
    """
    基于试卷扫描结果，AI 生成针对性强化试卷
    重点针对：
    1. 全班错误率高的知识点
    2. 学生个人错题对应的知识点
    3. 用户指定的薄弱知识点
    """
    # 获取原试卷
    result = await db.execute(
        select(TestPaperScan).where(TestPaperScan.id == data.source_scan_id)
    )
    original_scan = result.scalars().first()
    if not original_scan:
        raise HTTPException(status_code=404, detail="原试卷记录不存在")

    # 分析薄弱知识点
    weak_points = _identify_weak_points(
        original_scan.knowledge_breakdown or {},
        data.focus_knowledge_points,
    )

    # 收集学生错题知识点（如果有学生答题记录）
    answer_result = await db.execute(
        select(StudentAnswerRecord).where(StudentAnswerRecord.scan_id == data.source_scan_id)
    )
    answer_records = answer_result.scalars().all()
    student_error_kps = []
    for rec in answer_records:
        if rec.error_knowledge_points:
            student_error_kps.extend(rec.error_knowledge_points)
    student_error_kps = list(set(student_error_kps))

    # 合并薄弱点
    all_focus_kps = list(set(
        [wp["knowledge_point"] for wp in weak_points] +
        student_error_kps +
        (data.focus_knowledge_points or [])
    ))

    # AI 生成针对性试卷
    quiz_content, questions_list = await _ai_generate_targeted_quiz(
        ai_client,
        subject=original_scan.subject,
        quiz_name=data.quiz_name,
        quiz_type=data.quiz_type,
        question_count=data.question_count,
        focus_knowledge_points=all_focus_kps,
        difficulty_distribution=data.difficulty_distribution,
        original_paper_name=original_scan.paper_name,
        weak_points=weak_points,
    )

    # 保存生成的试卷
    quiz = TargetedQuiz(
        id=str(uuid.uuid4()),
        source_scan_id=data.source_scan_id,
        class_id=data.class_id,
        quiz_name=data.quiz_name,
        quiz_type=data.quiz_type.value if hasattr(data.quiz_type, 'value') else data.quiz_type,
        focus_knowledge_points=all_focus_kps,
        difficulty_distribution=data.difficulty_distribution,
        question_count=data.question_count,
        questions=questions_list,
        full_content=quiz_content,
    )
    db.add(quiz)
    await db.flush()

    return APIResponse(
        success=True,
        message="针对性强化试卷生成成功",
        data={
            "quiz_id": quiz.id,
            "quiz_name": quiz.quiz_name,
            "focus_knowledge_points": all_focus_kps,
            "weak_points": weak_points,
            "student_error_points": student_error_kps,
            "full_content": quiz_content,
        },
    )


@router.get("/quizzes", summary="获取生成的强化试卷列表")
async def list_targeted_quizzes(
    class_id: Optional[str] = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """获取已生成的针对性强化试卷列表"""
    query = select(TargetedQuiz)
    if class_id:
        query = query.where(TargetedQuiz.class_id == class_id)
    query = query.order_by(TargetedQuiz.created_at.desc()).limit(limit)

    result = await db.execute(query)
    quizzes = result.scalars().all()

    items = []
    for q in quizzes:
        items.append({
            "id": q.id,
            "quiz_name": q.quiz_name,
            "quiz_type": q.quiz_type,
            "source_paper": q.source_scan.paper_name if q.source_scan else "未知",
            "question_count": q.question_count,
            "focus_knowledge_points": q.focus_knowledge_points,
            "created_at": q.created_at.isoformat() if q.created_at else None,
        })

    return {"items": items, "total": len(items)}


# ── AI 辅助函数 ──────────────────────────────────────

async def _ai_parse_questions(
    ai_client: AIClient,
    ocr_text: str,
    subject: str,
) -> List[Dict]:
    """AI 识别 OCR 文本中的题目，提取知识点和难度"""
    system_prompt = (
        f"你是{subject}学科试题分析专家。请从 OCR 识别文本中提取所有题目，"
        f"并为每道题标注知识点和难度。\n\n"
        f"输出格式为 JSON 数组，每个元素包含：\n"
        f"- content: 题目内容\n"
        f"- answer: 答案（如果有）\n"
        f"- knowledge_point: 知识点名称\n"
        f"- difficulty: 难度系数（0-1，0.3=简单, 0.6=中等, 0.8=困难）\n"
        f"- question_type: 题型（选择题/填空题/解答题等）\n\n"
        f"只输出 JSON，不要其他文字。"
    )

    user_prompt = f"OCR 文本：\n{ocr_text[:3000]}"  # 限制长度

    result = await ai_client.chat_json([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ])

    if isinstance(result, list):
        return result
    elif isinstance(result, dict) and "questions" in result:
        return result["questions"]
    return []


def _analyze_knowledge_distribution(questions: List[Dict]) -> Dict:
    """分析知识点分布"""
    kp_stats = {}
    for q in questions:
        kp = q.get("knowledge_point", "未分类")
        if kp not in kp_stats:
            kp_stats[kp] = {"count": 0, "total_difficulty": 0}
        kp_stats[kp]["count"] += 1
        kp_stats[kp]["total_difficulty"] += q.get("difficulty", 0.5)

    for kp in kp_stats:
        count = kp_stats[kp]["count"]
        kp_stats[kp]["avg_difficulty"] = kp_stats[kp]["total_difficulty"] / count
        del kp_stats[kp]["total_difficulty"]

    return kp_stats


def _analyze_difficulty_distribution(questions: List[Dict]) -> Dict:
    """分析难度分布"""
    dist = {"简单 (0-0.4)": 0, "中等 (0.4-0.7)": 0, "困难 (0.7-1.0)": 0}
    for q in questions:
        d = q.get("difficulty", 0.5)
        if d < 0.4:
            dist["简单 (0-0.4)"] += 1
        elif d < 0.7:
            dist["中等 (0.4-0.7)"] += 1
        else:
            dist["困难 (0.7-1.0)"] += 1
    return dist


async def _ai_analyze_paper(
    ai_client: AIClient,
    paper_name: str,
    paper_type: str,
    questions: List[Dict],
    knowledge_breakdown: Dict,
    difficulty_distribution: Dict,
) -> str:
    """AI 生成试卷分析摘要"""
    kp_summary = "\n".join([
        f"- {kp}: {info['count']} 题, 平均难度 {info['avg_difficulty']:.2f}"
        for kp, info in list(knowledge_breakdown.items())[:8]
    ])

    user_prompt = (
        f"试卷：{paper_name}（{paper_type}）\n"
        f"题目总数：{len(questions)}\n"
        f"知识点分布：\n{kp_summary}\n"
        f"难度分布：{json.dumps(difficulty_distribution, ensure_ascii=False)}\n\n"
        f"请生成简要分析：整体难度评价、知识点覆盖情况、命题特点。"
    )

    return await ai_client.generate_with_system_prompt(
        system_prompt="你是试卷分析专家。请根据试卷的题目分布数据，生成专业简明的分析报告。",
        user_prompt=user_prompt,
    )


def _identify_weak_points(
    knowledge_breakdown: Dict,
    user_focus_points: Optional[List[str]] = None,
) -> List[Dict]:
    """识别薄弱知识点（高错误率/高难度/用户指定）"""
    weak_points = []

    for kp, info in knowledge_breakdown.items():
        avg_diff = info.get("avg_difficulty", 0.5)
        count = info.get("count", 0)

        # 难度高或题目多的知识点视为薄弱
        if avg_diff > 0.6 or count > 3:
            weak_points.append({
                "knowledge_point": kp,
                "question_count": count,
                "avg_difficulty": round(avg_diff, 2),
                "reason": "难度偏高" if avg_diff > 0.6 else "题目较多需强化",
            })

    # 用户指定的知识点优先
    if user_focus_points:
        for kp in user_focus_points:
            if not any(wp["knowledge_point"] == kp for wp in weak_points):
                weak_points.insert(0, {
                    "knowledge_point": kp,
                    "question_count": 0,
                    "avg_difficulty": 0,
                    "reason": "用户指定重点",
                })

    return weak_points


async def _ai_generate_targeted_quiz(
    ai_client: AIClient,
    subject: str,
    quiz_name: str,
    quiz_type,
    question_count: int,
    focus_knowledge_points: List[str],
    difficulty_distribution: Optional[Dict],
    original_paper_name: str,
    weak_points: List[Dict],
) -> tuple:
    """AI 生成针对性强化试卷"""
    diff_dist = difficulty_distribution or {"简单": 0.3, "中等": 0.5, "困难": 0.2}

    system_prompt = (
        f"你是{subject}命题专家。请根据以下薄弱知识点分析，"
        f"生成一份针对性强化试卷。\n\n"
        f"要求：\n"
        f"1. 重点覆盖指定的薄弱知识点\n"
        f"2. 难度分布：{json.dumps(diff_dist, ensure_ascii=False)}\n"
        f"3. 每道题标注知识点和难度\n"
        f"4. 题目类型多样化（选择/填空/解答）\n\n"
        f"输出格式：先输出完整试卷（Markdown 格式），然后在最后输出 JSON 格式的题目列表。"
    )

    kp_list = "\n".join([f"- {wp['knowledge_point']}（{wp['reason']}）" for wp in weak_points])

    user_prompt = (
        f"原试卷：{original_paper_name}\n"
        f"强化试卷名称：{quiz_name}\n"
        f"题目数量：{question_count} 道\n"
        f"重点知识点：\n{kp_list}\n\n"
        f"请生成针对性强化试卷。"
    )

    full_content = await ai_client.generate_with_system_prompt(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    # 尝试从输出中提取 JSON 题目列表
    questions_list = []
    # 这里简化处理，实际可以从 AI 输出中解析
    # 为演示，返回空列表，前端展示 full_content 即可

    return full_content, questions_list
