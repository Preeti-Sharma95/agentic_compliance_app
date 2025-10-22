from __future__ import annotations

from typing import Any, Optional
from langchain_groq import Chatgroq
from src.core.config import get_settings
settings = get_settings()
import logging

def _normalize_model(name: Optional[str]) ->str:
    if not name:
        return "llama-3.3-70-versatile"
    return _DEPRECATD_TO_CURRENT.get(name, name)

class GroqAdapter:
    def __init__(
            self,
            model: Optional[str] = None,
            *,
            temperature: Optional[float] = None,
            streaming: Optional[bool] = None,
            max_tokens: Optional[int] = None,
            groq_api_key: Optional[str] = None,
            **kwargs: Any,
    ) -> None:
        s = get_settings()

        api_key = groq_api_key or s.groq_api_key.get_secret_value()

        if not api_key:
            raise ValueError("GROQ API KEY is not configured in settings (.env)")

        model_name = _normalize_model(model or s.model_name)
        temp = s.temperature if temperature is None else float(temperature)
        stream = s.streaming if streaming is None else bool(streaming)
        max_toks = s.max_tokens if max_tokens is None else int(max_tokens)


        self.llm = Chatgroq(
            groq_api_key=api_key,
            model_name=model_name,
            temperature=temp,

        )

