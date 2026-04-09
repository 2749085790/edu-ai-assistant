"""
教培 AI 智能备课与学情分析系统 - 种子数据
为数据库填充初始示例数据：教师、学生、班级、成绩、知识状态等
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select

from src.db.database import async_session_factory, init_db
from src.db.models import (
    Teacher, ClassGroup, Student, StudentPerformance,
    KnowledgeState, ErrorRecord, TeachingMaterial,
)


def uid() -> str:
    return str(uuid.uuid4())


async def seed_database():
    """填充种子数据"""
    await init_db()

    async with async_session_factory() as session:
        # 检查是否已有数据
        result = await session.execute(select(Teacher).limit(1))
        if result.scalars().first():
            print("数据库已有数据，跳过种子填充")
            return

        # ---------- 教师 ----------
        teacher1_id = uid()
        teacher2_id = uid()
        teachers = [
            Teacher(id=teacher1_id, name="王老师", subject="数学", school="实验中学", email="wang@example.com"),
            Teacher(id=teacher2_id, name="李老师", subject="物理", school="实验中学", email="li@example.com"),
        ]
        session.add_all(teachers)

        # ---------- 班级 ----------
        class1_id = uid()
        class2_id = uid()
        classes = [
            ClassGroup(id=class1_id, name="八年级一班", grade="八年级", teacher_id=teacher1_id, school="实验中学", student_count=45),
            ClassGroup(id=class2_id, name="八年级二班", grade="八年级", teacher_id=teacher2_id, school="实验中学", student_count=42),
        ]
        session.add_all(classes)

        # ---------- 学生 ----------
        students_data = [
            {"name": "张小明", "grade": "八年级", "class_id": class1_id, "school": "实验中学", "learning_style": "视觉型"},
            {"name": "李小红", "grade": "八年级", "class_id": class1_id, "school": "实验中学", "learning_style": "听觉型"},
            {"name": "王小刚", "grade": "八年级", "class_id": class1_id, "school": "实验中学", "learning_style": "动觉型"},
            {"name": "赵小芳", "grade": "八年级", "class_id": class2_id, "school": "实验中学", "learning_style": "读写型"},
            {"name": "陈小磊", "grade": "八年级", "class_id": class2_id, "school": "实验中学", "learning_style": "视觉型"},
        ]
        student_ids = []
        student_name_to_id = {}
        for s in students_data:
            sid = uid()
            student_ids.append(sid)
            student_name_to_id[s["name"]] = sid
            session.add(Student(id=sid, **s))

        # ---------- 成绩记录 ----------
        now = datetime.utcnow()
        exam_names = ["月考一", "期中考试", "月考二", "月考三", "期末考试"]
        base_scores = {
            0: [72, 68, 75, 78, 82],   # 张小明 - 进步型
            1: [85, 88, 86, 90, 92],   # 李小红 - 优秀稳定
            2: [55, 52, 48, 50, 45],   # 王小刚 - 退步型（高风险）
            3: [65, 70, 72, 68, 74],   # 赵小芳 - 波动型
            4: [78, 75, 80, 82, 85],   # 陈小磊 - 稳步进步
        }
        for idx, sid in enumerate(student_ids):
            for i, (exam, score) in enumerate(zip(exam_names, base_scores[idx])):
                session.add(StudentPerformance(
                    id=uid(),
                    student_id=sid,
                    subject="数学",
                    exam_name=exam,
                    score=score,
                    total_score=100,
                    percentile=score,
                    exam_date=now - timedelta(days=(5 - i) * 30),
                ))

        # ---------- 知识状态 ----------
        knowledge_points = [
            ("一元二次方程", [0.85, 0.92, 0.35, 0.68, 0.80]),
            ("二次函数", [0.72, 0.88, 0.28, 0.60, 0.75]),
            ("相似三角形", [0.60, 0.80, 0.42, 0.55, 0.70]),
            ("勾股定理", [0.90, 0.95, 0.50, 0.78, 0.88]),
            ("概率统计", [0.55, 0.75, 0.30, 0.45, 0.65]),
            ("圆的性质", [0.48, 0.70, 0.25, 0.40, 0.58]),
        ]
        for kp_name, masteries in knowledge_points:
            for idx, sid in enumerate(student_ids):
                session.add(KnowledgeState(
                    id=uid(),
                    student_id=sid,
                    subject="数学",
                    knowledge_point=kp_name,
                    mastery_level=masteries[idx],
                    practice_count=int(masteries[idx] * 50),
                    correct_rate=masteries[idx],
                    last_practice_at=now - timedelta(days=idx + 1),
                ))

        # ---------- 错题记录 ----------
        error_records = [
            {
                "student_id": student_ids[0],
                "subject": "数学",
                "question_content": "解方程：x² - 5x + 6 = 0",
                "student_answer": "x = 2",
                "correct_answer": "x = 2 或 x = 3",
                "error_type": "概念不清",
                "ai_analysis": "学生只找到了一个根，忽略了一元二次方程有两个根的情况。需加强因式分解法求解的完整性训练。",
                "knowledge_points": ["一元二次方程", "因式分解"],
                "difficulty": 0.4,
            },
            {
                "student_id": student_ids[2],
                "subject": "数学",
                "question_content": "已知二次函数 y = x² - 4x + 3，求顶点坐标",
                "student_answer": "(4, 3)",
                "correct_answer": "(2, -1)",
                "error_type": "计算失误",
                "ai_analysis": "学生没有正确使用配方法，将 x² - 4x + 3 错误地认为顶点的 x 坐标为 4。需要复习配方法和顶点公式 x = -b/(2a)。",
                "knowledge_points": ["二次函数", "配方法"],
                "difficulty": 0.5,
            },
            {
                "student_id": student_ids[2],
                "subject": "数学",
                "question_content": "在 △ABC 中，已知 AB=6, BC=8, AC=10，判断 △ABC 的形状",
                "student_answer": "等腰三角形",
                "correct_answer": "直角三角形（∠B = 90°）",
                "error_type": "概念不清",
                "ai_analysis": "学生没有验证勾股定理。6² + 8² = 36 + 64 = 100 = 10²，满足勾股定理，所以是直角三角形。需要强化勾股定理逆定理的应用。",
                "knowledge_points": ["勾股定理", "三角形分类"],
                "difficulty": 0.3,
            },
        ]
        for rec in error_records:
            session.add(ErrorRecord(id=uid(), **rec))

        # ---------- 教学素材 ----------
        materials = [
            TeachingMaterial(
                id=uid(), title="一元二次方程微课", subject="数学", grade="八年级",
                knowledge_points=["一元二次方程"], material_type="video",
                content_url="/resources/video/quadratic_eq.mp4",
                description="10分钟讲解一元二次方程的三种解法", quality_score=4.5,
            ),
            TeachingMaterial(
                id=uid(), title="二次函数图像互动课件", subject="数学", grade="八年级",
                knowledge_points=["二次函数"], material_type="interactive",
                content_url="/resources/interactive/quadratic_func.html",
                description="拖拽参数观察二次函数图像变化", quality_score=4.8,
            ),
            TeachingMaterial(
                id=uid(), title="勾股定理证明动画", subject="数学", grade="八年级",
                knowledge_points=["勾股定理"], material_type="video",
                content_url="/resources/video/pythagorean.mp4",
                description="5种经典勾股定理证明方法动画演示", quality_score=4.7,
            ),
        ]
        session.add_all(materials)

        await session.commit()
        print(f"种子数据填充完成！创建了 {len(teachers)} 位教师, {len(students_data)} 位学生, {len(exam_names)*len(students_data)} 条成绩记录")


if __name__ == "__main__":
    asyncio.run(seed_database())
