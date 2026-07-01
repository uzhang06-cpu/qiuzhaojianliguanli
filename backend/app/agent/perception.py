"""
感知层 (Perception) — 系统的「输入网关」。

职责：
  1. 接收前端传入的非结构化文本
  2. 自动挂载系统上下文（当前时间等）
  3. 文本清洗与预处理
  4. 输出标准化的 PerceptPacket
"""
from __future__ import annotations

from datetime import datetime

from app.agent.models import PerceptPacket


def process(raw_input: str) -> PerceptPacket:
    """
    感知入口：将原始输入包装为结构化感知包。

    参数:
        raw_input: 用户输入的原始文本

    返回:
        携带系统上下文的 PerceptPacket
    """
    now = datetime.now()

    packet = PerceptPacket(
        raw_input=raw_input.strip(),
        system_time=now,
        processed_text=_clean(raw_input),
        hints={
            "input_length": len(raw_input.strip()),
            "has_url": "http" in raw_input.lower(),
            "has_time_ref": any(kw in raw_input for kw in [
                "今天", "明天", "后天", "昨天", "下周", "本周",
                "周一", "周二", "周三", "周四", "周五", "周六", "周日",
                "月", "点", "时", "分",
            ]),
        },
    )
    return packet


def _clean(text: str) -> str:
    """基础文本清洗：去除多余空白、统一标点。"""
    text = text.strip()
    # 合并多个空格/换行为单空格
    import re
    text = re.sub(r"\s+", " ", text)
    # 全角逗号 → 半角
    text = text.replace("，", ",").replace("。", ".").replace("：", ":")
    return text.strip()
