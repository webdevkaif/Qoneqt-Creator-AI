"""
Demo mode adapter — returns pre-built, locally generated sample data.
Used when no real AI provider API keys are configured.
All responses are clearly marked as demo data.
"""
import json
import struct
import wave
import io
from typing import Optional
from app.adapters.base import LLMAdapter, ImageAdapter, TTSAdapter

DEMO_SCRIPT_TEMPLATE = {
    "is_demo": True,
    "demo_notice": "⚠️ DEMO MODE: This content was generated locally without an AI API key. Configure OPENAI_API_KEY in .env for real AI generation.",
    "hook": "🚀 {topic} is revolutionizing the way we think about the future!",
    "scenes": [
        {
            "order": 0,
            "narration": "Welcome to this exploration of {topic}. In the next {duration} seconds, we'll cover the most important aspects.",
            "visual_prompt": "Dynamic illustration of {topic} with modern design elements, vibrant colors, professional look",
            "duration": 5.0,
            "caption": "Welcome to {topic}"
        },
        {
            "order": 1,
            "narration": "{topic} has been transforming the {community} community in remarkable ways. Here's what you need to know.",
            "visual_prompt": "People engaging with {topic} in a {community} setting, collaborative environment",
            "duration": 5.0,
            "caption": "The Impact of {topic}"
        },
        {
            "order": 2,
            "narration": "The key benefits include improved efficiency, broader accessibility, and real-world applications that matter.",
            "visual_prompt": "Infographic showing key benefits and statistics about {topic}, clean minimal design",
            "duration": 5.0,
            "caption": "Key Benefits"
        },
        {
            "order": 3,
            "narration": "Whether you're a beginner or an expert, {topic} offers something valuable for everyone in the {community} space.",
            "visual_prompt": "Diverse group of people at different skill levels learning about {topic}",
            "duration": 5.0,
            "caption": "For Everyone"
        },
        {
            "order": 4,
            "narration": "The future of {topic} looks bright. Stay ahead of the curve and join the conversation today!",
            "visual_prompt": "Futuristic visualization of {topic}'s potential, inspiring and forward-looking imagery",
            "duration": 5.0,
            "caption": "The Future is Now"
        },
        {
            "order": 5,
            "narration": "Follow for more {community} insights and don't forget to share this with someone who needs to see it!",
            "visual_prompt": "Call to action screen with follow/share buttons, engaging end card design",
            "duration": 5.0,
            "caption": "Follow for More!"
        },
    ]
}


class DemoLLMAdapter(LLMAdapter):
    async def generate_script(self, topic: str, community: str, style: str,
                               duration: int, language: str) -> dict:
        scene_count = max(3, duration // 5)
        scenes = []
        base = DEMO_SCRIPT_TEMPLATE["scenes"]
        for i in range(scene_count):
            scene = dict(base[i % len(base)])
            scene["order"] = i
            scene["narration"] = scene["narration"].format(
                topic=topic, community=community, duration=duration
            )
            scene["visual_prompt"] = scene["visual_prompt"].format(
                topic=topic, community=community
            )
            scene["caption"] = scene["caption"].format(topic=topic)
            scene["duration"] = round(duration / scene_count, 1)
            scenes.append(scene)

        hashtags = [
            f"#{topic.replace(' ', '')}",
            f"#{community}",
            "#QoneqtCreator",
            "#VideoAI",
            "#ShortVideo",
        ]
        return {
            "is_demo": True,
            "demo_notice": DEMO_SCRIPT_TEMPLATE["demo_notice"],
            "hook": DEMO_SCRIPT_TEMPLATE["hook"].format(topic=topic),
            "scenes": scenes,
            "video_title": f"Everything You Need to Know About {topic}",
            "video_description": f"An in-depth look at {topic} for the {community} community. Created with Qoneqt Creator AI.",
            "hashtags": hashtags,
            "language": language,
            "estimated_duration": duration,
        }

    async def regenerate_scene(self, scene_narration: str, topic: str,
                                community: str, style: str) -> dict:
        return {
            "is_demo": True,
            "narration": f"[DEMO] {topic} is fascinating in the context of {community}. Here's what stands out most.",
            "visual_prompt": f"Professional illustration of {topic} in {community} context, vibrant and engaging",
            "caption": f"About {topic}",
        }


class DemoImageAdapter(ImageAdapter):
    """Returns a simple colored placeholder PNG image without any external calls."""

    async def generate_image(self, prompt: str, style: str, aspect_ratio: str) -> tuple[bytes, str]:
        # Generate a minimal valid PNG (1x1 dark blue pixel) as placeholder
        # Real implementation would call DALL-E or Stability AI
        import base64
        # 100x56 dark blue PNG (hardcoded minimal valid PNG)
        # This is a real PNG header + IDAT chunk for a solid color image
        png_1x1_dark_blue = (
            b'\x89PNG\r\n\x1a\n'  # PNG signature
            b'\x00\x00\x00\rIHDR'  # IHDR chunk length + type
            b'\x00\x00\x00\x01'    # width: 1
            b'\x00\x00\x00\x01'    # height: 1
            b'\x08\x02'            # bit depth 8, color type RGB
            b'\x00\x00\x00'        # compression, filter, interlace
            b'\x90wS\xde'          # CRC
            b'\x00\x00\x00\x0cIDATx\x9cc\xf8\x1f\x00\x01\x01\x00\x05\x18\xd8N'  # IDAT
            b'\x00\x00\x00\x00IEND\xaeB`\x82'  # IEND
        )
        return png_1x1_dark_blue, "png"


class DemoTTSAdapter(TTSAdapter):
    """Returns a minimal valid silent WAV file — no external API calls needed."""

    async def generate_speech(self, text: str, voice_id: Optional[str] = None,
                               language: str = "en") -> bytes:
        # Generate a short silent WAV (0.5s, 16-bit, 22050 Hz, mono)
        sample_rate = 22050
        duration_ms = 500
        num_samples = int(sample_rate * duration_ms / 1000)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(b'\x00\x00' * num_samples)
        return buf.getvalue()
