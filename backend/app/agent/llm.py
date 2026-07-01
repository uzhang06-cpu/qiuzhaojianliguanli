"""
LLM 后端抽象层 — 支持 Mock / OpenAI / DashScope 三种模式。

通过 `active_backend` 全局切换，默认使用 Mock（规则引擎），
无需 API Key 即可跑通全链路。
"""
from __future__ import annotations

import abc
import os
import re
from datetime import datetime, timedelta
from typing import Optional

from app.agent.models import IntentType, SkillType


# ── 抽象基类 ─────────────────────────────────────────────────────────


class LLMBackend(abc.ABC):
    """LLM 后端抽象接口。"""

    @abc.abstractmethod
    def classify_intent(self, text: str, system_time: datetime) -> tuple[IntentType, float, str]:
        """意图分类 → (意图, 置信度, 原始描述)"""
        ...

    @abc.abstractmethod
    def extract_entities(
        self, text: str, skill: SkillType, system_time: datetime
    ) -> list[dict]:
        """实体提取 → [{field, value, confidence, display_text}, ...]"""
        ...

    @abc.abstractmethod
    def validate_and_fix(
        self, data: dict, schema_hint: str
    ) -> tuple[bool, dict, Optional[str]]:
        """校验并修复数据 → (是否通过, 修复后数据, 错误信息)"""
        ...


# ── Mock 规则引擎后端（默认） ────────────────────────────────────────


