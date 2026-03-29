from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a Bilibili video by URL.",
    )
    parser.add_argument("url", help="Bilibili video URL")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("downloads"),
        help="Directory to save downloaded files (default: downloads)",
    )
    parser.add_argument(
        "--cookie-file",
        type=Path,
        default=None,
        help="Optional cookie file for member-only videos",
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Download audio only",
    )
    parser.add_argument(
        "--proxy",
        default=None,
        help="Optional proxy URL, e.g. http://127.0.0.1:7890",
    )
    return parser.parse_args()


def build_ydl_options(
    output_dir: Path,
    cookie_file: Path | None,
    audio_only: bool,
    proxy: str | None,
) -> dict:
    has_ffmpeg = shutil.which("ffmpeg") is not None
    if audio_only:
        selected_format = "bestaudio/best"
    else:
        # If ffmpeg is unavailable, force single-stream format to avoid merge failure.
        selected_format = "bv*+ba/b" if has_ffmpeg else "b"

    output_dir.mkdir(parents=True, exist_ok=True)
    options: dict = {
        "outtmpl": str(output_dir / "%(title).200B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "merge_output_format": "mp4",
        "format": selected_format,
    }
    if cookie_file:
        options["cookiefile"] = str(cookie_file)
    if proxy:
        options["proxy"] = proxy
    return options


def download_video(
    url: str,
    output_dir: Path,
    cookie_file: Path | None = None,
    audio_only: bool = False,
    proxy: str | None = None,
) -> tuple[str, str]:
    ydl_options = build_ydl_options(
        output_dir=output_dir,
        cookie_file=cookie_file,
        audio_only=audio_only,
        proxy=proxy,
    )
    with YoutubeDL(ydl_options) as ydl:
        info = ydl.extract_info(url, download=True)
    title = str(info.get("title", "Unknown Title"))
    video_id = str(info.get("id", "Unknown ID"))
    return title, video_id


def main() -> int:
    args = parse_args()
    ffmpeg_missing = not args.audio_only and shutil.which("ffmpeg") is None
    if ffmpeg_missing:
        print(
            "Warning: ffmpeg is not installed. Falling back to single-stream video format.",
            file=sys.stderr,
        )
    try:
        title, video_id = download_video(
            url=args.url,
            output_dir=args.output_dir,
            cookie_file=args.cookie_file,
            audio_only=args.audio_only,
            proxy=args.proxy,
        )
    except DownloadError as exc:
        message = str(exc)
        print(f"Download failed: {message}", file=sys.stderr)
        if "Requested format is not available" in message and ffmpeg_missing:
            print(
                "Hint: This video may require separate video+audio streams. Install ffmpeg or use a different video.",
                file=sys.stderr,
            )
        if "premium member" in message.lower() or "cookies" in message.lower():
            print(
                "Hint: This video may require login. Try --cookie-file to provide Bilibili cookies.",
                file=sys.stderr,
            )
        if "SSL: UNEXPECTED_EOF_WHILE_READING" in message:
            print(
                "Hint: Network/TLS connection was interrupted. Retry later or set --proxy.",
                file=sys.stderr,
            )
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    print("Download completed.")
    print(f"Title: {title}")
    print(f"Video ID: {video_id}")
    print(f"Saved to: {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
