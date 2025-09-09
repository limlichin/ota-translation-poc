import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import io
import os
import time

# OCR
import easyocr

# Translation
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Image → Multilingual Table (OTA POC)", layout="wide")

st.title("Shared Translation POC — Image → Multilingual Table")
st.caption("Upload an image with English text → extract strings → translate to selected languages → export to CSV/XLSX.\n"
           "Supports custom glossary overrides per language (optional).")

with st.expander("Language selection (ISO-like headers)", expanded=True):
    # Display language codes (headers will be EN, ID, JA, KO, MS, TH, VI, ZH)
    language_options = ["ID","JA","KO","MS","TH","VI","ZH"]
    target_langs = st.multiselect(
        "Select target languages (you can pick one or more):",
        options=language_options,
        default=[]
    )
    st.caption("We always keep the English (EN) column. Headers shown in the table are EN + your selections.")

with st.expander("Optional: Upload a glossary CSV for overrides", expanded=False):
    st.write("Provide a CSV with columns: EN, ID, JA, KO, MS, TH, VI, ZH. "
             "If a source string matches EN exactly (case-insensitive trim), translations will be overridden.")
    glossary_file = st.file_uploader("Upload glossary CSV (optional)", type=["csv"], key="glossary")
    glossary_map = {}
    if glossary_file is not None:
        try:
            gdf = pd.read_csv(glossary_file).fillna("")
            # normalize headers
            expected_cols = ["EN","ID","JA","KO","MS","TH","VI","ZH"]
            missing = [c for c in expected_cols if c not in gdf.columns]
            if missing:
                st.error(f"Glossary missing columns: {', '.join(missing)}")
            else:
                for _, row in gdf.iterrows():
                    key = str(row["EN"]).strip().lower()
                    if key:
                        glossary_map[key] = {col: str(row[col]) for col in expected_cols}
                st.success(f"Loaded glossary with {len(glossary_map)} entries.")
        except Exception as e:
            st.error(f"Failed to read glossary: {e}")

# Helper: map UI codes to translator target codes
TARGET_CODE_MAP = {
    "ID": "id",
    "JA": "ja",
    "KO": "ko",
    "MS": "ms",
    "TH": "th",
    "VI": "vi",
    "ZH": "zh-CN",  # Simplified Chinese
}

def translate_text_list(texts, targets):
    """Translate each text into each selected target language using GoogleTranslator via deep_translator.
       Returns a dict: { "ID": [...], "JA": [...], ... } aligned with texts order.
    """
    results = {code: [] for code in targets}
    for t in texts:
        base = str(t)
        for code in targets:
            # Glossary override first (exact match on EN, case-insensitive)
            if glossary_map:
                gkey = base.strip().lower()
                if gkey in glossary_map and glossary_map[gkey].get(code, ""):
                    results[code].append(glossary_map[gkey][code])
                    continue
            # Fall back to MT
            try:
                tgt = TARGET_CODE_MAP[code]
                translated = GoogleTranslator(source="en", target=tgt).translate(base)
                results[code].append(translated)
            except Exception as e:
                results[code].append(f"[Translation error: {e}]")
    return results

def ocr_extract_strings(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    st.image(image, caption="Uploaded Image", use_container_width=True)
    np_img = np.array(image)

    with st.spinner("Running OCR (English)..."):
        reader = easyocr.Reader(['en'], gpu=False)
        # detail=0 returns only text lines
        texts = reader.readtext(np_img, detail=0, paragraph=False)
    # Clean up: strip, remove empties, deduplicate preserving order
    cleaned = []
    seen = set()
    for t in texts:
        s = str(t).strip()
        if s and s not in seen:
            cleaned.append(s)
            seen.add(s)
    return cleaned

st.subheader("1) Upload an image")
uploaded = st.file_uploader("Upload PNG/JPG image containing English text", type=["png","jpg","jpeg"])

if uploaded is not None:
    try:
        img_bytes = uploaded.read()
        strings = ocr_extract_strings(img_bytes)

        if not strings:
            st.warning("No text detected. Try another image or ensure there is clear English text.")
        else:
            st.success(f"Extracted {len(strings)} unique text strings.")
            # Build base dataframe
            df = pd.DataFrame({"EN": strings})

            if target_langs:
                st.subheader("2) Translating…")
                with st.spinner("Translating to selected languages…"):
                    tdict = translate_text_list(strings, target_langs)
                for code in target_langs:
                    df[code] = tdict[code]
            else:
                st.info("No target languages selected — showing only EN. Use the selector above to add languages.")

            st.subheader("3) Review & Export")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Prepare downloads
            csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Download as CSV", data=csv_bytes, file_name="translations.csv", mime="text/csv")

            # Excel export
            import xlsxwriter
            excel_buf = io.BytesIO()
            with pd.ExcelWriter(excel_buf, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="translations")
            st.download_button("⬇️ Download as Excel (.xlsx)", data=excel_buf.getvalue(),
                               file_name="translations.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # Optional: Save a copy on server (for simple persistence)
            save = st.checkbox("Also save a copy on server (./storage)")
            if save:
                os.makedirs("storage", exist_ok=True)
                ts = time.strftime("%Y%m%d-%H%M%S")
                df.to_csv(f"storage/translations_{ts}.csv", index=False)
                with pd.ExcelWriter(f"storage/translations_{ts}.xlsx", engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False, sheet_name="translations")
                st.success(f"Saved to storage/translations_{ts}.xlsx and .csv")

            st.caption("Tip: Use the glossary CSV to enforce preferred wording for OTA context (e.g., “Apply” (coupon) → context-appropriate equivalents).")
    except Exception as e:
        st.error(f"Something went wrong: {e}")
else:
    st.info("Awaiting image upload…")