class MockLLMBackend(LLMBackend):
    """
    基于正则与规则的 Mock 后端。
    无需网络、无需 API Key，可用于开发测试与降级兜底。
    """

    # 常见中英文公司名模式
    COMPANY_PATTERNS = [
        r"字节跳动|字节|抖音",
        r"阿里巴巴|阿里",
        r"腾讯|Tencent",
        r"百度|Baidu",
        r"美团|Meituan",
        r"拼多多|拼夕夕|Pinduoduo",
        r"网易|NetEase",
        r"京东|JD\.com",
        r"小红书|RED",
        r"快手|Kuaishou",
        r"华为|Huawei",
        r"小米|Xiaomi",
        r"滴滴|DiDi",
        r"哔哩哔哩|B站|Bilibili",
        r"蚂蚁集团|蚂蚁|Ant Group",
        r"微众银行|WeBank",
        r"理想汽车|理想|Li Auto",
        r"蔚来|NIO",
        r"小鹏|XPeng",
        r"中兴|ZTE",
        r"OPPO|一加|OnePlus",
        r"vivo",
        r"携程|Trip\.com",
        r"微软|Microsoft",
        r"谷歌|Google",
        r"亚马逊|Amazon|AWS",
        r"苹果|Apple",
        r"Meta|Facebook",
        r"特斯拉|Tesla",
        r"商汤|SenseTime",
        r"旷视|Megvii",
    ]

    # 岗位关键词
    POSITION_KEYWORDS = [
        "前端开发", "后端开发", "全栈开发", "客户端开发", "移动端开发",
        "算法工程师", "深度学习", "机器学习", "NLP", "计算机视觉",
        "数据分析", "数据开发", "数据仓库", "大数据",
        "测试开发", "软件测试", "QA",
        "运维开发", "SRE", "DevOps",
        "产品经理", "产品运营", "用户研究",
        "UI设计", "UX设计", "视觉设计",
        "技术支持", "技术顾问",
        "Java", "Go", "Python", "C\\+\\+", "Rust",
        "前端", "后端", "全栈",
    ]

    # 时间关键词
    WEEKDAY_MAP = {
        "周一": 0, "星期二": 1, "周二": 1, "星期三": 2, "周三": 2,
        "星期四": 3, "周四": 3, "星期五": 4, "周五": 4,
        "星期六": 5, "周六": 5, "星期日": 6, "周日": 6, "星期天": 6,
    }

    # 中文数字映射
    CN_NUM_MAP = {
        "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
        "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    }

    INTENT_KEYWORDS = {
        IntentType.CREATE_POSITION: [
            "收到.*offer", "拿到.*offer", "投递", "海投", "网申",
            "岗位", "招聘", "JD", "职位描述", "招.*实习生",
            "找.*工作", "求职",
        ],
        IntentType.UPDATE_INTERVIEW: [
            "面试.*通知", "面试.*时间", "二面", "一面", "三面",
            "HR面", "技术面", "群面", "交叉面",
            "面试.*链接", "面试.*平台", "腾讯会议", "飞书", "Zoom",
            "下周", "本周", "明天", "后天",
        ],
        IntentType.UPDATE_STATUS: [
            "挂了", "拒信", "感谢信", "人才库", "Offer",
            "已投递", "笔试", "测评", "行测",
            "AI面", "AI面试",
        ],
        IntentType.ADD_NOTES: [
            "复盘", "总结", "面试体验", "面试官", "面经",
        ],
        IntentType.QUERY: [
            "查.*状态", "查.*进度", "有哪些", "列表",
            "什么时候", "有没有",
        ],
    }

    def classify_intent(self, text: str, system_time: datetime) -> tuple[IntentType, float, str]:
        text_lower = text.lower()

        # 逐意图关键词匹配
        best_intent = IntentType.UNKNOWN
        best_score = 0.0
        best_match = ""

        for intent, patterns in self.INTENT_KEYWORDS.items():
            score = 0.0
            matched = []
            for p in patterns:
                if re.search(p, text, re.IGNORECASE):
                    score += 1.0
                    matched.append(p)
            if score > 0:
                avg = score / len(patterns)
                normalized = min(avg * 2, 0.95)
                if normalized > best_score:
                    best_score = normalized
                    best_intent = intent
                    best_match = "; ".join(matched[:3])

        # ③ 兜底策略：检测公司名 + 岗位名 → CREATE_POSITION
        has_company = self._extract_company(text) is not None
        has_position = self._extract_position(text) is not None
        has_salary = self._extract_salary(text) is not None

        if best_intent == IntentType.UNKNOWN and has_company and has_position:
            best_intent = IntentType.CREATE_POSITION
            best_score = 0.6
            best_match = f"公司+岗位组合匹配 ({self._extract_company(text)}/{self._extract_position(text)})"
        elif best_intent == IntentType.UNKNOWN and has_company and has_salary:
            best_intent = IntentType.CREATE_POSITION
            best_score = 0.55
            best_match = f"公司+薪资组合匹配 ({self._extract_company(text)})"
        elif best_intent == IntentType.UNKNOWN and has_position and has_salary:
            best_intent = IntentType.CREATE_POSITION
            best_score = 0.5
            best_match = f"岗位+薪资组合匹配 ({self._extract_position(text)})"

        # ④ 时间提及且无更明确的意图 → UPDATE_INTERVIEW
        if best_intent == IntentType.UNKNOWN and re.search(r"(下周|本周|明天|后天|周[一二三四五六日])", text):
            best_intent = IntentType.UPDATE_INTERVIEW
            best_score = 0.5
            best_match = "检测到时间提及"

        return best_intent, round(best_score, 2), best_match

    def extract_entities(
        self, text: str, skill: SkillType, system_time: datetime
    ) -> list[dict]:
        if skill == SkillType.TEXT_PARSING:
            return self._extract_text_entities(text)
        elif skill == SkillType.SCHEDULE_PARSING:
            return self._extract_schedule_entities(text, system_time)
        return []

    def _extract_text_entities(self, text: str) -> list[dict]:
        entities = []

        # 公司名
        company = self._extract_company(text)
        if company:
            entities.append({
                "field": "company",
                "value": company,
                "confidence": 0.8,
                "display_text": company,
            })

        # 岗位名
        position = self._extract_position(text)
        if position:
            entities.append({
                "field": "position",
                "value": position,
                "confidence": 0.7,
                "display_text": position,
            })

        # Base 地
        location = self._extract_location(text)
        if location:
            entities.append({
                "field": "base_location",
                "value": location,
                "confidence": 0.6,
                "display_text": location,
            })

        # 薪资范围
        salary = self._extract_salary(text)
        if salary:
            entities.append({
                "field": "salary_range",
                "value": salary,
                "confidence": 0.7,
                "display_text": salary,
            })

        return entities

    def _extract_schedule_entities(self, text: str, system_time: datetime) -> list[dict]:
        entities = []

        # 时间
        dt = self._parse_relative_time(text, system_time)
        if dt:
            entities.append({
                "field": "next_ddl",
                "value": dt.isoformat(),
                "confidence": 0.8,
                "display_text": dt.strftime("%Y-%m-%d %H:%M"),
            })

        # 面试平台
        platform = self._extract_platform(text)
        if platform:
            entities.append({
                "field": "interview_platform",
                "value": platform,
                "confidence": 0.9,
                "display_text": platform,
            })

        # 面试链接
        link = self._extract_link(text)
        if link:
            entities.append({
                "field": "interview_link",
                "value": link,
                "confidence": 0.95,
                "display_text": link,
            })

        return entities

    def _extract_company(self, text: str) -> Optional[str]:
        for pattern_group in self.COMPANY_PATTERNS:
            m = re.search(pattern_group, text)
            if m:
                return m.group(0)
        return None

    def _extract_position(self, text: str) -> Optional[str]:
        for kw in self.POSITION_KEYWORDS:
            m = re.search(kw, text)
            if m:
                return m.group(0)
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        # 常见城市名
        cities = (
            r"北京|上海|广州|深圳|杭州|成都|南京|武汉|西安|苏州|长沙|天津"
            r"重庆|厦门|珠海|青岛|大连|合肥|宁波|无锡|佛山|东莞"
        )
        m = re.search(cities, text)
        return m.group(0) if m else None

    def _extract_salary(self, text: str) -> Optional[str]:
        # 匹配 "20k-40k" "20K-40K" "2万-4万" "20k" 等
        m = re.search(r"(\d+\.?\d*)[kK]\s*[-~]\s*(\d+\.?\d*)[kK]", text)
        if m:
            return f"{m.group(1)}k-{m.group(2)}k"
        m = re.search(r"(\d+\.?\d*)[kK]", text)
        if m:
            return f"{m.group(1)}k"
        return None

    def _extract_platform(self, text: str) -> Optional[str]:
        platforms = {
            "腾讯会议": r"腾讯会议",
            "飞书": r"飞书|ByteDance Meeting|飞书会议",
            "Zoom": r"Zoom",
            "Teams": r"Teams|Microsoft Teams",
            "钉钉": r"钉钉",
            "企业微信": r"企业微信",
            "牛客": r"牛客",
            "赛码": r"赛码",
        }
        for name, pattern in platforms.items():
            if re.search(pattern, text, re.IGNORECASE):
                return name
        return None

    def _extract_link(self, text: str) -> Optional[str]:
        m = re.search(r"https?://[^\s,，、]+", text)
        return m.group(0) if m else None

    def _parse_relative_time(
        self, text: str, system_time: datetime
    ) -> Optional[datetime]:
        """解析相对时间（下周三下午两点 → 绝对时间）。"""
        dt = system_time.replace(second=0, microsecond=0)

        # 提取时间部分（上午/下午 + 小时:分钟）
        hour, minute = 9, 0  # 默认上午9点

        # 尝试匹配 "10:30" 或 "10：30" 格式
        time_match = re.search(
            r"(上午|下午|早上|晚上|中午)?\s*(\d+)[:：](\d+)", text
        )
        if time_match:
            ampm = time_match.group(1) or ""
            hour = int(time_match.group(2))
            minute = int(time_match.group(3))
            hour, minute = self._adjust_ampm(ampm, hour, minute)
        else:
            # 匹配 "下午2点"、"两点"、"10点半"、"两点半" 等中文格式
            time_match = re.search(
                r"(上午|下午|早上|晚上|中午)?\s*(\d+|两|半)\s*点\s*(半|一刻)?",
                text,
            )
            if time_match:
                ampm = time_match.group(1) or ""
                hour_str = time_match.group(2)
                minute_str = time_match.group(3) if time_match.lastindex >= 3 else None

                hour = self._cn_to_int(hour_str)
                minute = 30 if minute_str == "半" else 15 if minute_str == "一刻" else 0
                hour, minute = self._adjust_ampm(ampm, hour, minute)

        dt = dt.replace(hour=hour, minute=minute)

        # 提取日期部分
        # "下周三"
        for weekday_cn, weekday_num in self.WEEKDAY_MAP.items():
            if weekday_cn in text:
                days_ahead = weekday_num - dt.weekday()
                if "下" in text:
                    days_ahead += 7
                elif "上" in text:
                    days_ahead -= 7
                if days_ahead <= 0 and "下" in text:
                    days_ahead += 7
                if "这" in text or "本" in text:
                    if days_ahead < 0:
                        days_ahead += 7
                dt += timedelta(days=days_ahead)
                return dt

        # "明天"
        if "明天" in text or "明日" in text:
            dt += timedelta(days=1)
            return dt
        if "后天" in text:
            dt += timedelta(days=2)
            return dt

        # 具体日期 "7月15日" "7月15"
        date_match = re.search(r"(\d+)\s*月\s*(\d+)\s*日?", text)
        if date_match:
            month, day = int(date_match.group(1)), int(date_match.group(2))
            year = system_time.year
            dt = dt.replace(year=year, month=month, day=day)
            return dt

        return None

    def _cn_to_int(self, s: str) -> int:
        """中文数字 → 整数。"""
        if s in self.CN_NUM_MAP:
            return self.CN_NUM_MAP[s]
        try:
            return int(s)
        except ValueError:
            return 0

    def _adjust_ampm(self, ampm: str, hour: int, minute: int) -> tuple[int, int]:
        """根据上午/下午调整小时。"""
        if ampm in ("下午", "晚上") and hour < 12:
            hour += 12
        if ampm == "上午" and hour == 12:
            hour = 0
        if ampm == "中午" and hour < 12:
            hour += 12
        return hour, minute

    def validate_and_fix(
        self, data: dict, schema_hint: str
    ) -> tuple[bool, dict, Optional[str]]:
        """Mock 校验：公司名缺失时降级。"""
        if schema_hint == "create_position":
            if not data.get("company"):
                return False, data, "公司名称缺失"

        if schema_hint == "update_interview":
            if not data.get("next_ddl") and not data.get("interview_link"):
                return False, data, "面试时间和链接均缺失，至少需要一项"

        return True, data, None


# ── OpenAI 后端（当 API Key 可用时） ─────────────────────────────────


class OpenAIBackend(LLMBackend):
    """基于 OpenAI API 的 LLM 后端。"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        import openai
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
        self.model = model

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        return resp.choices[0].message.content or ""

    def classify_intent(self, text: str, system_time: datetime) -> tuple[IntentType, float, str]:
        prompt = (
            f"当前时间: {system_time.isoformat()}\n"
            f"用户输入: {text}\n\n"
            "请判断意图类别: create_position / update_status / update_interview / add_notes / query / unknown\n"
            "返回格式: intent|confidence|description"
        )
        result = self._call("你是一个求职管理系统的意图分类器。", prompt)
        parts = result.split("|")
        try:
            intent = IntentType(parts[0].strip())
            conf = float(parts[1].strip())
            desc = parts[2].strip() if len(parts) > 2 else ""
            return intent, conf, desc
        except (ValueError, IndexError):
            return IntentType.UNKNOWN, 0.0, result

    def extract_entities(self, text: str, skill: SkillType, system_time: datetime) -> list[dict]:
        prompts = {
            SkillType.TEXT_PARSING: (
                f"从以下文本中提取公司名、岗位名、Base地、薪资范围。\n文本: {text}\n"
                "返回JSON数组: [{\"field\": \"company\", \"value\": \"...\", ...}]"
            ),
            SkillType.SCHEDULE_PARSING: (
                f"当前时间: {system_time.isoformat()}\n"
                f"从以下文本提取: 面试时间(绝对时间)、平台、链接。\n文本: {text}\n"
                "返回JSON数组: [{\"field\": \"next_ddl\", \"value\": \"2024-...\", ...}]"
            ),
        }
        import json
        prompt = prompts.get(skill, "")
        if not prompt:
            return []
        result = self._call("你是一个实体提取器，只返回JSON。", prompt)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return []

    def validate_and_fix(self, data: dict, schema_hint: str) -> tuple[bool, dict, Optional[str]]:
        prompt = (
            f"Schema: {schema_hint}\n"
            f"数据: {data}\n"
            "请校验数据完整性，如果缺少关键字段请补充或标记。返回JSON: {\"valid\": bool, \"data\": {...}, \"error\": \"\"}"
        )
        import json
        result = self._call("你是一个数据校验器。", prompt)
        try:
            parsed = json.loads(result)
            return parsed.get("valid", False), parsed.get("data", data), parsed.get("error")
        except json.JSONDecodeError:
            return True, data, None


# ── DeepSeek 后端（通过 OpenAI 兼容 API） ──────────────────────────────


class DeepSeekBackend(LLMBackend):
    """
    基于 DeepSeek API 的 LLM 后端。

    DeepSeek 提供 OpenAI 兼容接口，只需改 base_url 和 model 名。
    环境变量:
      DEEPSEEK_API_KEY — API Key
      DEEPSEEK_BASE_URL — 可选，默认 https://api.deepseek.com
      DEEPSEEK_MODEL    — 可选，默认 deepseek-chat
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        import openai
        self.client = openai.OpenAI(
            api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
            base_url=base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

    def _call(self, system_prompt: str, user_prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        return resp.choices[0].message.content or ""

    def classify_intent(self, text: str, system_time: datetime) -> tuple[IntentType, float, str]:
        prompt = (
            f"当前时间: {system_time.isoformat()}\n"
            f"用户输入: {text}\n\n"
            "请判断意图类别: create_position / update_status / update_interview / add_notes / query / unknown\n"
            "返回格式: intent|confidence|description"
        )
        result = self._call("你是一个求职管理系统的意图分类器，只返回格式化的结果。", prompt)
        parts = result.split("|")
        try:
            intent = IntentType(parts[0].strip())
            conf = float(parts[1].strip())
            desc = parts[2].strip() if len(parts) > 2 else ""
            return intent, conf, desc
        except (ValueError, IndexError):
            return IntentType.UNKNOWN, 0.0, result

    def extract_entities(self, text: str, skill: SkillType, system_time: datetime) -> list[dict]:
        prompts = {
            SkillType.TEXT_PARSING: (
                f"从以下文本中提取公司名、岗位名、Base地、薪资范围。\n文本: {text}\n"
                "返回JSON数组: [{\"field\": \"company\", \"value\": \"...\", ...}]"
            ),
            SkillType.SCHEDULE_PARSING: (
                f"当前时间: {system_time.isoformat()}\n"
                f"从以下文本提取: 面试时间(绝对时间)、平台、链接。\n文本: {text}\n"
                "返回JSON数组: [{\"field\": \"next_ddl\", \"value\": \"2024-...\", ...}]"
            ),
        }
        import json
        prompt = prompts.get(skill, "")
        if not prompt:
            return []
        result = self._call("你是一个实体提取器，只返回JSON数组。", prompt)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return []

    def validate_and_fix(self, data: dict, schema_hint: str) -> tuple[bool, dict, Optional[str]]:
        prompt = (
            f"Schema: {schema_hint}\n"
            f"数据: {data}\n"
            "请校验数据完整性，如果缺少关键字段请补充或标记。返回JSON: {\"valid\": bool, \"data\": {...}, \"error\": \"\"}"
        )
        import json
        result = self._call("你是一个数据校验器，只返回JSON。", prompt)
        try:
            parsed = json.loads(result)
            return parsed.get("valid", False), parsed.get("data", data), parsed.get("error")
        except json.JSONDecodeError:
            return True, data, None


# ── 后端工厂 & 全局实例 ──────────────────────────────────────────────


_BACKEND: Optional[LLMBackend] = None


def get_llm_backend() -> LLMBackend:
    """获取当前 LLM 后端（单例）。

    优先级: DeepSeek > OpenAI > Mock
    设置对应环境变量即可自动切换，无需改代码。
    """
    global _BACKEND
    if _BACKEND is not None:
        return _BACKEND

    if os.getenv("DEEPSEEK_API_KEY"):
        _BACKEND = DeepSeekBackend()
    elif os.getenv("OPENAI_API_KEY"):
        _BACKEND = OpenAIBackend()
    else:
        _BACKEND = MockLLMBackend()

    return _BACKEND


def set_llm_backend(backend: LLMBackend):
    """注入自定义后端（用于测试或切换）。"""
    global _BACKEND
    _BACKEND = backend
