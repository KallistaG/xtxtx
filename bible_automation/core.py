from __future__ import annotations

import json
import os
import random
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Verse:
    reference: str
    text: str


def choose_verse(path: Path | None = None) -> Verse:
    source = path or ROOT / "bible_automation" / "verses.json"
    entries = json.loads(source.read_text(encoding="utf-8"))
    if not entries:
        raise ValueError(f"No verses found in {source}")
    item = random.choice(entries)
    return Verse(reference=item["reference"], text=item["text"])


def make_caption(verse: Verse) -> str:
    return f'“{verse.text}”\n— {verse.reference} (KJV)\n\nMay this word encourage you today. #BibleVerse #Faith #Hope'


def generate_image(verse: Verse, output_path: Path) -> Path:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required. Add it to .env (see .env.example).")

    model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    prompt = (
        "Create a polished, reverent Facebook Bible verse poster, square 1:1 composition. "
        "Beautiful cinematic sunrise over a peaceful landscape, soft natural light, elegant "
        "subtle botanical details, warm cream and muted gold palette, uncluttered premium design. "
        "Set the following exact text prominently and legibly, with the reference beneath it. "
        "Do not add any other text, logos, watermarks, or invented words.\n"
        f'Verse: “{verse.text}”\nReference: {verse.reference} (KJV)'
    )
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.data:
            output_path.write_bytes(part.inline_data.data)
            return output_path
    raise RuntimeError("Image model returned no image. Check model access/quota and try again.")


def publish_to_facebook(image_path: Path, caption: str) -> str:
    load_dotenv()
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    version = os.getenv("FACEBOOK_GRAPH_VERSION", "v23.0")
    if not page_id or not token:
        raise RuntimeError("Set FACEBOOK_PAGE_ID and FACEBOOK_PAGE_ACCESS_TOKEN in .env.")
    if not image_path.is_file():
        raise FileNotFoundError(image_path)

    endpoint = f"https://graph.facebook.com/{version}/{page_id}/photos"
    with image_path.open("rb") as photo:
        response = requests.post(
            endpoint,
            data={"caption": caption, "access_token": token},
            files={"source": (image_path.name, photo, "image/png")},
            timeout=90,
        )
    if not response.ok:
        # Avoid including the token in error output.
        try:
            detail = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            detail = response.text
        raise RuntimeError(f"Facebook Graph API error ({response.status_code}): {detail}")
    return str(response.json().get("post_id") or response.json().get("id", "unknown"))


def create_post(output_dir: Path, should_publish: bool = False, image_provider: str = "gemini") -> tuple[Verse, Path, str | None]:
    verse = choose_verse()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_ref = re.sub(r"[^a-zA-Z0-9]+", "-", verse.reference).strip("-").lower()
    image_path = output_dir / f"{stamp}-{safe_ref}.png"
    if image_provider == "flow":
        from .flow_browser import create_with_flow
        create_with_flow(verse, image_path)
        if not image_path.is_file():
            raise RuntimeError(f"Flow image was not saved to {image_path}. Save/download it from the open browser and retry.")
    elif image_provider == "gemini":
        generate_image(verse, image_path)
    else:
        raise ValueError(f"Unknown image provider: {image_provider}")
    (image_path.with_suffix(".txt")).write_text(make_caption(verse), encoding="utf-8")
    post_id = publish_to_facebook(image_path, make_caption(verse)) if should_publish else None
    return verse, image_path, post_id
