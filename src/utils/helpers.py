"""
教培 AI 智能备课与学情分析系统 - 通用工具函数
"""

import json
import hashlib
from datetime import datetime, date
from typing import Any, Dict, List, Optional


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    if dt is None:
        return ""
    return dt.strftime(fmt)


def format_date(d: date, fmt: str = "%Y-%m-%d") -> str:
    """格式化日期"""
    if d is None:
        return ""
    return d.strftime(fmt)


def format_percent(value: float, decimals: int = 0) -> str:
    """格式化百分比"""
    return f"{value * 100:.{decimals}f}%"


def classify_mastery(level: float) -> str:
    """知识掌握度分类"""
    if level >= 0.8:
        return "已掌握"
    elif level >= 0.6:
        return "待巩固"
    else:
        return "薄弱"


def mastery_color(level: float) -> str:
    """掌握度对应颜色"""
    if level >= 0.8:
        return "#22C55E"  # green
    elif level >= 0.6:
        return "#F59E0B"  # amber
    else:
        return "#EF4444"  # red


def truncate_text(text: str, max_length: int = 100) -> str:
    """截断文本，超长加省略号"""
    if not text:
        return ""
    return text[:max_length] + "..." if len(text) > max_length else text


def compute_linear_regression(values: List[float]) -> tuple:
    """
    计算简单线性回归

    Returns:
        (slope, intercept)
    """
    n = len(values)
    if n < 2:
        return 0.0, 0.0

    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(values) / n

    numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return 0.0, y_mean

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    return slope, intercept


def compute_variance(values: List[float]) -> float:
    """计算方差"""
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def compute_std_dev(values: List[float]) -> float:
    """计算标准差"""
    return compute_variance(values) ** 0.5


def safe_json_loads(text: str, default: Any = None) -> Any:
    """安全的 JSON 解析"""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def generate_cache_key(*args) -> str:
    """生成缓存键"""
    raw = ":".join(str(a) for a in args)
    return hashlib.md5(raw.encode()).hexdigest()


def paginate(items: list, page: int = 1, page_size: int = 20) -> Dict:
    """通用分页函数"""
    total = len(items)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
