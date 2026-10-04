import edge_tts
from pathlib import Path
import os
from loguru import logger

async def generate_speech(text: str, voice: str, output_path: str) -> str:
    """
    Generates TTS using edge-tts.
    Common voices:
    - en-US-AriaNeural (Female)
    - en-US-GuyNeural (Male)
    - en-GB-SoniaNeural (Female)
    - en-GB-RyanNeural (Male)
    """
    logger.info(f"Generating voice for text: '{text[:20]}...' with voice: {voice}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    
    logger.info(f"Audio saved to {output_path}")
    return output_path
