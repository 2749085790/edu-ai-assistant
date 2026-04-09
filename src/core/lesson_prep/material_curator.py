"""
AI 智能备课系统 - 教学素材精选器
检索和推荐适合特定课题的教学素材资源
"""

import logging
from typing import List, Dict, Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import TeachingMaterial

logger = logging.getLogger(__name__)


class MaterialCurator:
    """
    教学素材精选器

    核心功能：
    - search_materials: 按关键词和条件检索素材
    - curate_by_topic: 按知识点自动精选最优素材组合
    - rank_materials: 按质量和相关性排序
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def search_materials(
        self,
        subject: str,
        grade: Optional[str] = None,
        knowledge_points: Optional[List[str]] = None,
        material_type: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """
        按条件检索教学素材

        Args:
            subject: 学科
            grade: 年级（可选）
            knowledge_points: 知识点列表（可选）
            material_type: 素材类型 video/document/image/interactive（可选）
            limit: 返回数量限制

        Returns:
            素材列表
        """
        conditions = [TeachingMaterial.subject == subject]

        if grade:
            conditions.append(TeachingMaterial.grade == grade)
        if material_type:
            conditions.append(TeachingMaterial.material_type == material_type)

        query = (
            select(TeachingMaterial)
            .where(and_(*conditions))
            .order_by(TeachingMaterial.quality_score.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        materials = result.scalars().all()

        # 如果指定了知识点，进一步过滤
        if knowledge_points:
            filtered = []
            for m in materials:
                if m.knowledge_points:
                    overlap = set(m.knowledge_points) & set(knowledge_points)
                    if overlap:
                        filtered.append(m)
            materials = filtered if filtered else materials

        return [self._to_dict(m) for m in materials]

    async def curate_by_topic(
        self,
        subject: str,
        grade: str,
        topic: str,
        knowledge_points: List[str],
        max_per_type: int = 3,
    ) -> Dict[str, List[Dict]]:
        """
        按知识点精选最优素材组合

        Returns:
            {
                "video": [...],
                "document": [...],
                "interactive": [...],
                "image": [...]
            }
        """
        result = {}
        material_types = ["video", "document", "interactive", "image"]

        for mt in material_types:
            materials = await self.search_materials(
                subject=subject,
                grade=grade,
                knowledge_points=knowledge_points,
                material_type=mt,
                limit=max_per_type,
            )
            if materials:
                result[mt] = materials

        logger.info(
            f"素材精选完成 | {subject} {grade} {topic} | "
            f"共 {sum(len(v) for v in result.values())} 个素材"
        )
        return result

    async def get_material_by_id(self, material_id: str) -> Optional[Dict]:
        """按 ID 获取素材"""
        result = await self.db.execute(
            select(TeachingMaterial).where(TeachingMaterial.id == material_id)
        )
        material = result.scalars().first()
        return self._to_dict(material) if material else None

    async def increment_usage(self, material_id: str):
        """增加素材使用计数"""
        result = await self.db.execute(
            select(TeachingMaterial).where(TeachingMaterial.id == material_id)
        )
        material = result.scalars().first()
        if material:
            material.usage_count += 1

    @staticmethod
    def _to_dict(material: TeachingMaterial) -> Dict:
        """将 ORM 对象转为字典"""
        return {
            "id": material.id,
            "title": material.title,
            "subject": material.subject,
            "grade": material.grade,
            "knowledge_points": material.knowledge_points or [],
            "material_type": material.material_type,
            "content_url": material.content_url,
            "description": material.description,
            "tags": material.tags or [],
            "quality_score": material.quality_score,
            "usage_count": material.usage_count,
        }
