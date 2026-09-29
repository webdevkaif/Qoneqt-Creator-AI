"""
OpenAI adapter for LLM (GPT-4o), image generation (DALL-E 3), and TTS.
Only instantiated when OPENAI_API_KEY is set.
"""
import json
import httpx
from typing import Optional
from openai import AsyncOpenAI
from app.adapters.base import LLMAdapter, ImageAdapter, TTSAdapter
from app.core.config import settings
from loguru import logger

SCRIPT_SYSTEM_PROMPT = """You are an expert video content creator and scriptwriter for the Qoneqt social platform.
Generate a short video script in JSON format with the following structure:
{
  "hook": "Catchy opening line (1-2 sentences)",
  "scenes": [
    {
      "order": 0,
      "narration": "What the narrator says (concise, engaging)",
      "visual_prompt": "Detailed DALL-E image prompt for this scene",
      "duration": 5.0,
      "caption": "Short on-screen text (max 8 words)"
    }
  ],
  "video_title": "Catchy title for the video",
  "video_description": "2-3 sentence description for posting",
  "hashtags": ["#tag1", "#tag2", "#tag3"]
}

Rules:
- Use community-specific vocabulary and tone
- Keep narration natural and conversational
- Duration per scene should sum to approximately {duration} seconds
- Generate {scene_count} scenes
- Visual prompts should be detailed and specify art style, lighting, composition
- Never present invented facts as verified information
- Tailor tone to the style: {style}
- Language: {language}
- Return ONLY valid JSON, no markdown fences
"""


class OpenAILLMAdapter(LLMAdapter):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_script(self, topic: str, community: str, style: str,
                               duration: int, language: str) -> dict:
        scene_count = max(3, duration // 5)
        prompt = f"Create a {duration}-second {style} video script about: {topic}\nCommunity: {community}\nLanguage: {language}"
        system = SCRIPT_SYSTEM_PROMPT.format(
            duration=duration, scene_count=scene_count, style=style, language=language
        )
        response = await self.client.chat.completions.create(
            model=settings.OPENAI_LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
        )
        raw = response.choices[0].message.content
        return json.loads(raw)

    async def regenerate_scene(self, scene_narration: str, topic: str,
                                community: str, style: str) -> dict:
        prompt = f"""Rewrite this scene for a {style} video about {topic} in the {community} community.
Current narration: {scene_narration}
Return JSON: {{"narration": "...", "visual_prompt": "...", "caption": "..."}}
Return ONLY valid JSON."""
        response = await self.client.chat.completions.create(
            model=settings.OPENAI_LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.9,
        )
        return json.loads(response.choices[0].message.content)


class OpenAIImageAdapter(ImageAdapter):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_image(self, prompt: str, style: str,
                              aspect_ratio: str) -> tuple[bytes, str]:
        size_map = {"9:16": "1024x1792", "16:9": "1792x1024", "1:1": "1024x1024"}
        size = size_map.get(aspect_ratio, "1024x1024")
        full_prompt = f"{prompt}. Style: {style}. High quality, professional."
        response = await self.client.images.generate(
            model=settings.OPENAI_IMAGE_MODEL,
            prompt=full_prompt[:1000],
            size=size,
            quality="standard",
            response_format="b64_json",
            n=1,
        )
        import base64
        img_data = base64.b64decode(response.data[0].b64_json)
        return img_data, "png"


class OpenAITTSAdapter(TTSAdapter):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_speech(self, text: str, voice_id: Optional[str] = None,
                               language: str = "en") -> bytes:
        voice = voice_id or settings.OPENAI_TTS_VOICE
        valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if voice not in valid_voices:
            voice = "alloy"
        response = await self.client.audio.speech.create(
            model=settings.OPENAI_TTS_MODEL,
            voice=voice,
            input=text[:4096],
        )
        return response.content
