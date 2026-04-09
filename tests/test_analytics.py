"""
学情分析模块测试
覆盖 PerformanceTracker, KnowledgeMapper, RiskPredictor 中的纯逻辑方法
"""

import pytest
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# PerformanceTracker 趋势检测
# ---------------------------------------------------------------------------

from src.core.analytics.performance_tracker import PerformanceTracker


class TestPerformanceTracker:
    """PerformanceTracker 纯函数测试"""

    def _make_tracker(self):
        return PerformanceTracker(db_session=MagicMock())

    # -- _detect_trend -------------------------------------------------

    def test_detect_trend_ascending(self):
        """连续上升成绩 → '上升'"""
        t = self._make_tracker()
        trend, slope = t._detect_trend([60, 65, 70, 78, 85])
        assert trend == "上升"
        assert slope > 1.0

    def test_detect_trend_descending(self):
        """连续下降成绩 → '下降'"""
        t = self._make_tracker()
        trend, slope = t._detect_trend([90, 82, 75, 68, 60])
        assert trend == "下降"
        assert slope < -1.0

    def test_detect_trend_stable(self):
        """成绩波动不大 → '稳定'"""
        t = self._make_tracker()
        trend, slope = t._detect_trend([75, 76, 75, 74, 75])
        assert trend == "稳定"
        assert abs(slope) <= 1.0

    def test_detect_trend_single_score(self):
        """只有 1 条记录 → '无数据'"""
        t = self._make_tracker()
        trend, slope = t._detect_trend([80])
        assert trend == "无数据"
        assert slope == 0.0

    def test_detect_trend_two_scores(self):
        """2 条记录仍可判断趋势"""
        t = self._make_tracker()
        trend, slope = t._detect_trend([60, 90])
        assert trend == "上升"
        assert slope > 0

    def test_detect_trend_window(self):
        """只取最近 window 条，前面的老成绩不影响"""
        t = self._make_tracker()
        # 前 5 条下降，后 5 条上升；window=5 应检测为上升
        scores = [90, 85, 80, 75, 70, 72, 76, 80, 84, 90]
        trend, slope = t._detect_trend(scores, window=5)
        assert trend == "上升"


# ---------------------------------------------------------------------------
# KnowledgeMapper 知识诊断
# ---------------------------------------------------------------------------

from src.core.analytics.knowledge_mapper import KnowledgeMapper, MATH_KNOWLEDGE_GRAPH


class TestKnowledgeMapper:
    """KnowledgeMapper 纯函数 / 同步方法测试"""

    def _make_mapper(self):
        return KnowledgeMapper(db_session=MagicMock())

    # -- _classify_mastery ---------------------------------------------

    def test_classify_mastery_mastered(self):
        assert KnowledgeMapper._classify_mastery(0.85) == "已掌握"

    def test_classify_mastery_needs_practice(self):
        assert KnowledgeMapper._classify_mastery(0.65) == "待巩固"

    def test_classify_mastery_weak(self):
        assert KnowledgeMapper._classify_mastery(0.3) == "薄弱"

    def test_classify_mastery_boundary_80(self):
        assert KnowledgeMapper._classify_mastery(0.8) == "已掌握"

    def test_classify_mastery_boundary_60(self):
        assert KnowledgeMapper._classify_mastery(0.6) == "待巩固"

    # -- _detect_prerequisite_gaps -------------------------------------

    def test_detect_prerequisite_gaps_found(self):
        """
        一元二次方程 掌握度低 & 前置知识'一元一次方程'也低 → 检出
        """
        m = self._make_mapper()
        kps = {
            "一元二次方程": {"mastery": 0.3, "category": "代数"},
            "一元一次方程": {"mastery": 0.4, "category": "代数"},
            "因式分解": {"mastery": 0.8, "category": "代数"},
        }
        gaps = m._detect_prerequisite_gaps(kps)
        assert len(gaps) >= 1
        found = gaps[0]
        assert found["knowledge_point"] == "一元二次方程"
        assert "一元一次方程" in found["missing_prerequisites"]
        # 因式分解已掌握，不应出现在 missing_prerequisites
        assert "因式分解" not in found["missing_prerequisites"]

    def test_detect_prerequisite_gaps_none(self):
        """所有知识点均掌握 → 无缺失"""
        m = self._make_mapper()
        kps = {
            "一元二次方程": {"mastery": 0.9, "category": "代数"},
            "一元一次方程": {"mastery": 0.85, "category": "代数"},
            "因式分解": {"mastery": 0.8, "category": "代数"},
        }
        gaps = m._detect_prerequisite_gaps(kps)
        assert gaps == []

    def test_detect_prerequisite_gaps_missing_in_graph(self):
        """知识点不在图谱中 → 没有前置要求，不检出"""
        m = self._make_mapper()
        kps = {
            "不存在的知识点": {"mastery": 0.2, "category": "其他"},
        }
        gaps = m._detect_prerequisite_gaps(kps)
        assert gaps == []

    # -- 知识图谱结构完整性 --------------------------------------------

    def test_knowledge_graph_has_prerequisites(self):
        """每个图谱节点都有 prerequisites 和 category"""
        for name, info in MATH_KNOWLEDGE_GRAPH.items():
            assert "prerequisites" in info, f"{name} 缺少 prerequisites"
            assert "category" in info, f"{name} 缺少 category"
            assert isinstance(info["prerequisites"], list)


