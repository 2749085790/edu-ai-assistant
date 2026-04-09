"""
学情分析引擎 - 学习风险预警
综合多维度数据识别学习风险，生成干预建议
"""

import json
import logging
import uuid
from typing import List, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    Student, StudentPerformance, KnowledgeState, ErrorRecord, RiskAlert,
    RiskLevel, RiskType,
)
from src.services.ai_client import AIClient
from src.utils.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class RiskPredictor:
    """
    学习风险预测器

    核心功能：
    - predict_risk: 综合风险评估
    - generate_intervention: 干预建议生成
    - batch_predict: 批量风险扫描
    - get_risk_alerts: 获取风险预警列表
    """

    # 风险阈值
    HIGH_RISK = 0.8
    MEDIUM_RISK = 0.5

    def __init__(
        self,
        db_session: AsyncSession,
        ai_client: Optional[AIClient] = None,
        prompt_manager: Optional[PromptManager] = None,
    ):
        self.db = db_session
        self.ai = ai_client
        self.pm = prompt_manager

    async def predict_risk(
        self, student_id: str, subject: str = "数学"
    ) -> Dict:
        """
        综合风险评估

        基于以下特征进行风险预测：
        1. 成绩趋势斜率
        2. 知识点掌握波动
        3. 错题重复率
        4. 整体掌握度

        Returns:
            {
                "risk_level": "high/medium/low",
                "risk_factors": [...],
                "intervention_suggestions": [...],
                "confidence_score": 0.85
            }
        """
        logger.info(f"开始风险评估 | student_id={student_id}")

        # 收集特征数据
        features = await self._collect_features(student_id, subject)

        # 规则引擎预评估
        rule_result = self._rule_based_prediction(features)

        # 如果有 AI 客户端，使用 AI 增强预测
        if self.ai and self.pm:
            ai_result = await self._ai_enhanced_prediction(
                student_id, subject, features
            )
            # 综合规则和 AI 结果
            final_result = self._merge_predictions(rule_result, ai_result)
        else:
            final_result = rule_result

        # 持久化风险预警
        await self._save_risk_alert(student_id, final_result)

        logger.info(
            f"风险评估完成 | student_id={student_id} | "
            f"risk_level={final_result['risk_level']}"
        )
        return final_result

    async def _collect_features(
        self, student_id: str, subject: str
    ) -> Dict:
        """收集风险评估特征数据"""
        # 1. 成绩趋势
        perf_query = (
            select(StudentPerformance)
            .where(
                StudentPerformance.student_id == student_id,
                StudentPerformance.subject == subject,
            )
            .order_by(StudentPerformance.exam_date.asc())
        )
        perf_result = await self.db.execute(perf_query)
        performances = perf_result.scalars().all()
        scores = [p.score for p in performances]

        # 2. 知识状态
        kn_query = select(KnowledgeState).where(
            KnowledgeState.student_id == student_id,
            KnowledgeState.subject == subject,
        )
        kn_result = await self.db.execute(kn_query)
        knowledge_states = kn_result.scalars().all()
        masteries = [k.mastery_level for k in knowledge_states]

        # 3. 错题记录
        err_query = select(ErrorRecord).where(
            ErrorRecord.student_id == student_id,
            ErrorRecord.subject == subject,
        )
        err_result = await self.db.execute(err_query)
        errors = err_result.scalars().all()

        # 计算特征值
        score_trend = self._compute_trend_slope(scores) if len(scores) >= 2 else 0
        avg_mastery = sum(masteries) / len(masteries) if masteries else 0
        low_mastery_count = sum(1 for m in masteries if m < 0.6)
        error_count = len(errors)
        unresolved_errors = sum(1 for e in errors if not e.is_resolved)

        return {
            "scores": scores,
            "score_trend": score_trend,
            "avg_mastery": avg_mastery,
            "low_mastery_count": low_mastery_count,
            "total_knowledge_points": len(masteries),
            "error_count": error_count,
            "unresolved_errors": unresolved_errors,
            "mastery_variance": self._compute_variance(masteries),
        }

    def _rule_based_prediction(self, features: Dict) -> Dict:
        """基于规则的风险预测"""
        risk_factors = []
        risk_score = 0.0

        # 规则1: 成绩下降趋势
        if features["score_trend"] < -2.0:
            risk_factors.append({
                "type": "knowledge_gap",
                "severity": min(abs(features["score_trend"]) / 5, 1.0),
                "indicators": [f"成绩连续下滑，趋势斜率 {features['score_trend']:.1f}"],
                "threshold_breach": "成绩趋势斜率低于 -2.0",
            })
            risk_score += 0.3

        # 规则2: 知识掌握薄弱
        if features["total_knowledge_points"] > 0:
            weak_ratio = features["low_mastery_count"] / features["total_knowledge_points"]
            if weak_ratio > 0.5:
                risk_factors.append({
                    "type": "knowledge_gap",
                    "severity": weak_ratio,
                    "indicators": [
                        f"有 {features['low_mastery_count']}/{features['total_knowledge_points']} "
                        f"个知识点掌握度低于 60%"
                    ],
                    "threshold_breach": "超过 50% 的知识点未达标",
                })
                risk_score += 0.3

        # 规则3: 整体掌握度偏低
        if features["avg_mastery"] < 0.5:
            risk_factors.append({
                "type": "methodology",
                "severity": 1.0 - features["avg_mastery"],
                "indicators": [f"整体知识掌握度仅 {features['avg_mastery']:.0%}"],
                "threshold_breach": "整体掌握度低于 50%",
            })
            risk_score += 0.2

        # 规则4: 未解决的错题堆积
        if features["unresolved_errors"] > 5:
            risk_factors.append({
                "type": "motivation",
                "severity": min(features["unresolved_errors"] / 10, 1.0),
                "indicators": [f"有 {features['unresolved_errors']} 道错题未订正"],
                "threshold_breach": "未订正错题超过 5 道",
            })
            risk_score += 0.2

        # 确定风险等级
        risk_level = "low"
        if risk_score >= self.HIGH_RISK:
            risk_level = "high"
        elif risk_score >= self.MEDIUM_RISK:
            risk_level = "medium"

        # 生成干预建议
        interventions = self._generate_rule_interventions(risk_factors)

        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "intervention_suggestions": interventions,
            "confidence_score": min(risk_score + 0.3, 0.95),
        }

    async def _ai_enhanced_prediction(
        self, student_id: str, subject: str, features: Dict
    ) -> Dict:
        """AI 增强的风险预测"""
        # 获取学生信息
        student_result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        student = student_result.scalars().first()

        prompts = self.pm.get_full_prompt(
            category="analytics",
            name="risk_prediction",
            student_id=student_id,
            student_name=student.name if student else "未知",
            trend_window=5,
            score_trend=json.dumps(features["scores"], ensure_ascii=False),
            homework_quality=f"平均掌握度 {features['avg_mastery']:.0%}",
            knowledge_volatility=f"掌握度方差 {features['mastery_variance']:.3f}",
            error_repeat_rate=f"{features['unresolved_errors']}/{features['error_count']}" if features["error_count"] > 0 else "0",
            study_time_data="",
        )

        messages = [
            {"role": "system", "content": prompts["system"]},
            {"role": "user", "content": prompts["user"]},
        ]

        result = await self.ai.chat_json(messages)
        return result if isinstance(result, dict) and "risk_level" in result else {}

    def _merge_predictions(self, rule_result: Dict, ai_result: Dict) -> Dict:
        """合并规则引擎和 AI 的预测结果"""
        if not ai_result or "risk_level" not in ai_result:
            return rule_result

        # AI 结果的风险因素和干预建议作为补充
        merged = rule_result.copy()

        # 如果 AI 评估风险更高，采用 AI 的等级
        risk_order = {"low": 0, "medium": 1, "high": 2}
        ai_level = ai_result.get("risk_level", "low")
        rule_level = rule_result.get("risk_level", "low")

        if risk_order.get(ai_level, 0) > risk_order.get(rule_level, 0):
            merged["risk_level"] = ai_level

        # 合并风险因素
        ai_factors = ai_result.get("risk_factors", [])
        if ai_factors:
            merged["risk_factors"].extend(ai_factors)

        # 合并干预建议
        ai_interventions = ai_result.get("intervention_suggestions", [])
        if ai_interventions:
            merged["intervention_suggestions"].extend(ai_interventions)

        return merged

    async def _save_risk_alert(self, student_id: str, prediction: Dict):
        """持久化风险预警"""
        risk_level_map = {
            "high": RiskLevel.HIGH,
            "medium": RiskLevel.MEDIUM,
            "low": RiskLevel.LOW,
        }

        factors = prediction.get("risk_factors", [])
        primary_type = factors[0]["type"] if factors else "methodology"
        risk_type_map = {
            "knowledge_gap": RiskType.KNOWLEDGE_GAP,
            "motivation": RiskType.MOTIVATION,
            "methodology": RiskType.METHODOLOGY,
            "external": RiskType.EXTERNAL,
        }

        alert = RiskAlert(
            id=str(uuid.uuid4()),
            student_id=student_id,
            risk_level=risk_level_map.get(prediction["risk_level"], RiskLevel.LOW),
            risk_type=risk_type_map.get(primary_type, RiskType.METHODOLOGY),
            severity=prediction.get("confidence_score", 0.5),
            indicators=[ind for f in factors for ind in f.get("indicators", [])],
            intervention_suggestions=prediction.get("intervention_suggestions", []),
            confidence_score=prediction.get("confidence_score", 0.5),
        )
        self.db.add(alert)

    def _generate_rule_interventions(self, risk_factors: List[Dict]) -> List[Dict]:
        """基于风险因素生成规则化干预建议"""
        interventions = []
        priority = 1

        for factor in risk_factors:
            if factor["type"] == "knowledge_gap":
                interventions.append({
                    "priority": priority,
                    "action": "针对薄弱知识点进行专项补缺训练",
                    "responsible": "教师",
                    "timeline": "本周",
                    "expected_outcome": "薄弱知识点掌握度提升至 60% 以上",
                })
            elif factor["type"] == "motivation":
                interventions.append({
                    "priority": priority,
                    "action": "与学生进行一对一面谈，了解学习状态",
                    "responsible": "教师",
                    "timeline": "立即",
                    "expected_outcome": "明确学习动力不足的原因",
                })
            elif factor["type"] == "methodology":
                interventions.append({
                    "priority": priority,
                    "action": "指导学生调整学习方法和时间分配",
                    "responsible": "教师",
                    "timeline": "本周",
                    "expected_outcome": "学习效率提升",
                })
            priority += 1

        return interventions

    async def get_risk_alerts(
        self,
        is_resolved: Optional[bool] = None,
        risk_level: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """获取风险预警列表"""
        conditions = []
        if is_resolved is not None:
            conditions.append(RiskAlert.is_resolved == is_resolved)
        if risk_level:
            level_map = {"high": RiskLevel.HIGH, "medium": RiskLevel.MEDIUM, "low": RiskLevel.LOW}
            if risk_level in level_map:
                conditions.append(RiskAlert.risk_level == level_map[risk_level])

        query = (
            select(RiskAlert)
            .where(*conditions) if conditions else select(RiskAlert)
        ).order_by(RiskAlert.created_at.desc()).limit(limit)

        result = await self.db.execute(query)
        alerts = result.scalars().all()

        output = []
        for a in alerts:
            # 获取学生姓名
            student_result = await self.db.execute(
                select(Student.name).where(Student.id == a.student_id)
            )
            name_row = student_result.first()

            output.append({
                "id": a.id,
                "student_id": a.student_id,
                "student_name": name_row[0] if name_row else "未知",
                "risk_level": a.risk_level.value,
                "risk_type": a.risk_type.value,
                "severity": a.severity,
                "indicators": a.indicators or [],
                "intervention_suggestions": a.intervention_suggestions or [],
                "confidence_score": a.confidence_score,
                "is_resolved": a.is_resolved,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            })

        return output

    @staticmethod
    def _compute_trend_slope(values: List[float]) -> float:
        """计算趋势斜率"""
        n = len(values)
        if n < 2:
            return 0.0
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        num = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        den = sum((x[i] - x_mean) ** 2 for i in range(n))
        return num / den if den != 0 else 0.0

    @staticmethod
    def _compute_variance(values: List[float]) -> float:
        """计算方差"""
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)
