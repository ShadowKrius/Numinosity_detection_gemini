import argparse
import json
import time
import pathlib
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()


FASHION_PROMPT = """
You are a fashion expert specialising in Indian and global fashion. Watch this video and identify every distinct fashion item worn by people on screen.

For each unique item return a JSON object with these fields:
- "item_id": sequential integer starting at 1
- "person": string describing the person (e.g. "woman in foreground", "man on left")
- "item_type": garment category. Use Indian-specific terms where appropriate: "saree", "kurta", "kurti", "lehenga", "anarkali", "salwar suit", "sherwani", "dhoti", "dupatta" — not generic Western equivalents like "dress" or "skirt"
- "item_subtype": more specific type (e.g. "wrap midi dress", "silk saree", "straight-leg jeans")
- "colors": array of color strings, primary first. Be specific — "cobalt blue" not "blue"
- "pattern": exactly one of: "solid", "striped", "plaid", "floral", "geometric", "animal print", "logo", "abstract", "other"
- "material_guess": ONE primary inferred material (e.g. "chiffon", "georgette", "denim"). Never two.
- "style_tags": array of style descriptors (e.g. ["ethnic", "bridal", "festive"] or ["casual", "streetwear"])
- "fit": exactly one of: "slim", "regular", "oversized", "fitted", "flowy", "tailored"
- "brand_visible": ONE brand name if clearly visible, otherwise null
- "description": 1-2 sentences a shopper could use to find this item. No double-quote characters inside.
- "confidence": float 0.0-1.0

Rules:
- Every string field must be a single string value — never comma-separated values
- Only include items visible for at least 1 second
- Each distinct garment is a separate item (top + bottom = 2 items)
- Include accessories: bags, shoes, jewellery, hats, belts, sunglasses
- Skip items that are blurry, too small, or only partially visible
- Same outfit across multiple scenes = ONE item. Deduplicate aggressively.
- When uncertain if two appearances are the same item, treat them as one

Return ONLY a valid JSON array. No markdown fences, no explanation.
[
  {
    "item_id": 1,
    "person": "woman in foreground",
    "item_type": "saree",
    "item_subtype": "silk saree",
    "colors": ["royal blue", "gold"],
    "pattern": "floral",
    "material_guess": "silk",
    "style_tags": ["ethnic", "festive"],
    "fit": "flowy",
    "brand_visible": null,
    "description": "A royal blue silk saree with gold floral embroidery and a contrast gold border.",
    "confidence": 0.91
  }
]
"""


def upload_video(client: genai.Client, video_path: str) -> str:
    path = pathlib.Path(video_path)
    print(f"Uploading {path.name} ({path.stat().st_size / 1e6:.1f} MB)...")

    with open(video_path, "rb") as f:
        response = client.files.upload(
            file=f,
            config={"mime_type": "video/mp4", "display_name": path.name},
        )

    file_name = response.name
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


def detect_fashion(client: genai.Client, video_uri: str, model: str = "gemini-2.5-flash") -> list[dict]:
    print(f"Running detection with {model}...")

    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_uri(file_uri=video_uri, mime_type="video/mp4"),
            FASHION_PROMPT,
        ],
        config={"temperature": 0.2, "max_output_tokens": 65536},
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--api-key", default=os.getenv("GEMINI_API_KEY", ""))
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument("--output")
    args = parser.parse_args()

    client = genai.Client(api_key=args.api_key)

    t0 = time.time()
    video_uri = upload_video(client, args.video)
    items = detect_fashion(client, video_uri, model=args.model)
    elapsed = time.time() - t0

    from myntra_search import build_myntra_urls
    myntra_urls = build_myntra_urls(items)

    print(f"\n{'='*60}\n  {len(items)} ITEMS DETECTED  ({elapsed:.1f}s)\n{'='*60}")
    for item in items:
        iid = item["item_id"]
        print(f"\n[{iid}] {item['item_type'].upper()} — {item['item_subtype']}")
        print(f"  {item['person']}  |  {', '.join(item['colors'])}  |  {item['confidence']:.0%}")
        print(f"  {item['description']}")
        if iid in myntra_urls:
            print(f"  Myntra → {myntra_urls[iid]['url']}")

    if args.output:
        export = [
            {**item, **({"myntra_url": myntra_urls[item["item_id"]]["url"],
                         "search_query": myntra_urls[item["item_id"]]["query"]}
                        if item["item_id"] in myntra_urls else {})}
            for item in items
        ]
        with open(args.output, "w") as f:
            json.dump(export, f, indent=2)
        print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()