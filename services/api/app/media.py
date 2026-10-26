from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from app.settings import settings

YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}


class MediaError(ValueError):
    pass


def parse_youtube_url(raw_url: str) -> tuple[str, str]:
    """Accept only public single-video YouTube URL forms; never pass arbitrary URLs to yt-dlp."""
    parsed = urlparse(raw_url.strip())
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise MediaError("Use a public HTTPS YouTube video URL.")
    host = (parsed.hostname or "").lower().rstrip(".")
    video_id = ""
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            query = parse_qs(parsed.query)
            video_id = query.get("v", [""])[0]
            if any(key in query for key in ("list", "playlist")):
                raise MediaError("Playlists are not supported; provide one public video URL.")
        elif parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/")[2] if len(parsed.path.split("/")) > 2 else ""
        else:
            raise MediaError("Provide a single YouTube video URL.")
    elif host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
        if parse_qs(parsed.query).get("list"):
            raise MediaError("Playlists are not supported; provide one public video URL.")
    else:
        raise MediaError("Only public YouTube videos are supported.")
    if not YOUTUBE_ID.fullmatch(video_id):
        raise MediaError("The YouTube URL does not contain a valid video ID.")
    return video_id, f"https://www.youtube.com/watch?v={video_id}"


def probe_media(path: Path) -> dict:
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)], check=True, capture_output=True, text=True, timeout=60)
        info = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise MediaError("The file is not a readable video stream.") from exc
    streams = info.get("streams", [])
    if not any(stream.get("codec_type") == "video" for stream in streams):
        raise MediaError("The file must contain a video stream.")
    try:
        duration = float(info.get("format", {}).get("duration", 0))
    except (TypeError, ValueError):
        duration = 0
    if not 0 < duration <= settings.max_video_duration_seconds:
        raise MediaError(f"Video duration must be between a few seconds and {settings.max_video_duration_seconds // 3600} hours.")
    return {"duration_ms": round(duration * 1000), "streams": streams, "format": info.get("format", {})}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_audio(video_path: Path, audio_path: Path) -> None:
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-i", str(video_path), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio_path)], check=True, capture_output=True, timeout=3600)


def make_video_chunk(video_path: Path, output_path: Path, start_ms: int, duration_ms: int) -> None:
    # Low-resolution, silent visual samples limit transfer size and avoid re-sending audio.
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-ss", f"{start_ms / 1000:.3f}", "-i", str(video_path), "-t", f"{duration_ms / 1000:.3f}", "-vf", "fps=1/10,scale=720:-2", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-movflags", "+faststart", str(output_path)], check=True, capture_output=True, timeout=900)

