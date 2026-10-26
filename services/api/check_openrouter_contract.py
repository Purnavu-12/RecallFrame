"""Explicitly test the configured provider's video + JSON Schema contract."""
import argparse
from pathlib import Path

from app.inference import OpenRouterClient
from app.media import probe_media
from app.settings import settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clip", type=Path, help="A short, non-sensitive clip you have permission to send")
    args = parser.parse_args()
    if not settings.openrouter_api_key:
        parser.error("OPENROUTER_API_KEY is not configured in the local environment.")
    if not args.clip.is_file() or args.clip.suffix.lower() not in {".mp4", ".mov", ".webm"}:
        parser.error("Provide a readable MP4, MOV, or WebM clip.")
    try:
        duration_ms = probe_media(args.clip)["duration_ms"]
    except ValueError as exc:
        parser.error(str(exc))
    if duration_ms > 15_000:
        parser.error("Use a clip no longer than 15 seconds for the contract check.")
    print("This sends the selected clip to NVIDIA through OpenRouter's free endpoint.")
    print("Do not send personal or confidential content; NVIDIA may log submissions for service improvement.")
    if input("Type SEND to continue: ").strip() != "SEND":
        raise SystemExit("Contract check cancelled.")
    mime = {".mp4": "data:video/mp4", ".mov": "data:video/mov", ".webm": "data:video/webm"}[args.clip.suffix.lower()]
    response = OpenRouterClient().analyze_video_chunk(
        str(args.clip), mime, [], 15_000, frame_prefix="contract_check"
    )
    required = {"chapters", "takeaways", "visual_notes", "concepts"}
    if not required <= response.keys() or not all(isinstance(response[key], list) for key in required):
        raise SystemExit("The provider returned a response outside the expected structured schema.")
    print(f"Video + JSON Schema contract verified for {settings.openrouter_model}.")


if __name__ == "__main__":
    main()
