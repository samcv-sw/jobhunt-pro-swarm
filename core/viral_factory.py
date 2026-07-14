"""
JobHunt Pro - Viral Factory (Instant Hyper-Growth Engine)
Mass generates viral TikTok/Reels videos using AI text-to-speech and dynamic waveforms.
"""

import asyncio
import contextlib
import logging
import os
import time

logger = logging.getLogger(__name__)

# Pre-written highly controversial / viral hooks designed for the TikTok algorithm
VIRAL_SCRIPTS = [
    "HR managers are furious because this AI applies to 500 jobs while you sleep. They can't stop you from doing this. Link in bio.",
    "Stop applying to jobs manually. It's a scam. Use this secret AI bot to auto-apply to 1000 jobs today. Link in bio.",
    "The job market is rigged. Here is how you cheat the system using an AI that passes the ATS filters automatically. Link in bio.",
    "I was unemployed for 6 months until I found this AI agent. It literally does the interviews for you. Link in bio.",
    "If you are manually writing cover letters in 2026, you are losing to robots. Use this AI instead. Link in bio.",
]


class ViralFactory:
    def __init__(self):
        self.output_dir = "cache/viral_videos"
        os.makedirs(self.output_dir, exist_ok=True)
        self.voice = "en-US-ChristopherNeural"  # Professional male voice

    async def _generate_audio(self, text: str, filename: str) -> str:
        """Uses Edge-TTS to generate an MP3 for the script."""
        audio_path = os.path.join(self.output_dir, f"{filename}.mp3")
        cmd = [
            "edge-tts",
            "--voice",
            self.voice,
            "--text",
            text,
            "--write-media",
            audio_path,
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return audio_path if process.returncode == 0 else ""

    async def _generate_video(self, audio_path: str, filename: str) -> str:
        """Uses FFmpeg to attach a viral waveform and background to the audio."""
        video_path = os.path.join(self.output_dir, f"{filename}.mp4")

        # We generate a vertical 1080x1920 video for TikTok/Shorts
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=1080x1920:d=1",  # Vertical black background
            "-i",
            audio_path,
            "-filter_complex",
            "[1:a]showwaves=s=1080x400:mode=cline:colors=0x00FF00[wave];[0:v][wave]overlay=0:(H-h)/2[outv]",
            "-map",
            "[outv]",
            "-map",
            "1:a",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "28",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            video_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return video_path if process.returncode == 0 else ""

    async def create_viral_video(self, script_text: str = None) -> dict:
        """Generates a complete MP4 viral video from text."""
        import random

        text = script_text or random.choice(VIRAL_SCRIPTS)
        filename = f"viral_{int(time.time())}"

        logger.info(
            f"[VIRAL FACTORY] Generating viral audio for script: {text[:30]}..."
        )
        audio_path = await self._generate_audio(text, filename)
        if not audio_path or not os.path.exists(audio_path):
            return {"status": "error", "error": "TTS Failed"}

        logger.info("[VIRAL FACTORY] Stitiching MP4 with FFmpeg...")
        video_path = await self._generate_video(audio_path, filename)

        # Cleanup audio
        with contextlib.suppress(Exception):
            os.remove(audio_path)

        if not video_path or not os.path.exists(video_path):
            return {"status": "error", "error": "FFmpeg Failed"}

        logger.info(f"[VIRAL FACTORY] Viral MP4 created: {video_path}")

        # ── AUTONOMOUS DISTRIBUTION (ZERO-TOUCH) ──
        logger.info("[VIRAL FACTORY] Initiating autonomous Telegram broadcast...")
        try:
            from core.telegram.bot import send_telegram_message_sync

            # In a real environment, we would also upload the video document itself.
            # For now, we simulate the blast by sending the text and a local reference to the channel.
            send_telegram_message_sync(
                f"🚀 *AUTO-VIRAL BLAST*\n\n{text}\n\n*Video rendered and ready to upload from Server:* `{video_path}`"
            )
            logger.info(
                "[VIRAL FACTORY] Successfully broadcasted to Telegram channels!"
            )
        except Exception as e:
            logger.warning(f"[VIRAL FACTORY] Could not auto-blast to Telegram: {e}")

        return {"status": "success", "file": video_path, "script": text}


viral_factory = ViralFactory()
