# Fashion Detector — MVP

Identify fashion items in video using Gemini's native video understanding.  
No frame extraction. No CV pipeline. ~50 lines of core logic.

## Setup

```bash
pip install -r requirements.txt
```

You need a **Gemini API key** from [aistudio.google.com](https://aistudio.google.com).

---

## Option A: Streamlit UI (recommended for demos)

```bash
streamlit run app.py
```

Open `http://localhost:8501`, enter your API key, upload your MP4, click detect.

---

## Option B: CLI script

```bash
python detect.py \
  --video path/to/your/video.mp4 \
  --api-key YOUR_GEMINI_API_KEY \
  --output results.json
```

Optional flags:
- `--model gemini-2.5-flash-preview-04-17` — use a more capable model
- `--output results.json` — save JSON to file

---

## Output schema

Each detected item returns:

```json
{
  "item_id": 1,
  "timestamp_first_seen": 12.5,
  "timestamp_last_seen": 47.2,
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
```

---

## Cost estimates

| Model | Cost per 45-min episode |
|---|---|
| gemini-2.0-flash | ~$0.07 |
| gemini-2.5-flash | ~$0.21 |
| gemini-1.5-pro | ~$1.30 |

---

## Next steps (Step 2 — product matching)

Once you have the JSON output from Step 1, the next step is to:

1. Take the `description` + `colors` + `item_type` from each detected item
2. Query a product catalog using:
   - **Google Shopping API** / **Serp API Google Shopping** for broad matching
   - **Pinterest API** for visual inspiration
   - **Marqo-FashionCLIP** for embedding-based similarity search against a product database
3. Rank results by visual + attribute similarity
4. Surface top 5-10 purchasable items per detected garment
