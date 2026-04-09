"""
教培 AI 智能备课与学情分析系统 - 提示词管理器
支持 YAML 加载、Jinja2 渲染、内存缓存、热更新
"""

import os
import logging
from typing import Dict, Optional
from functools import lru_cache

import yaml
from jinja2 import Template

logger = logging.getLogger(__name__)


class PromptManager:
    """
    提示词版本管理与渲染引擎

    功能：
    - 从 YAML 文件加载提示词模板
    - 使用 Jinja2 渲染模板变量
    - 内存缓存 + 文件修改时间检测热更新
    """

    def __init__(self, base_dir: str = "src/prompts"):
        self.base_dir = base_dir
        self._cache: Dict[str, Dict] = {}
        self._mtimes: Dict[str, float] = {}

    def _get_prompt_path(self, category: str, name: str) -> str:
        """构建提示词文件路径"""
        path = os.path.join(self.base_dir, category, f"{name}.yaml")
        if not os.path.exists(path):
            raise FileNotFoundError(f"提示词文件不存在: {path}")
        return path

    def _should_reload(self, path: str) -> bool:
        """检查文件是否已修改（热更新检测）"""
        try:
            current_mtime = os.path.getmtime(path)
            cached_mtime = self._mtimes.get(path, 0)
            return current_mtime > cached_mtime
        except OSError:
            return True

    def load_prompt(self, category: str, name: str) -> Dict:
        """
        加载提示词 YAML 文件

        Args:
            category: 提示词分类 (lesson_prep / analytics / personalization / system)
            name: 提示词名称 (不含 .yaml 后缀)

        Returns:
            解析后的 YAML 字典
        """
        cache_key = f"{category}/{name}"
        path = self._get_prompt_path(category, name)

        # 检查缓存
        if cache_key in self._cache and not self._should_reload(path):
            return self._cache[cache_key]

        # 加载并缓存
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self._cache[cache_key] = data
        self._mtimes[path] = os.path.getmtime(path)
        logger.info(f"加载提示词 | {cache_key}")
        return data

    def render(self, template_str: str, **kwargs) -> str:
        """
        使用 Jinja2 渲染提示词模板

        Args:
            template_str: 包含 {{ variable }} 占位符的模板字符串
            **kwargs: 模板变量

        Returns:
            渲染后的字符串
        """
        template = Template(template_str)
        return template.render(**kwargs)

    def get_system_prompt(self, category: str, name: str, **kwargs) -> str:
        """
        获取渲染后的系统提示词

        Args:
            category: 分类
            name: 名称
            **kwargs: 渲染变量

        Returns:
            渲染后的系统提示词字符串
        """
        data = self.load_prompt(category, name)
        system_prompt = data.get("system_prompt", "")
        if kwargs:
            system_prompt = self.render(system_prompt, **kwargs)
        return system_prompt

    def get_user_prompt(self, category: str, name: str, template_key: str = "user_template", **kwargs) -> str:
        """
        获取渲染后的用户提示词

        Args:
            category: 分类
            name: 名称
            template_key: 用户模板的键名
            **kwargs: 渲染变量

        Returns:
            渲染后的用户提示词字符串
        """
        data = self.load_prompt(category, name)
        user_template = data.get(template_key, "")
        if kwargs:
            user_template = self.render(user_template, **kwargs)
        return user_template

    def get_full_prompt(self, category: str, name: str, **kwargs) -> Dict[str, str]:
        """
        获取完整的提示词对（system + user）

        Returns:
            {"system": "...", "user": "..."}
        """
        data = self.load_prompt(category, name)
        result = {}

        # 渲染系统提示词
        if "system_prompt" in data:
            result["system"] = self.render(data["system_prompt"], **kwargs) if kwargs else data["system_prompt"]

        # 渲染用户模板（尝试多个可能的键名）
        for key in ["user_template", "context_template", "data_input", "path_planning"]:
            if key in data:
                result["user"] = self.render(data[key], **kwargs) if kwargs else data[key]
                break

        # 附加输出格式要求
        for key in ["output_format", "output_requirements", "recommendation_output", "analysis_framework"]:
            if key in data:
                output = self.render(data[key], **kwargs) if kwargs else data[key]
                if "user" in result:
                    result["user"] += f"\n\n{output}"
                else:
                    result["user"] = output

        # 附加生成规则
        if "generation_rules" in data:
            rules = self.render(data["generation_rules"], **kwargs) if kwargs else data["generation_rules"]
            if "user" in result:
                result["user"] += f"\n\n{rules}"

        return result

    def list_prompts(self, category: Optional[str] = None) -> Dict[str, list]:
        """
        列出可用的提示词

        Returns:
            {category: [name1, name2, ...]}
        """
        result = {}
        search_dir = os.path.join(self.base_dir, category) if category else self.base_dir

        if category:
            if os.path.isdir(search_dir):
                files = [f[:-5] for f in os.listdir(search_dir) if f.endswith(".yaml")]
                result[category] = files
        else:
            for cat_dir in os.listdir(self.base_dir):
                cat_path = os.path.join(self.base_dir, cat_dir)
                if os.path.isdir(cat_path):
                    files = [f[:-5] for f in os.listdir(cat_path) if f.endswith(".yaml")]
                    if files:
                        result[cat_dir] = files
        return result

    def clear_cache(self):
        """清除所有缓存"""
        self._cache.clear()
        self._mtimes.clear()
        logger.info("提示词缓存已清除")
