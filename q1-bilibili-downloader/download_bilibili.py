from __future__ import annotations

import argparse
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
    output_dir.mkdir(parents=True, exist_ok=True)
    options: dict = {
        "outtmpl": str(output_dir / "%(title).200B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "merge_output_format": "mp4",
        "format": "bestaudio/best" if audio_only else "bv*+ba/b",
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
    try:
        title, video_id = download_video(
            url=args.url,
            output_dir=args.output_dir,
            cookie_file=args.cookie_file,
            audio_only=args.audio_only,
            proxy=args.proxy,
        )
    except DownloadError as exc:
        print(f"Download failed: {exc}", file=sys.stderr)
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
