"""
fashion_detector/detect.py
Core fashion detection using Gemini native video input.
Usage: python detect.py --video path/to/video.mp4 --api-key YOUR_KEY
"""

import argparse
import json
import time
import pathlib
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()


FASHION_PROMPT = """
You are a fashion expert and visual analyst. Watch this video carefully and identify every distinct fashion item worn by people on screen.

For each unique fashion item you detect, return a JSON object with these fields:
- "item_id": sequential integer starting at 1
- "person": single string describing the person wearing it (e.g. "woman in foreground", "man on left")
- "item_type": single string garment category (e.g. "dress", "blazer", "jeans", "sneakers", "handbag", "necklace", "watch")
- "item_subtype": single string, more specific type (e.g. "midi dress", "oversized blazer", "straight-leg jeans")
- "colors": JSON array of color strings, primary color first (e.g. ["burgundy", "cream"]). Be specific — "cobalt blue" not "blue"
- "pattern": exactly one of these strings: "solid", "striped", "plaid", "floral", "geometric", "animal print", "logo", "abstract", "other"
- "material_guess": single string only, the ONE primary inferred material (e.g. "chiffon"). Never output two materials.
- "style_tags": JSON array of style descriptor strings (e.g. ["casual", "streetwear"])
- "fit": exactly one of these strings: "slim", "regular", "oversized", "fitted", "flowy", "tailored"
- "brand_visible": single string with ONE brand name if clearly visible, otherwise JSON null. Never list multiple brands.
- "description": single string, 1-2 sentences a shopper could use to find this item. Do not use double-quote characters inside this string.
- "confidence": float between 0.0 and 1.0

Important rules:
- Every field that is a string must be ONE string value — never output two comma-separated values for a single string field
- Only include items clearly visible for at least 1 second
- Treat each distinct garment as a separate item (top and bottom = 2 items)
- Include accessories: bags, shoes, jewelry, hats, belts, sunglasses
- Skip items that are too blurry, too small, or only partially visible
- If the same person appears multiple times in different outfits, list each outfit's items separately
- This is the full video — a person wearing the same outfit across multiple scenes is ONE item, not multiple. Deduplicate aggressively.
- If you are uncertain whether two appearances are the same item, treat them as one. Err on the side of fewer items, not more.
- Do not list the same garment twice just because it appears in different shots or scenes.

Return ONLY a valid JSON array. No markdown fences, no explanation, no text before or after the array.
[
  {
    "item_id": 1,
    "person": "woman in foreground",
    "item_type": "dress",
    "item_subtype": "wrap midi dress",
    "colors": ["forest green", "cream"],
    "pattern": "floral",
    "material_guess": "chiffon",
    "style_tags": ["feminine", "boho", "spring"],
    "fit": "flowy",
    "brand_visible": null,
    "description": "A flowy forest green and cream floral wrap midi dress with a V-neckline and long sleeves.",
    "confidence": 0.91
  }
]
"""


def upload_video(client: genai.Client, video_path: str) -> str:
    """Upload video to Gemini Files API, return file URI."""
    path = pathlib.Path(video_path)
    print(f"Uploading {path.name} ({path.stat().st_size / 1e6:.1f} MB)...")

    with open(video_path, "rb") as f:
        response = client.files.upload(
            file=f,
            config={"mime_type": "video/mp4", "display_name": path.name},
        )

    file_name = response.name
    print(f"Upload complete. File: {file_name}")
    print("Waiting for processing", end="", flush=True)

    while True:
        file_info = client.files.get(name=file_name)
        if file_info.state.name == "ACTIVE":
            print(" done.")
            break
        elif file_info.state.name == "FAILED":
            raise RuntimeError(f"File processing failed: {file_info.name}")
        print(".", end="", flush=True)
        time.sleep(3)

    return file_info.uri


def detect_fashion(client: genai.Client, video_uri: str, model: str = "gemini-2.0-flash") -> list[dict]:
    """Run fashion detection on uploaded video."""
    print(f"Running detection with {model}...")

    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_uri(file_uri=video_uri, mime_type="video/mp4"),
            FASHION_PROMPT,
        ],
        config={"temperature": 0.2, "max_output_tokens": 8192},
    )

    raw = response.text.strip()
    # Strip markdown code blocks if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    items = json.loads(raw)
    return items


def format_results(items: list[dict]) -> str:
    lines = [f"\n{'='*60}", f"  DETECTED {len(items)} FASHION ITEMS", f"{'='*60}"]
    for item in items:
        ts = f"{item['timestamp_first_seen']:.1f}s – {item['timestamp_last_seen']:.1f}s"
        lines.append(f"\n[{item['item_id']}] {item['item_type'].upper()} — {ts}")
        lines.append(f"  Person:      {item['person']}")
        lines.append(f"  Subtype:     {item['item_subtype']}")
        lines.append(f"  Colors:      {', '.join(item['colors'])}")
        lines.append(f"  Pattern:     {item['pattern']}  |  Fit: {item['fit']}")
        lines.append(f"  Material:    {item['material_guess']}")
        lines.append(f"  Style:       {', '.join(item['style_tags'])}")
        if item.get("brand_visible"):
            lines.append(f"  Brand:       {item['brand_visible']}")
        lines.append(f"  Description: {item['description']}")
        lines.append(f"  Confidence:  {item['confidence']:.0%}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Fashion item detector for video files")
    parser.add_argument("--video", required=True, help="Path to MP4 file")
    parser.add_argument("--api-key", default=os.getenv("GEMINI_API_KEY", ""), help="Google Gemini API key")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model to use")
    parser.add_argument("--output", help="Optional: save JSON results to this file")
    args = parser.parse_args()

    client = genai.Client(api_key=args.api_key)

    t0 = time.time()
    video_uri = upload_video(client, args.video)
    items = detect_fashion(client, video_uri, model=args.model)
    elapsed = time.time() - t0

    print(format_results(items))
    print(f"\nTotal time: {elapsed:.1f}s")
    print(f"Items detected: {len(items)}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(items, f, indent=2)
        print(f"Results saved to {args.output}")

    return items


if __name__ == "__main__":
    main()