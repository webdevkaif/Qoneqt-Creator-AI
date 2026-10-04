#!/usr/bin/env python3
"""
Assembles an explanation video for the Qoneqt Creator AI project
using pre-generated slides + edge-tts narration + FFmpeg.
"""
import asyncio
import subprocess
import tempfile
import os
import sys

# Add backend to path to use existing modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Bundled FFmpeg binary (installed via imageio-ffmpeg)
FFMPEG = "/Users/mohammadkaif/control freak/qoneqt-creator-ai/backend/venv/lib/python3.9/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"

SLIDES = [
    {
        "image": "/Users/mohammadkaif/.gemini/antigravity-ide/brain/7043629d-1e76-427a-af4e-c474294a1e3d/slide_hero_1791077266593.jpg",
        "narration": "Welcome to Qoneqt Creator AI — a powerful, LLM-powered content creation platform. With just a topic or idea, this application automatically generates a complete, professional video ready for the Qoneqt Global Feed.",
        "duration": 9,
    },
    {
        "image": "/Users/mohammadkaif/.gemini/antigravity-ide/brain/7043629d-1e76-427a-af4e-c474294a1e3d/slide_pipeline_1791077289441.jpg",
        "narration": "The AI generation pipeline works in seven intelligent stages. First, you provide a topic or prompt. The system then generates a structured script using a Large Language Model, builds a storyboard, creates AI visuals for each scene, synthesizes a voice narration, and finally assembles everything into a polished MP4 video using FFmpeg.",
        "duration": 14,
    },
    {
        "image": "/Users/mohammadkaif/.gemini/antigravity-ide/brain/7043629d-1e76-427a-af4e-c474294a1e3d/slide_techstack_1791077314225.jpg",
        "narration": "The project is built on a modern, production-ready tech stack. The frontend uses Next.js for a fast, responsive UI. The backend is powered by FastAPI with Python. MongoDB stores all project data. Background video processing runs via Celery task queues, while FFmpeg handles video rendering. OpenAI provides the AI intelligence, and edge-tts delivers high-quality, free voice synthesis — all working together seamlessly.",
        "duration": 16,
    },
]

VOICE = "en-US-AriaNeural"
OUTPUT_VIDEO = "/Users/mohammadkaif/control freak/qoneqt-creator-ai/qoneqt_explanation_video.mp4"


async def generate_audio(text: str, voice: str, output_path: str):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


def create_slide_video(image_path: str, audio_path: str, duration: float, output_path: str):
    """Create a video from a still image + audio using FFmpeg."""
    cmd = [
        FFMPEG, "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,"
               "fade=t=in:st=0:d=0.5,fade=t=out:st={}:d=0.5".format(max(duration - 0.5, 0.1)),
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr[-500:]}")
        raise RuntimeError(f"FFmpeg failed for {image_path}")
    print(f"  ✓ Slide video created: {output_path}")


def concatenate_videos(clip_paths: list, output_path: str):
    """Concatenate multiple video clips into one."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for path in clip_paths:
            f.write(f"file '{path}'\n")
        concat_list = f.name

    cmd = [
        FFMPEG, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(concat_list)
    if result.returncode != 0:
        print(f"Concat error: {result.stderr[-500:]}")
        raise RuntimeError("Video concatenation failed")
    print(f"  ✓ Final video assembled: {output_path}")


async def main():
    print("🎬 Qoneqt Creator AI — Explanation Video Generator")
    print("=" * 55)

    tmp_dir = tempfile.mkdtemp(prefix="qoneqt_explainer_")
    clip_paths = []

    for i, slide in enumerate(SLIDES):
        print(f"\n📍 Processing slide {i+1}/{len(SLIDES)}...")

        # 1. Generate TTS audio
        audio_path = os.path.join(tmp_dir, f"slide_{i}_audio.mp3")
        print(f"  🔊 Generating narration...")
        await generate_audio(slide["narration"], VOICE, audio_path)
        print(f"  ✓ Audio ready")

        # 2. Create slide video
        clip_path = os.path.join(tmp_dir, f"slide_{i}_clip.mp4")
        print(f"  🖼️  Assembling slide video...")
        create_slide_video(slide["image"], audio_path, slide["duration"], clip_path)
        clip_paths.append(clip_path)

    # 3. Concatenate all clips
    print(f"\n🔗 Concatenating {len(clip_paths)} clips...")
    concatenate_videos(clip_paths, OUTPUT_VIDEO)

    # 4. Cleanup temp files
    for f in os.listdir(tmp_dir):
        os.unlink(os.path.join(tmp_dir, f))
    os.rmdir(tmp_dir)

    print(f"\n✅ DONE! Explanation video saved to:")
    print(f"   {OUTPUT_VIDEO}")

    # Get file size
    size_mb = os.path.getsize(OUTPUT_VIDEO) / (1024 * 1024)
    print(f"   Size: {size_mb:.1f} MB")


if __name__ == "__main__":
    asyncio.run(main())
