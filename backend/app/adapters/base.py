"""
AI Provider Adapters — Provider-agnostic interface for LLM, image generation, and TTS.
Each adapter implements a standard interface so the backend logic is decoupled from providers.
"""
from abc import ABC, abstractmethod
from typing import Optional


class LLMAdapter(ABC):
    @abstractmethod
    async def generate_script(self, topic: str, community: str, style: str,
                               duration: int, language: str) -> dict:
        """Generate a full script with scenes, captions, and metadata."""

    @abstractmethod
    async def regenerate_scene(self, scene_narration: str, topic: str,
                                community: str, style: str) -> dict:
        """Regenerate a single scene's narration and visual prompt."""


class ImageAdapter(ABC):
    @abstractmethod
    async def generate_image(self, prompt: str, style: str,
                              aspect_ratio: str) -> tuple[bytes, str]:
        """Returns (image_bytes, file_extension)."""


class TTSAdapter(ABC):
    @abstractmethod
    async def generate_speech(self, text: str, voice_id: Optional[str] = None,
                               language: str = "en") -> bytes:
        """Returns raw audio bytes (mp3)."""