# ---------------------------------------------------------------------------
# RiskPredictor 规则引擎
# ---------------------------------------------------------------------------

from src.core.analytics.risk_predictor import RiskPredictor


class TestRiskPredictor:
    """RiskPredictor 纯函数测试"""

    def _make_predictor(self):
        return RiskPredictor(db_session=MagicMock())

    # -- _compute_trend_slope ------------------------------------------

    def test_trend_slope_ascending(self):
        slope = RiskPredictor._compute_trend_slope([60, 70, 80])
        assert slope > 0

    def test_trend_slope_descending(self):
        slope = RiskPredictor._compute_trend_slope([80, 70, 60])
        assert slope < 0

    def test_trend_slope_single(self):
        slope = RiskPredictor._compute_trend_slope([80])
        assert slope == 0.0

    def test_trend_slope_empty(self):
        slope = RiskPredictor._compute_trend_slope([])
        assert slope == 0.0

    # -- _compute_variance ---------------------------------------------

    def test_variance_zero(self):
        """全部相同的值 → 方差接近 0"""
        assert RiskPredictor._compute_variance([0.7, 0.7, 0.7]) < 1e-10

    def test_variance_positive(self):
        v = RiskPredictor._compute_variance([0.2, 0.8])
        assert v > 0

    def test_variance_empty(self):
        assert RiskPredictor._compute_variance([]) == 0.0

    # -- _rule_based_prediction ----------------------------------------

    def test_rule_high_risk(self):
        """
        同时满足 成绩大幅下滑 + 大量薄弱知识点 + 整体掌握度低 → high
        """
        p = self._make_predictor()
        features = {
            "scores": [90, 80, 70, 60, 50],
            "score_trend": -10.0,
            "avg_mastery": 0.35,
            "low_mastery_count": 8,
            "total_knowledge_points": 10,
            "error_count": 15,
            "unresolved_errors": 10,
            "mastery_variance": 0.12,
        }
        result = p._rule_based_prediction(features)
        assert result["risk_level"] == "high"
        assert len(result["risk_factors"]) >= 3
        assert len(result["intervention_suggestions"]) >= 1

    def test_rule_low_risk(self):
        """所有指标良好 → low"""
        p = self._make_predictor()
        features = {
            "scores": [80, 82, 85],
            "score_trend": 2.5,
            "avg_mastery": 0.82,
            "low_mastery_count": 0,
            "total_knowledge_points": 10,
            "error_count": 2,
            "unresolved_errors": 1,
            "mastery_variance": 0.01,
        }
        result = p._rule_based_prediction(features)
        assert result["risk_level"] == "low"
        assert result["risk_factors"] == []

    def test_rule_medium_risk(self):
        """只触发部分规则 → medium"""
        p = self._make_predictor()
        features = {
            "scores": [80, 75, 70, 65, 60],
            "score_trend": -5.0,
            "avg_mastery": 0.45,
            "low_mastery_count": 6,
            "total_knowledge_points": 10,
            "error_count": 10,
            "unresolved_errors": 7,
            "mastery_variance": 0.05,
        }
        result = p._rule_based_prediction(features)
        assert result["risk_level"] in ("medium", "high")

    # -- _merge_predictions --------------------------------------------

    def test_merge_ai_higher_risk(self):
        """AI 判定更高风险 → 采用 AI 等级"""
        p = self._make_predictor()
        rule = {"risk_level": "low", "risk_factors": [], "intervention_suggestions": [], "confidence_score": 0.4}
        ai = {"risk_level": "high", "risk_factors": [{"type": "knowledge_gap"}], "intervention_suggestions": []}
        merged = p._merge_predictions(rule, ai)
        assert merged["risk_level"] == "high"

    def test_merge_empty_ai(self):
        """AI 结果为空 → 直接用规则结果"""
        p = self._make_predictor()
        rule = {"risk_level": "medium", "risk_factors": [], "intervention_suggestions": [], "confidence_score": 0.6}
        merged = p._merge_predictions(rule, {})
        assert merged["risk_level"] == "medium"

    # -- _generate_rule_interventions ----------------------------------

    def test_interventions_for_knowledge_gap(self):
        p = self._make_predictor()
        factors = [{"type": "knowledge_gap", "severity": 0.8, "indicators": ["下滑"]}]
        result = p._generate_rule_interventions(factors)
        assert len(result) == 1
        assert "薄弱知识点" in result[0]["action"]

    def test_interventions_for_motivation(self):
        p = self._make_predictor()
        factors = [{"type": "motivation", "severity": 0.6, "indicators": ["未订正"]}]
        result = p._generate_rule_interventions(factors)
        assert "面谈" in result[0]["action"]

    def test_interventions_multiple(self):
        p = self._make_predictor()
        factors = [
            {"type": "knowledge_gap", "severity": 0.8, "indicators": []},
            {"type": "methodology", "severity": 0.5, "indicators": []},
        ]
        result = p._generate_rule_interventions(factors)
        assert len(result) == 2
