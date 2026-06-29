"""
app.py  --  Streamlit UI for the Invoice Data Extraction demo.

A switch chooses between TWO extraction methods on the same invoice:
  * "Our model"  -> rule-based / pattern matching + OpenCV bounding boxes
  * "LLM model"  -> LangChain + Google Gemini structured extraction

Accepts PDF, DOCX, and image files (PNG/JPG/...). Images have no text layer,
so they are read via Tesseract OCR — useful for testing the OCR path.

Run with:   python -m streamlit run app.py
"""
import os
import json
import shutil
import tempfile

import cv2
import streamlit as st

import invoice_processor as ip
import llm_extract as llm

st.set_page_config(page_title="Invoice Data Extraction",
                   page_icon="🧾", layout="wide")

TESSERACT_OK = shutil.which("tesseract") is not None
LIBREOFFICE_OK = (shutil.which("soffice") or shutil.which("libreoffice")) is not None
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp", ".gif")


def bgr_to_rgb(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def color_chip(bgr):
    b, g, r = bgr
    return f"#{r:02x}{g:02x}{b:02x}"


# --------------------------------------------------------------------------- #
# Sidebar controls
# --------------------------------------------------------------------------- #
st.sidebar.title("⚙️ Controls")

uploaded = st.sidebar.file_uploader(
    "Upload an invoice",
    type=["pdf", "docx", "png", "jpg", "jpeg", "bmp", "tiff", "tif", "webp"])
st.sidebar.caption("📄 PDF · 🖼️ images (PNG/JPG) for OCR · 📝 DOCX (needs LibreOffice)")
use_sample = st.sidebar.button("Use the bundled sample invoice")

zoom = st.sidebar.slider("Render resolution (zoom)", 1.0, 3.0, 2.0, 0.5,
                         help="Higher = sharper image, slower processing.")
show_labels = st.sidebar.checkbox("Show text labels on boxes", value=True)
use_ocr = st.sidebar.checkbox(
    "Force OCR (for scanned invoices)", value=False,
    disabled=not TESSERACT_OK,
    help="Reads scanned/image invoices. Needs Tesseract installed.")
if not TESSERACT_OK:
    st.sidebar.caption("ℹ️ OCR is disabled because Tesseract isn't installed. "
                       "Needed for image / scanned invoices.")

st.sidebar.divider()
st.sidebar.subheader("🤖 Gemini (for the LLM model)")
gemini_key = st.sidebar.text_input(
    "Gemini API key", type="password",
    value=os.environ.get("GOOGLE_API_KEY", os.environ.get("GEMINI_API_KEY", "")),
    help="Free, no credit card: https://aistudio.google.com/ → Get API key")
st.sidebar.caption("Only used when the LLM model is selected.")

st.sidebar.divider()
all_types = list(ip.LABELS.keys())
chosen = st.sidebar.multiselect(
    "Sections to display (rule-based)",
    options=all_types, default=all_types,
    format_func=lambda t: ip.LABELS[t])

# --------------------------------------------------------------------------- #
# Header + method switch
# --------------------------------------------------------------------------- #
st.title("🧾 Invoice Data Extraction")
st.caption("Switch between the rule-based engine (bounding boxes) and the "
           "LangChain + Gemini LLM on the same invoice.")

RULE = "🔍 Our model (rule-based + boxes)"
LLM_MODE = "🤖 LLM model (Gemini)"
mode = st.radio("Extraction method", [RULE, LLM_MODE], horizontal=True)

st.divider()

# --------------------------------------------------------------------------- #
# Resolve input file
# --------------------------------------------------------------------------- #
work_dir = tempfile.mkdtemp()
src_path = None
if use_sample:
    if os.path.exists("sample_invoice.pdf"):
        src_path = "sample_invoice.pdf"
    else:
        st.error("sample_invoice.pdf not found. Run `python make_sample_invoice.py` first.")
elif uploaded is not None:
    src_path = os.path.join(work_dir, uploaded.name)
    with open(src_path, "wb") as f:
        f.write(uploaded.getbuffer())

if src_path is None:
    st.info("👈 Upload a PDF / image / DOCX invoice, or click "
            "**Use the bundled sample invoice** to start.")
    st.stop()

# Images and scans need OCR; turn it on automatically for image files.
is_image = os.path.splitext(src_path)[1].lower() in IMAGE_EXTS
eff_ocr = use_ocr or is_image
if is_image and not TESSERACT_OK:
    st.error("This is an image invoice, which needs OCR — but Tesseract isn't "
             "installed. Install it (winget install UB-Mannheim.TesseractOCR), "
             "add it to PATH, and relaunch.")
    st.stop()

# --------------------------------------------------------------------------- #
# Process (rule-based engine — local, free, runs for both modes to render page)
# --------------------------------------------------------------------------- #
try:
    with st.spinner("Reading the invoice…"):
        results = ip.process_file(src_path, zoom=zoom, use_ocr=eff_ocr,
                                  draw_labels=show_labels, work_dir=work_dir)
except RuntimeError as e:
    st.error(str(e)); st.stop()
except Exception as e:                       # pragma: no cover
    st.error(f"Could not process the file: {e}"); st.stop()

page_idx = 0
if len(results) > 1:
    page_idx = st.selectbox("Page", range(len(results)),
                            format_func=lambda i: f"Page {i + 1}") or 0
res = results[page_idx]

if res["used_ocr"]:
    st.info("📷 Read via OCR (no embedded text layer). On scans the rule-based "
            "side is rougher than the LLM — that's expected.")

# =========================================================================== #
# MODE 1 — Our model (rule-based + bounding boxes)
# =========================================================================== #
if mode == RULE:
    st.markdown("**Colour legend**")
    legend_cols = st.columns(len(ip.LABELS))
    for col, (t, name) in zip(legend_cols, ip.LABELS.items()):
        col.markdown(
            f"<div style='display:flex;align-items:center;gap:6px'>"
            f"<div style='width:14px;height:14px;border-radius:3px;"
            f"background:{color_chip(ip.COLORS[t])};border:1px solid #999'></div>"
            f"<span style='font-size:0.8rem'>{name}</span></div>",
            unsafe_allow_html=True)

    filtered = [d for d in res["detections"] if d["type"] in chosen]
    tables = res["tables"] if "table" in chosen else []
    annotated = ip.draw(res["original"], filtered, tables, show_labels=show_labels)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Original")
        st.image(bgr_to_rgb(res["original"]), use_container_width=True)
    with c2:
        st.subheader("Detected fields & tables")
        st.image(bgr_to_rgb(annotated), use_container_width=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Key fields detected", len(filtered))
    m2.metric("Tables detected", len(tables))
    m3.metric("Source", "OCR" if res["used_ocr"] else "PDF text layer")

    st.subheader("Extracted values")
    FIELD_ORDER = ["vendor", "invoice_number", "date", "total", "tax", "tax_id",
                   "from_addr", "bill_to", "ship_to", "email", "phone", "amount"]
    by_type = {}
    for d in filtered:
        by_type.setdefault(d["type"], []).append((d["text"] or "").strip())
    rows = []
    for t in FIELD_ORDER:
        if t not in chosen:
            continue
        vals = [v for v in by_type.get(t, []) if v]
        rows.append({"Field": ip.LABELS[t], "Value": "; ".join(vals) if vals else "-"})
    if rows:
        st.table(rows)

    ok, buf = cv2.imencode(".png", annotated)
    if ok:
        st.download_button("⬇️ Download annotated image", buf.tobytes(),
                           file_name=f"annotated_page_{page_idx + 1}.png",
                           mime="image/png")

# =========================================================================== #
# MODE 2 — LLM model (LangChain + Gemini)
# =========================================================================== #
else:
    if not gemini_key:
        st.warning("Enter a free Gemini API key in the sidebar. "
                   "Get one at https://aistudio.google.com/ (no credit card).")
        st.stop()

    proc_path = src_path
    if src_path.lower().endswith(".docx"):
        proc_path = ip.docx_to_pdf(src_path, work_dir)
    try:
        page_obj = ip.load_pdf(proc_path)[page_idx]
        text, llm_used_ocr = ip.page_text(page_obj, zoom=zoom, use_ocr=eff_ocr)
    except Exception as e:
        st.error(f"Could not read page text for the LLM: {e}"); st.stop()
    if not text.strip():
        st.error("No text could be read from this page."); st.stop()

    with st.spinner("Asking Gemini to extract the fields…"):
        data, err = llm.extract_invoice(text, gemini_key)
    if err:
        st.error(err); st.stop()

    d = data.model_dump()
    # Adaptive: only the fields THIS invoice actually has; drop blanks/N-A/dupes.
    rows, seen, fields = [], set(), d.get("fields", [])
    for fobj in fields:
        name = (fobj.get("name") or "").strip()
        val = (fobj.get("value") or "").strip().lstrip("•·▪◦*-–— ").strip()
        if not name or not val or val.lower() in ("n/a", "na", "none", "null", "-", "nil"):
            continue
        if name.lower() in seen:
            continue
        seen.add(name.lower())
        rows.append({"Field": name, "Value": val})

    # Locate each extracted value on the page and draw boxes (LLM bounding boxes).
    try:
        llm_dets = ip.locate_values(page_obj, fields, zoom=zoom, use_ocr=eff_ocr)
    except Exception:
        llm_dets = []
    annotated = ip.draw(res["original"], llm_dets, [], show_labels=show_labels)

    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Located on the invoice")
        st.image(bgr_to_rgb(annotated), use_container_width=True)
        st.caption(f"{len(llm_dets)} of {len(rows)} extracted values located & boxed "
                   "(values the LLM normalised or inferred may not box).")
    with c2:
        st.subheader("🤖 Gemini extraction")
        st.success(f"Text source: {'Tesseract OCR' if llm_used_ocr else 'PDF text layer'}")
        if not rows:
            st.warning("Gemini didn't find labelled fields in this document.")
        else:
            st.table(rows)
            flat = {r["Field"]: r["Value"] for r in rows}
            with st.expander("Raw LLM JSON"):
                st.json(flat)
            st.download_button("⬇️ Download extracted JSON", json.dumps(flat, indent=2),
                               file_name=f"invoice_data_page_{page_idx + 1}.json",
                               mime="application/json")

with st.expander("How it works"):
    st.markdown("""
**Our model (rule-based):** PyMuPDF reads the PDF text layer (or Tesseract OCR
for images/scans); keyword + regex + spatial rules classify each field; OpenCV
detects tables; colour-coded boxes are drawn.

**LLM model:** the same page text is sent to **Google Gemini via LangChain**
(`with_structured_output`), returning the fields present in the document. Each
returned value is then located on the page and boxed.

Use the switch at the top to view either one. Rules give boxes + precision on
clean PDFs; the LLM adapts its fields per invoice and is more robust on messy OCR.
""")
