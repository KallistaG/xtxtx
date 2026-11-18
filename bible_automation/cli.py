from __future__ import annotations

import argparse
import os
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

from .core import create_post


def _output_dir() -> Path:
    return Path(os.getenv("OUTPUT_DIR", "output"))


def _run(publish: bool, image_provider: str = "gemini") -> None:
    verse, image_path, post_id = create_post(_output_dir(), should_publish=publish, image_provider=image_provider)
    print(f"Verse: {verse.reference} (KJV)\n{verse.text}\nImage: {image_path}")
    if post_id:
        print(f"Published successfully. Facebook post ID: {post_id}")
    elif publish:
        print("Publish requested but no post ID was returned.")
    else:
        print("Preview only; nothing was published. Review the image and caption.")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Create Bible verse graphics for a Facebook Page.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create", help="Generate one verse graphic")
    create.add_argument("--post", action="store_true", help="Publish to the configured Page")
    create.add_argument("--image-provider", choices=["flow", "gemini"], default="gemini", help="Generate using the visible Flow browser or Gemini API")
    subparsers.add_parser("schedule", help="Generate a daily post (publishing is opt-in)")
    args = parser.parse_args()

    if args.command == "create":
        _run(args.post, args.image_provider)
        return

    time_text = os.getenv("POST_TIME", "09:00")
    try:
        hour, minute = (int(part) for part in time_text.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError as exc:
        raise SystemExit("POST_TIME must be HH:MM, for example 09:00") from exc
    timezone_name = os.getenv("TIMEZONE", "UTC")
    auto_post = os.getenv("ENABLE_AUTO_POST", "false").lower() in {"true", "1", "yes"}
    scheduler = BlockingScheduler(timezone=timezone_name)
    scheduler.add_job(lambda: _run(auto_post), "cron", hour=hour, minute=minute)
    mode = "PUBLISHING" if auto_post else "DRY-RUN"
    print(f"Daily schedule active at {time_text} ({timezone_name}); mode: {mode}. Press Ctrl+C to stop.")
    scheduler.start()


if __name__ == "__main__":
    main()
