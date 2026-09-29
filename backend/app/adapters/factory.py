"""
Provider factory — returns the appropriate adapter based on configured API keys.
Automatically falls back to demo mode when no keys are present.
"""
from app.core.config import settings
from app.adapters.base import LLMAdapter, ImageAdapter, TTSAdapter
from app.adapters.demo import DemoLLMAdapter, DemoImageAdapter, DemoTTSAdapter


def get_llm_adapter() -> LLMAdapter:
    if settings.has_llm:
        from app.adapters.openai_adapter import OpenAILLMAdapter
        return OpenAILLMAdapter()
    return DemoLLMAdapter()


def get_image_adapter() -> ImageAdapter:
    if settings.has_image_gen:
        from app.adapters.openai_adapter import OpenAIImageAdapter
        return OpenAIImageAdapter()
    return DemoImageAdapter()


def get_tts_adapter() -> TTSAdapter:
    if settings.has_tts:
        from app.adapters.openai_adapter import OpenAITTSAdapter
        return OpenAITTSAdapter()
    return DemoTTSAdapter()


def get_provider_status() -> dict:
    return {
        "llm": {
            "provider": "openai" if settings.has_llm else "demo",
            "model": settings.OPENAI_LLM_MODEL if settings.has_llm else "local-demo",
            "configured": settings.has_llm,
        },
        "image": {
            "provider": "openai-dalle" if settings.OPENAI_API_KEY else ("stability" if settings.STABILITY_API_KEY else "demo"),
            "configured": settings.has_image_gen,
        },
        "tts": {
            "provider": "openai" if settings.OPENAI_API_KEY else ("elevenlabs" if settings.ELEVENLABS_API_KEY else "demo"),
            "configured": settings.has_tts,
        },
        "qoneqt_api": {
            "configured": settings.has_qoneqt_api,
            "manual_workflow": not settings.has_qoneqt_api,
        },
        "demo_mode": settings.demo_mode,
    }
