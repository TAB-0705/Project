# Invoice Data Extraction — Rule-based + LLM (LangChain + Gemini)

Extracts key fields from invoices (invoice number, date, total, vendor, tax,
bill-to) using **two complementary methods**, shown side by side:

1. **Rule-based parsing + bounding boxes** — PyMuPDF reads the PDF text layer,
   keyword/regex rules classify fields, OpenCV detects tables, and colour-coded
   boxes are drawn on the page. Precision-first.
2. **LLM extraction** — the page text is sent to **Google Gemini via LangChain**
   (`with_structured_output`), returning a clean, validated JSON record. Robust
   on layouts the rules have never seen.

Text comes from the **PDF text layer** for digital invoices (accurate, no OCR),
and falls back to **Tesseract OCR** for scanned/image invoices.

## How this meets the assignment

| Requirement | How it's met |
|---|---|
| Extract invoice no / date / total / vendor with **LangChain or LlamaIndex** | `llm_extract.py` — LangChain `ChatGoogleGenerativeAI` + a Pydantic schema via `with_structured_output` |
| **Template matching / rule-based parsing** of structured invoices | `invoice_processor.py` — `KEYWORD_RULES`, `REGEX_RULES`, spatial value-finding, OpenCV table detection |
| **OCR** (Tesseract / Cloud Vision / Azure) on invoice **images** | Tesseract via `pytesseract` (`ocr_lines`, `page_text(..., use_ocr=True)`); Cloud Vision/Azure documented as drop-in alternatives below |

## Setup (Windows, recommended Python 3.12)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1        # if blocked: Set-ExecutionPolicy -Scope Process Bypass
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Free Gemini API key (no credit card)
1. Go to https://aistudio.google.com/  →  **Get API key**  →  create one.
2. Either paste it into the app's sidebar, or set it once:
   ```powershell
   setx GOOGLE_API_KEY "your_key_here"     # then open a NEW terminal
   ```
The free **gemini-2.0-flash** model is used by default.

### Tesseract (only needed for scanned/image invoices)
```powershell
winget install UB-Mannheim.TesseractOCR    # then restart the terminal
```
Digital PDFs do **not** need Tesseract — they use the text layer.

## Run

```powershell
python -m streamlit run app.py
```

Upload a PDF or image (or click **Use the bundled sample invoice**). Both the boxed
rule-based output and the Gemini LLM extraction appear, with a side-by-side
comparison table and a JSON download.

CLI smoke tests (no UI):
```powershell
python invoice_processor.py sample_invoice.pdf   # prints fields, writes annotated_page_1.png
python llm_extract.py sample_invoice.pdf          # prints the LLM-extracted record
```

## Demo click-through (≈3 min)
1. Open the app, click **Use the bundled sample invoice**.
2. Point at the coloured boxes — explain rules + OpenCV table detection (criterion 2).
3. Scroll to **LLM extraction** — show the structured Gemini output and the
   **Rule-based vs LLM** comparison table (criterion 1, LangChain).
4. Mention OCR: digital PDFs use the text layer; tick **Force OCR** (with
   Tesseract installed) or upload a scanned image to show the OCR path (criterion 3).
5. Download the JSON to show structured-data output.

## Swapping the OCR provider (optional, to literally "experiment with" others)
The OCR call lives in `ocr_lines()` / `page_text()` in `invoice_processor.py`.
To use **Google Cloud Vision** instead of Tesseract, replace the pytesseract
call with `google-cloud-vision`'s `document_text_detection` (needs a GCP key);
for **Azure**, use `azure-ai-formrecognizer` / Computer Vision Read. The rest of
the pipeline is unchanged because it only consumes the returned text + boxes.

## Files
- `invoice_processor.py` — rule-based engine + OpenCV + `page_text()` helper
- `llm_extract.py` — LangChain + Gemini structured extraction
- `app.py` — Streamlit UI (boxes + LLM comparison)
- `make_sample_invoice.py` — regenerates `sample_invoice.pdf`
- `requirements.txt`, `sample_invoice.pdf`

## Honest limitations (good for Q&A)
- Rules are precision-first; unusual/non-English labels may be missed (one-line
  edit to `KEYWORD_RULES`). The LLM path covers many of these.
- Borderless tables (no ruling lines) aren't boxed by the strict grid detector.
- Purely graphical logos need OCR (or a vision model) to yield a vendor name.
- Free Gemini tier is rate-limited; wait a few seconds between calls if needed.
