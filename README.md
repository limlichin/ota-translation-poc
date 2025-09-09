# Shared Translation POC — Image → Multilingual Table

This proof-of-concept lets anyone upload an image with English text, extract the strings via OCR, and translate them into selected Southeast Asia languages. It then displays the image and a copy/export-friendly table (CSV/XLSX).

**Supported output headers (ISO-like):** `EN, ID, JA, KO, MS, TH, VI, ZH`  
(Under the hood, `ZH` maps to Simplified Chinese `zh-CN`.)

---

## What you can do

1. **Upload** a PNG/JPG image containing English text.
2. **Select languages** you actually need (multi-select).
3. **(Optional) Upload a glossary CSV** to override machine translations for specific strings.
4. **Extract + Translate** with one click (happens automatically on upload).
5. **Review & Export** the results to **CSV** or **Excel**. Optionally save a copy on the server (`./storage`).

> This POC is tuned for OTA (online travel agency) contexts in SEA. Use the glossary to ensure terms like “Apply (coupon)” get the right contextual equivalents.

---

## One‑time setup (no coding required)

### Option A — Local computer (Mac or Windows)

1. **Install Python (3.10–3.12 recommended).**  
   - Mac: Install via [python.org](https://www.python.org/downloads/) or `brew install python` if you use Homebrew.  
   - Windows: Download from [python.org](https://www.python.org/downloads/). On the installer, tick “Add Python to PATH.”

2. **Open a Terminal (Mac) or Command Prompt/PowerShell (Windows).**
3. **Create a project folder** and **enter it**:
   ```bash
   mkdir ota-translation-poc
   cd ota-translation-poc
   ```
4. **Create a virtual environment** (keeps things clean):
   ```bash
   python -m venv .venv
   # Activate it
   # Mac:
   source .venv/bin/activate
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   ```
5. **Download the two files** from this repo (or copy them in):  
   - `app.py`  
   - `requirements.txt`

6. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   > If you see popups about additional system packages for OCR, try:  
   > - Mac (Homebrew): `brew install tesseract` is **NOT** required here (we use EasyOCR), but installing `ffmpeg`/`libjpeg` sometimes helps images: `brew install ffmpeg jpeg`  
   > - Windows: make sure you installed Python 64-bit. If EasyOCR errors, run `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu` then rerun `pip install -r requirements.txt`.

7. **Run the app**:
   ```bash
   streamlit run app.py
   ```

8. Your browser will open at a local URL (something like `http://localhost:8501`).  
   Upload an image, pick languages, (optionally upload a glossary), and export.

### Option B — Streamlit Community Cloud (free)

1. Put `app.py` and `requirements.txt` in a new **public GitHub repo**.
2. Go to **share.streamlit.io**, connect your GitHub, and **deploy** the repo.
3. The app will build automatically and give you a URL you can share with your team.

---

## Using the glossary (optional but recommended)

- Create a CSV with headers: `EN, ID, JA, KO, MS, TH, VI, ZH`
- Add rows for strings you want to **force** (exact match on EN, case-insensitive trim). Example:

| EN             | ID     | JA               | KO       | MS    | TH          | VI       | ZH   |
|----------------|--------|------------------|----------|-------|-------------|----------|------|
| Apply coupon   | Klaim  | クーポンを適用     | 쿠폰 적용 | Tebus | ใช้คูปอง       | Áp dụng | 领取优惠券 |

Upload this CSV before/after the image; any matching EN cell will override machine translation.

---

## Notes on quality and context

- OCR quality depends on image clarity. High-contrast, readable text works best.
- Machine translation (Google via `deep-translator`) is strong, but **you should maintain a glossary** of OTA-specific terms for each market to ensure cultural and contextual accuracy.
- We **do not** preserve positions, styles, or formatting; output is plain text by line.
- We only translate **unique** strings (deduplicated) to reduce noise.

---

## Troubleshooting

- **EasyOCR model download stalls**: re-run `pip install -r requirements.txt` or ensure internet access the first time it runs (models are cached).
- **Windows Torch errors**: install CPU wheels explicitly:
  ```bash
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
  ```
- **Blank OCR results**: try a sharper image, larger font, or higher-contrast artwork.

---

## Tech choices

- **Streamlit** for a quick, shareable UI.
- **EasyOCR** for English text extraction (no Tesseract setup headaches).
- **deep-translator (GoogleTranslator)** for robust, production-grade baseline MT without API keys.
- **Glossary overrides** to achieve OTA-grade localization quality for SEA markets.
