# Fashion Detector — MVP

Identify fashion items in video using Gemini's native video understanding.  
No frame extraction. No CV pipeline. ~50 lines of core logic.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
```

Get your key from [aistudio.google.com](https://aistudio.google.com).

### 3. Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501`, upload your MP4, and click **Detect Fashion Items**.

> **Test clip:** A Saiyaara MP4 clip is included in the folder — use that to try it out immediately.

> **Note:** You'll see a `search.py` file in the folder — ignore it for now, product search is still work in progress.

---

## Output

Each detected item returns:

```json
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
```

Results are shown as cards in the UI and can be downloaded as JSON.

---

## Cost

| Model | Cost per 45-min episode |
|---|---|
| gemini-2.0-flash | ~$0.07 |
| gemini-2.5-flash | ~$0.10 |

For short clips (under 3 minutes), cost is well under $0.01.