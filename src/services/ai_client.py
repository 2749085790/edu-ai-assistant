"""
教培 AI 智能备课与学情分析系统 - 通义千问 API 统一封装
支持流式/非流式调用，兼容 OpenAI 接口格式
"""

import os
import json
import logging
from typing import AsyncGenerator, Optional, List, Dict

import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class AIClient:
    """
    AI 大模型统一客户端
    默认使用通义千问 DashScope 兼容 OpenAI 格式的接口
    """

    # DashScope OpenAI 兼容端点
    DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "qwen-plus",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.9,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.base_url = base_url or self.DASHSCOPE_BASE_URL
        self._client = httpx.AsyncClient(timeout=120.0)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None,
    ) -> str:
        """
        非流式调用：返回完整响应文本
        """
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "top_p": self.top_p,
        }
        if response_format:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = await self._client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            logger.info(f"AI 调用成功 | model={payload['model']} | tokens={data.get('usage', {})}")
            return content
        except httpx.HTTPStatusError as e:
            logger.error(f"AI 调用失败 | status={e.response.status_code} | body={e.response.text}")
            raise
        except Exception as e:
            logger.error(f"AI 调用异常 | error={str(e)}")
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式调用：逐块返回响应文本
        """
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "top_p": self.top_p,
            "stream": True,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with self._client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"AI 流式调用异常 | error={str(e)}")
            raise

    async def chat_json(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> Dict:
        """
        调用 AI 并解析 JSON 响应
        """
        content = await self.chat(
            messages=messages,
            model=model,
            response_format={"type": "json_object"},
        )
        # 尝试提取 JSON（AI 可能返回 markdown 代码块包裹的 JSON）
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            # 去掉首行 ```json 和末行 ```
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.strip() == "```":
                    break
                elif in_block:
                    json_lines.append(line)
            content = "\n".join(json_lines)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"JSON 解析失败，返回原始文本 | content={content[:200]}")
            return {"raw_content": content}

    async def generate_with_system_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        便捷方法：使用系统提示词 + 用户提示词生成内容
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
        )

    async def close(self):
        """关闭 HTTP 客户端"""
        await self._client.aclose()
