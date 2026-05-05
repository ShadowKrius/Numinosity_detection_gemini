# Fashion Detector - MVP

Identify fashion items in video using Gemini's native video understanding and generate Myntra search links.  
No frame extraction. No CV pipeline.

---

## Files

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI — upload video, view results, download JSON |
| `detect.py` | Core detection logic + CLI runner |
| `myntra_search.py` | Builds Myntra search URLs from detected items |

---

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file with 'GEMINI_API_KEY=your_key_here'

Get your key at [aistudio.google.com](https://aistudio.google.com).

---

## Run

**Streamlit app**
```bash
streamlit run app.py
```
Open `http://localhost:8501`, upload an MP4, click **Detect Fashion Items**.

**CLI**
```bash
python detect.py --video clip.mp4 --output results.json
```

> A Saiyaara MP4 test clip is included - use it to try immediately.

---

## Output

Each detected item:

```json
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
  "confidence": 0.91,
  "myntra_url": "https://www.myntra.com/sarees?rawQuery=silk+saree+royal+blue+floral+silk+ethnic",
  "search_query": "silk saree royal blue floral silk ethnic"
}
```