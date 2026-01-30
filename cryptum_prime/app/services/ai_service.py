import base64
from dataclasses import dataclass
from typing import Any

from openai import AsyncOpenAI

from app.core.config import get_settings


@dataclass
class AnalysisResult:
    signal: str
    reasoning: str
    entry: str | None
    stop_loss: str | None
    take_profit: str | None
    risks: str
    confidence: int | None


class AIService:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.vision_model = settings.openai_vision_model

    async def analyze_chart(self, image_bytes: bytes, pair: str, timeframe: str) -> AnalysisResult:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        prompt = (
            "You are a crypto chart analyst. Provide educational analysis only. "
            "Return a concise response with signal, reasoning, entry, stop loss, "
            "take profit, risks, and confidence percentage. Avoid financial advice language."
        )

        response = await self.client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Analyze the chart for {pair} on {timeframe}. "
                                "Respond in this format:\n"
                                "Signal: <LONG/SHORT/NO TRADE>\n"
                                "Reasoning: <technical reasoning>\n"
                                "Entry: <value or N/A>\n"
                                "Stop Loss: <value or N/A>\n"
                                "Take Profit: <value or N/A>\n"
                                "Risks: <risk notes>\n"
                                "Confidence: <percent>"
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_b64}",
                            },
                        },
                    ],
                },
            ],
            temperature=0.4,
        )
        content = response.choices[0].message.content or ""
        return self._parse_response(content)

    def _parse_response(self, content: str) -> AnalysisResult:
        data: dict[str, Any] = {
            "signal": "NO TRADE",
            "reasoning": "",
            "entry": None,
            "stop_loss": None,
            "take_profit": None,
            "risks": "",
            "confidence": None,
        }
        for line in content.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            normalized = key.strip().lower()
            value = value.strip()
            if normalized.startswith("signal"):
                data["signal"] = value.upper()
            elif normalized.startswith("reasoning"):
                data["reasoning"] = value
            elif normalized.startswith("entry"):
                data["entry"] = value
            elif normalized.startswith("stop"):
                data["stop_loss"] = value
            elif normalized.startswith("take"):
                data["take_profit"] = value
            elif normalized.startswith("risks"):
                data["risks"] = value
            elif normalized.startswith("confidence"):
                percent = value.replace("%", "").strip()
                if percent.isdigit():
                    data["confidence"] = int(percent)
        return AnalysisResult(**data)
