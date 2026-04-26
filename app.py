"""
fashion_detector/app.py
Streamlit UI for fashion detection.
Run with: streamlit run app.py
"""

import streamlit as st
import json
import time
import tempfile
import pathlib
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(
    page_title="Fashion Detector",
    page_icon="👗",
    layout="wide",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.item-card {
    background: #1a1a2e;
    border: 1px solid #2d2d4a;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
}
.item-header {
    font-size: 17px;
    font-weight: 700;
    color: #e8d5ff;
    margin-bottom: 4px;
}
.item-ts {
    font-size: 12px;
    color: #7a7aaa;
    margin-bottom: 10px;
}
.item-desc {
    font-size: 14px;
    color: #c4c4e0;
    line-height: 1.5;
    margin-bottom: 12px;
}
.tag {
    display: inline-block;
    background: #2d2d4a;
    color: #b8b8dd;
    border-radius: 6px;
    padding: 3px 9px;
    font-size: 12px;
    margin: 2px 3px 2px 0;
}
.color-dot {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 4px;
    vertical-align: middle;
    border: 1px solid rgba(255,255,255,0.2);
}
.conf-bar-bg {
    background: #2d2d4a;
    border-radius: 4px;
    height: 5px;
    width: 100%;
    margin-top: 8px;
}
.conf-bar-fill {
    background: linear-gradient(90deg, #7b5ea7, #c084fc);
    border-radius: 4px;
    height: 5px;
}
.stat-box {
    background: #1a1a2e;
    border: 1px solid #2d2d4a;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
}
.stat-num { font-size: 28px; font-weight: 800; color: #c084fc; }
.stat-label { font-size: 12px; color: #7a7aaa; margin-top: 2px; }
.product-card {
    background: #12122a;
    border: 1px solid #3a2d5a;
    border-radius: 10px;
    padding: 10px;
    text-align: center;
    height: 100%;
}
.product-title {
    font-size: 12px;
    color: #c4c4e0;
    margin: 8px 0 4px 0;
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.product-price { font-size: 15px; font-weight: 700; color: #c084fc; margin: 4px 0; }
.product-retailer { font-size: 11px; color: #7a7aaa; margin-bottom: 8px; }
.shop-btn {
    display: inline-block;
    background: linear-gradient(90deg, #7b5ea7, #c084fc);
    color: white !important;
    text-decoration: none !important;
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 12px;
    font-weight: 600;
}
.query-pill {
    font-size: 11px;
    color: #7a7aaa;
    background: #1a1a2e;
    border: 1px solid #2d2d4a;
    border-radius: 4px;
    padding: 2px 7px;
    display: inline-block;
    margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 👗 Fashion Detector")
st.markdown("Upload a video and get AI-powered fashion item identification with rich attributes.")
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    api_key = os.getenv("GEMINI_API_KEY", "")
    model = st.selectbox(
        "Model",
        ["gemini-2.5-flash", "gemini-2.0-flash-001", "gemini-1.5-pro"],
        help="2.5-flash is most accurate. 2.0-flash-001 is faster and cheaper."
    )
    st.divider()
    st.divider()
    st.markdown("**💡 Tips**")
    st.markdown("- Works best on well-lit scenes\n- Min recommended clip: 5 seconds\n- Max file: 2 GB\n- Processing: ~30-90 seconds")
    st.divider()
    st.markdown("**Pricing estimate**")
    st.markdown("~$0.10 per 45-min episode")

# ── Main ──────────────────────────────────────────────────────────────────────
uploaded = st.file_uploader("Upload MP4 video", type=["mp4", "mov", "avi", "mkv"])

if uploaded and api_key:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.video(uploaded)
    with col2:
        st.markdown(f"**File:** {uploaded.name}")
        st.markdown(f"**Size:** {uploaded.size / 1e6:.1f} MB")
        run = st.button("🔍 Detect Fashion Items", type="primary", use_container_width=True)

    if run:
        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        try:
            from google import genai
            from google.genai import types
            from detect import FASHION_PROMPT

            client = genai.Client(api_key=api_key)

            status = st.status("Processing video...", expanded=True)
            t0 = time.time()

            with status:
                st.write("📤 Uploading to Gemini Files API...")
                with open(tmp_path, "rb") as f:
                    file_resp = client.files.upload(
                        file=f,
                        config={"mime_type": "video/mp4", "display_name": uploaded.name},
                    )
                file_name = file_resp.name

                st.write("⏳ Waiting for video processing...")
                while True:
                    info = client.files.get(name=file_name)
                    if info.state.name == "ACTIVE":
                        break
                    elif info.state.name == "FAILED":
                        st.error("Video processing failed.")
                        st.stop()
                    time.sleep(2)

                st.write(f"🧠 Running {model} fashion analysis...")
                response = client.models.generate_content(
                    model=model,
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
                raw = raw.strip()
                try:
                    items = json.loads(raw)
                except json.JSONDecodeError:
                    last_complete = raw.rfind("},")
                    if last_complete != -1:
                        items = json.loads(raw[:last_complete + 1] + "\n]")
                    else:
                        raise

            elapsed = time.time() - t0
            status.update(label=f"✅ Done in {elapsed:.1f}s — {len(items)} items found", state="complete")

            # ── Stats ──────────────────────────────────────────────────────
            st.markdown("### Summary")
            sc1, sc2, sc3, sc4 = st.columns(4)
            item_types = [i["item_type"] for i in items]
            top_type = max(set(item_types), key=item_types.count) if items else "—"
            avg_conf = sum(i.get("confidence", 0) for i in items) / max(len(items), 1)

            sc1.markdown(f'<div class="stat-box"><div class="stat-num">{len(items)}</div><div class="stat-label">Items detected</div></div>', unsafe_allow_html=True)
            sc2.markdown(f'<div class="stat-box"><div class="stat-num">{len(set(item_types))}</div><div class="stat-label">Item categories</div></div>', unsafe_allow_html=True)
            sc3.markdown(f'<div class="stat-box"><div class="stat-num">{top_type}</div><div class="stat-label">Most common type</div></div>', unsafe_allow_html=True)
            sc4.markdown(f'<div class="stat-box"><div class="stat-num">{avg_conf:.0%}</div><div class="stat-label">Avg confidence</div></div>', unsafe_allow_html=True)

            # ── Filter controls ────────────────────────────────────────────
            st.markdown("### Detected Items")
            all_types = sorted(set(i["item_type"] for i in items))
            all_patterns = sorted(set(i.get("pattern", "—") for i in items))

            f1, f2, f3 = st.columns(3)
            filter_type = f1.multiselect("Filter by type", all_types, default=[])
            filter_pattern = f2.multiselect("Filter by pattern", all_patterns, default=[])
            min_conf = f3.slider("Min confidence", 0.0, 1.0, 0.0, 0.05)

            filtered = items
            if filter_type:
                filtered = [i for i in filtered if i["item_type"] in filter_type]
            if filter_pattern:
                filtered = [i for i in filtered if i.get("pattern") in filter_pattern]
            filtered = [i for i in filtered if i.get("confidence", 0) >= min_conf]

            st.markdown("---")
            import pandas as pd
            summary_df = pd.DataFrame([{
                "ID": i["item_id"],
                "Type": i["item_type"].title(),
                "Subtype": i["item_subtype"],
                "Colors": ", ".join(i.get("colors", [])),
                "Pattern": i.get("pattern", ""),
                "Fit": i.get("fit", ""),
                "Material": i.get("material_guess", ""),
                "Style": ", ".join(i.get("style_tags", [])),
                "Brand": i.get("brand_visible") or "—",
                "Confidence": f"{i.get('confidence', 0):.0%}",
            } for i in filtered])
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            st.markdown("---")

            # ── Item cards ─────────────────────────────────────────────────
            for item in filtered:
                colors_html = "".join(
                    f'<span class="tag">● {c}</span>' for c in item.get("colors", [])
                )
                style_tags_html = "".join(
                    f'<span class="tag">{t}</span>' for t in item.get("style_tags", [])
                )
                meta_tags = f'<span class="tag">{item.get("pattern","")}</span> <span class="tag">{item.get("fit","")}</span> <span class="tag">{item.get("material_guess","")}</span>'
                conf = item.get("confidence", 0)
                brand = f'<span class="tag">🏷️ {item["brand_visible"]}</span>' if item.get("brand_visible") else ""

                st.markdown(f"""
<div class="item-card">
  <div class="item-header">[{item["item_id"]}] {item["item_type"].title()} — {item["item_subtype"]}</div>
  <div class="item-ts">👤 {item.get("person","")}</div>
  <div class="item-desc">{item.get("description","")}</div>
  <div style="margin-bottom:8px">{colors_html}</div>
  <div style="margin-bottom:8px">{meta_tags} {brand}</div>
  <div>{style_tags_html}</div>
  <div class="conf-bar-bg"><div class="conf-bar-fill" style="width:{conf*100:.0f}%"></div></div>
  <div style="font-size:11px;color:#7a7aaa;margin-top:4px">Confidence: {conf:.0%}</div>
</div>
""", unsafe_allow_html=True)

            # ── Raw JSON export ────────────────────────────────────────────
            st.markdown("### Export")
            st.download_button(
                "⬇️ Download JSON",
                data=json.dumps(items, indent=2),
                file_name=f"fashion_detection_{pathlib.Path(uploaded.name).stem}.json",
                mime="application/json",
            )
            with st.expander("View raw JSON"):
                st.json(items)

        except json.JSONDecodeError as e:
            st.error(f"Could not parse model response as JSON: {e}")
            st.text(response.text if "response" in locals() else "No response")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            os.unlink(tmp_path)

elif uploaded and not api_key:
    st.info("Enter your Gemini API key in the sidebar to run detection.")
elif not uploaded:
    st.markdown("""
    <div style="background:#1a1a2e;border:2px dashed #2d2d4a;border-radius:12px;padding:48px;text-align:center;color:#7a7aaa;">
        <div style="font-size:48px;margin-bottom:16px">📹</div>
        <div style="font-size:18px;color:#c4c4e0;margin-bottom:8px">Drop your video file above</div>
        <div>Supports MP4, MOV, AVI, MKV</div>
    </div>
    """, unsafe_allow_html=True)