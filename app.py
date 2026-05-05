import streamlit as st
import json
import time
import tempfile
import pathlib
from dotenv import load_dotenv
import os

from myntra_search import build_myntra_urls

load_dotenv()

st.set_page_config(page_title="Fashion Detector", page_icon="✦", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif !important;
  background: #0d0d0d !important;
  color: #f0f0f0 !important;
}

[data-testid="stSidebar"],
[data-testid="collapsedControl"] { display: none !important; }

.block-container { padding: 3rem 1.5rem 4rem !important; max-width: 760px !important; }

/* upload widget */
[data-testid="stFileUploaderDropzone"] {
  background: #161616 !important;
  border: 1px solid #2a2a2a !important;
  border-radius: 10px !important;
}
[data-testid="stFileUploader"] > label { display: none !important; }

/* detect button */
.stButton > button[kind="primary"] {
  background: #f0f0f0 !important;
  color: #0d0d0d !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  padding: 12px 28px !important;
  width: 100% !important;
  letter-spacing: 0 !important;
  text-transform: none !important;
}
.stButton > button[kind="primary"]:hover { background: #ffffff !important; }

/* item tile */
.item-tile {
  background: #161616;
  border: 1px solid #222;
  border-radius: 10px;
  padding: 18px 20px;
  margin-bottom: 10px;
}
.item-type {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: #666;
  margin-bottom: 4px;
}
.item-name {
  font-size: 16px;
  font-weight: 600;
  color: #f0f0f0;
  margin-bottom: 4px;
}
.item-desc {
  font-size: 13px;
  color: #888;
  line-height: 1.55;
  margin-bottom: 12px;
}
.tags-wrap { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 12px; }
.tag {
  font-size: 11px;
  padding: 3px 9px;
  background: #1e1e1e;
  border: 1px solid #2a2a2a;
  border-radius: 5px;
  color: #888;
}
.btn-myntra {
  display: inline-block;
  background: #ff3f6c;
  color: #fff !important;
  text-decoration: none !important;
  font-size: 12px;
  font-weight: 600;
  padding: 7px 16px;
  border-radius: 6px;
}

/* download button */
.stDownloadButton > button {
  background: #161616 !important;
  border: 1px solid #2a2a2a !important;
  color: #888 !important;
  border-radius: 8px !important;
  font-size: 13px !important;
  font-weight: 500 !important;
}
.stDownloadButton > button:hover { border-color: #444 !important; color: #f0f0f0 !important; }

/* status box */
[data-testid="stStatusWidget"] { background: #161616 !important; border-radius: 10px !important; }

.stAlert { background: #161616 !important; border: 1px solid #2a2a2a !important; border-radius: 8px !important; }

/* hide top Streamlit chrome */
#MainMenu, header, footer { visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)

API_KEY = os.getenv("GEMINI_API_KEY", "")
MODEL   = "gemini-2.5-flash"

st.markdown("### Fashion Detector")
st.markdown("<p style='color:#666;font-size:13px;margin-top:-8px;margin-bottom:24px'>Upload a video to detect items and generate Myntra links.</p>", unsafe_allow_html=True)

uploaded = st.file_uploader("Upload video", type=["mp4", "mov", "avi", "mkv"], label_visibility="collapsed")

if not uploaded:
    st.stop()

if not API_KEY:
    st.error("GEMINI_API_KEY not set in .env")
    st.stop()

st.video(uploaded)
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
run = st.button("Detect Fashion Items", type="primary", use_container_width=True)

if not run:
    st.stop()

with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
    tmp.write(uploaded.read())
    tmp_path = tmp.name

try:
    from google import genai
    from google.genai import types
    from detect import FASHION_PROMPT

    client = genai.Client(api_key=API_KEY)

    with st.status("Analysing video...", expanded=True) as status:
        st.write("Uploading to Gemini...")
        with open(tmp_path, "rb") as f:
            file_resp = client.files.upload(
                file=f,
                config={"mime_type": "video/mp4", "display_name": uploaded.name},
            )
        file_name = file_resp.name

        st.write("Processing...")
        while True:
            info = client.files.get(name=file_name)
            if info.state.name == "ACTIVE":
                break
            elif info.state.name == "FAILED":
                st.error("Video processing failed.")
                st.stop()
            time.sleep(2)

        st.write(f"Detecting fashion items...")
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_uri(file_uri=info.uri, mime_type="video/mp4"),
                FASHION_PROMPT,
            ],
            config={"temperature": 0.2, "max_output_tokens": 65536},
        )

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            items = json.loads(raw.strip())
        except json.JSONDecodeError:
            last = raw.rfind("},")
            items = json.loads(raw[:last + 1] + "\n]") if last != -1 else (_ for _ in ()).throw(ValueError("bad JSON"))

        myntra_urls = build_myntra_urls(items, min_confidence=0.6)
        status.update(label=f"Done — {len(items)} items found", state="complete")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    for item in items:
        iid  = item["item_id"]
        tags = (
            item.get("colors", []) +
            ([item.get("pattern")] if item.get("pattern") and item["pattern"] not in ("solid","n/a") else []) +
            ([item.get("material_guess")] if item.get("material_guess") and item["material_guess"] not in ("n/a","") else []) +
            item.get("style_tags", [])
        )
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in tags if t)

        st.markdown(f"""
<div class="item-tile">
  <div class="item-type">{item["item_type"]}</div>
  <div class="item-name">{item["item_subtype"].title()}</div>
  <div class="item-desc">{item.get("description", "")}</div>
  <div class="tags-wrap">{tags_html}</div>
  {"" if iid not in myntra_urls else f'<a class="btn-myntra" href="{myntra_urls[iid]["url"]}" target="_blank">Shop on Myntra →</a>'}
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    export = [
        {**item, **({"myntra_url": myntra_urls[item["item_id"]]["url"],
                     "search_query": myntra_urls[item["item_id"]]["query"]}
                    if item["item_id"] in myntra_urls else {})}
        for item in items
    ]
    st.download_button(
        "Download JSON",
        data=json.dumps(export, indent=2),
        file_name=f"fashion_{pathlib.Path(uploaded.name).stem}.json",
        mime="application/json",
    )

except Exception as e:
    st.error(f"Error: {e}")
finally:
    os.unlink(tmp_path)