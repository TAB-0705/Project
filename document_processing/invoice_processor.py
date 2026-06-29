"""
invoice_processor.py
--------------------
Core engine for the Invoice Bounding-Box demo.

Pipeline:
  1. Load a PDF (or DOCX converted to PDF) and render each page to an image.
  2. Pull the text layer (word boxes) directly from the PDF  -> accurate, no OCR.
     If a page has no text layer (scanned image), optionally fall back to OCR.
  3. Classify "key fields" (invoice no, dates, totals, tax, bill-to, email, etc.)
     using keyword + regex rules, mapping each back to its bounding box.
  4. Detect tables with OpenCV (morphological line detection).
  5. Draw colour-coded boxes with OpenCV.

Everything here is plain Python so it can be imported by the Streamlit app
or run on its own.
"""

import os
import re
import cv2
import fitz  # PyMuPDF
import numpy as np

# ---------------------------------------------------------------------------
# Colour map.  OpenCV uses BGR, so these tuples are (Blue, Green, Red).
# ---------------------------------------------------------------------------
COLORS = {
    "invoice_number": (255, 0, 0),     # blue
    "date":           (0, 170, 0),     # green
    "total":          (0, 0, 220),     # red
    "tax":            (0, 140, 255),   # orange
    "tax_id":         (0, 200, 200),   # yellow-ish (GSTIN / VAT no.)
    "vendor":         (180, 0, 180),   # purple
    "bill_to":        (200, 130, 0),   # teal/blue-green
    "ship_to":        (130, 90, 0),    # dark teal
    "from_addr":      (0, 110, 90),    # dark green-teal (sender)
    "email":          (60, 60, 60),    # dark grey
    "phone":          (110, 110, 110),  # grey
    "amount":         (0, 80, 160),    # brown/orange
    "table":          (255, 0, 255),   # magenta
}

# Human-friendly labels drawn on the image / shown in the legend.
LABELS = {
    "invoice_number": "Invoice No",
    "date":           "Date",
    "total":          "Total",
    "tax":            "Tax",
    "tax_id":         "Tax ID",
    "vendor":         "Vendor",
    "bill_to":        "Bill To",
    "ship_to":        "Ship To",
    "from_addr":      "From",
    "email":          "Email",
    "phone":          "Phone",
    "amount":         "Amount",
    "table":          "Table",
}

# Keyword patterns: if a text line matches, the value tokens after it (or the
# whole line) get tagged with this field type.
KEYWORD_RULES = {
    "invoice_number": [r"invoice\s*(no|number|num|#)", r"\binv\s*(no|#)",
                       r"bill\s*(no|number)", r"receipt\s*(no|number)"],
    "date":           [r"invoice\s*date", r"due\s*date", r"\bdate\b", r"dated"],
    "total":          [r"grand\s*total", r"total\s*due", r"amount\s*due",
                       r"balance\s*due", r"\btotal\b"],
    # tax_id MUST come before tax so "GST Number" is an ID, not a tax amount.
    "tax_id":         [r"gst\s*(no|number|in)", r"gstin", r"tax\s*id",
                       r"vat\s*(no|number|reg)", r"\btin\b", r"pan\b"],
    "tax":            [r"\bc?gst\b", r"\bs?gst\b", r"\bigst\b", r"\bvat\b",
                       r"sales\s*tax", r"\btax\b"],
    "bill_to":        [r"bill\s*to", r"billed\s*to", r"invoice\s*to",
                       r"sold\s*to"],
    "ship_to":        [r"ship\s*to", r"shipped\s*to", r"deliver\s*to"],
    "from_addr":      [r"bill\s*from", r"\bfrom\b", r"sold\s*by",
                       r"\bsupplier\b", r"\bseller\b"],
}

# Standalone regexes that don't need a label nearby.
REGEX_RULES = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    # phone: only accept candidates that contain at least 10 digits, so that
    # short codes like an invoice id "2026-00871" are not misread as a phone.
    "phone": re.compile(r"(\(?\+?\d[\d\s().\-]{8,}\d)"),
}


def _looks_like_phone(s):
    """A real phone number: 9-13 digits AND phone-style separators.

    This rejects long digit runs that are actually register numbers, account
    numbers, or transaction IDs (e.g. '27118551409', '2023040446')."""
    digits = sum(c.isdigit() for c in s)
    if not (10 <= digits <= 13):
        return False
    if "/" in s or "@" in s:
        return False
    if not re.search(r"[+()\-]| \d", s):   # must contain +, (), -, or spaced groups
        return False
    return True


_MONEY_RE = re.compile(r"[\$₹€£]\s?\d|\d[\d,]*\.\d{2}")


def _is_money(s):
    return bool(_MONEY_RE.search(s))


def _is_taxid(s):
    """Alphanumeric tax identifier like a GSTIN (mix of letters and digits)."""
    s = s.strip()
    return (len(s) >= 8 and any(c.isalpha() for c in s)
            and any(c.isdigit() for c in s) and " " not in s)


def _is_placeholder(s):
    """True for blank-template format strings like 'mm/dd/yyyy' or 'dd-mm-yyyy'.

    These appear on un-filled invoice templates and must NOT be treated as
    real values. Matches tokens made only of m/d/y letters joined by / - or .
    (case-insensitive). A real date such as '02-Feb-2026' or '12/06/2026'
    contains other letters or digits, so it is not matched.
    """
    t = s.strip().lower()
    return bool(re.fullmatch(r"[mdy]{1,4}([/\-.][mdy]{1,4}){1,2}", t))


# When walking down from a Bill-To / Ship-To label, stop the block as soon as
# the next line looks like a different section (another label, a table header,
# or a totals row).
_STOP_RE = re.compile(
    r"(ship\s*to|bill\s*to|bill\s*from|deliver\s*to|sold\s*to|sold\s*by|"
    r"\bfrom\b|\bcustomer\b|\brecipient\b|\bsupplier\b|\bdetails\b|\bterms\b|"
    r"\binvoice\b|\breceipt\b|\bpayment\b|description|\bqty\b|"
    r"quantity|unit\s*price|\bamount\b|subtotal|grand\s*total|\btotal\b|"
    r"\btax\b|hsn|sac)", re.I)


# ---------------------------------------------------------------------------
# Loading / rendering
# ---------------------------------------------------------------------------
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp", ".gif")


def load_pdf(path):
    """Open a PDF and return the fitz document.

    Image files (.png/.jpg/...) are converted to a single-page PDF on the fly so
    the rest of the pipeline is unchanged. An image has no text layer, so it
    automatically goes through the OCR path.
    """
    if os.path.splitext(path)[1].lower() in IMAGE_EXTS:
        img_doc = fitz.open(path)
        pdf_bytes = img_doc.convert_to_pdf()       # wrap the image in a PDF page
        img_doc.close()
        return fitz.open("pdf", pdf_bytes)
    return fitz.open(path)


def docx_to_pdf(docx_path, out_dir):
    """
    Best-effort DOCX -> PDF using LibreOffice headless (cross-platform).
    Returns the PDF path, or raises RuntimeError if LibreOffice isn't found.
    """
    import shutil
    import subprocess
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError(
            "LibreOffice not found. Install it to convert DOCX, or upload a PDF.")
    subprocess.run([soffice, "--headless", "--convert-to", "pdf",
                    "--outdir", out_dir, docx_path], check=True,
                   capture_output=True, timeout=60)
    base = os.path.splitext(os.path.basename(docx_path))[0] + ".pdf"
    return os.path.join(out_dir, base)


def page_to_image(page, zoom=2.0):
    """Render a PDF page to a BGR numpy image (for OpenCV)."""
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
    elif pix.n == 3:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    else:  # grayscale
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return np.ascontiguousarray(img)


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------
def get_lines(page, zoom):
    """
    Return text grouped into lines using the PDF text layer.
    Each line: {text, words:[(x0,y0,x1,y1,word)], box:(x0,y0,x1,y1)}.
    Coordinates are scaled by `zoom` to match the rendered image.
    """
    words = page.get_text("words")  # x0,y0,x1,y1,word,block,line,word_no
    lines = {}
    for x0, y0, x1, y1, w, b, l, _ in words:
        key = (b, l)
        lines.setdefault(key, []).append(
            (x0 * zoom, y0 * zoom, x1 * zoom, y1 * zoom, w))
    out = []
    for key, ws in lines.items():
        ws.sort(key=lambda t: t[0])
        text = " ".join(t[4] for t in ws)
        xs0 = min(t[0] for t in ws); ys0 = min(t[1] for t in ws)
        xs1 = max(t[2] for t in ws); ys1 = max(t[3] for t in ws)
        out.append({"text": text, "words": ws, "box": (xs0, ys0, xs1, ys1)})
    return out


def _preprocess_for_ocr(img):
    """Clean a scanned page before OCR: grayscale, denoise, and binarize.
    Crisp black-on-white text markedly improves Tesseract accuracy on faint /
    grey thermal receipts (e.g. fewer misreads like 'CS' -> '€§'). Coordinates
    are unchanged (no resize), so boxes still line up with the rendered image.
    """
    try:
        g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
        g = cv2.bilateralFilter(g, 5, 40, 40)         # denoise, preserve edges
        bw = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 31, 15)
        return bw
    except Exception:
        return img                                    # fall back to raw


def ocr_lines(img):
    """OCR fallback for scanned pages. Requires pytesseract + Tesseract.

    Runs OCR on both the raw image and a binarized (enhanced) version, then
    keeps whichever Tesseract is more confident about. This lifts accuracy on
    faint/grey scans (fewer misreads like 'CS' -> '€§') without hurting clean
    scans, where the raw image already wins.
    """
    import pytesseract
    from pytesseract import Output

    def run(im):
        d = pytesseract.image_to_data(im, output_type=Output.DICT)
        confs = [float(c) for c, t in zip(d["conf"], d["text"])
                 if t.strip() and str(c) not in ("-1", "")]
        mean = sum(confs) / len(confs) if confs else -1
        return d, mean

    data, conf_raw = run(img)
    try:
        data_bw, conf_bw = run(_preprocess_for_ocr(img))
        if conf_bw > conf_raw:                       # enhanced read better
            data = data_bw
    except Exception:
        pass
    lines = {}
    n = len(data["text"])
    for i in range(n):
        txt = data["text"][i].strip()
        if not txt:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        x, y, w, h = (data["left"][i], data["top"][i],
                      data["width"][i], data["height"][i])
        lines.setdefault(key, []).append((x, y, x + w, y + h, txt))
    out = []
    for ws in lines.values():
        ws.sort(key=lambda t: t[0])
        text = " ".join(t[4] for t in ws)
        xs0 = min(t[0] for t in ws); ys0 = min(t[1] for t in ws)
        xs1 = max(t[2] for t in ws); ys1 = max(t[3] for t in ws)
        out.append({"text": text, "words": ws, "box": (xs0, ys0, xs1, ys1)})
    return out


# ---------------------------------------------------------------------------
# Field classification
# ---------------------------------------------------------------------------
def _value_box_after(line, match_end_char):
    """
    Given a line and the char index where a keyword match ends, return the
    bounding box of the value words that come *after* the keyword on that line.
    Falls back to the full line box if nothing sensible follows.
    """
    # Rebuild char offsets per word to find which words are "after" the keyword.
    text = line["text"]
    offsets = []
    pos = 0
    for w in line["words"]:
        idx = text.find(w[4], pos)
        offsets.append((idx, idx + len(w[4]), w))
        pos = idx + len(w[4])
    value_words = [w for (s, e, w) in offsets if s >= match_end_char]
    # strip a leading ":" token if present
    value_words = [w for w in value_words if w[4].strip(":")]
    if not value_words:
        return None, ""

    # Cut the value at the first large horizontal gap. On two-column receipts a
    # single text line can read "Label  value    NextLabel  nextvalue"; without
    # this we would sweep the neighbouring column into the value.
    value_words.sort(key=lambda w: w[0])
    ly0, ly1 = line["box"][1], line["box"][3]
    lh = max(1.0, ly1 - ly0)
    kept = [value_words[0]]
    for prev, cur in zip(value_words, value_words[1:]):
        if (cur[0] - prev[2]) > 1.5 * lh:      # big gap -> a new column starts
            break
        kept.append(cur)
    value_words = kept

    # Drop leading tokens that are pure separators / bullets ("=", "•", "-", …)
    # but keep currency symbols. These show up as stray prefixes like "= 8,000".
    _junk = set("=•·▪◦*|-–—:")
    while value_words and value_words[0][4] and all(c in _junk for c in value_words[0][4]):
        value_words.pop(0)
    if not value_words:
        return None, ""

    xs0 = min(w[0] for w in value_words); ys0 = min(w[1] for w in value_words)
    xs1 = max(w[2] for w in value_words); ys1 = max(w[3] for w in value_words)
    val_text = " ".join(w[4] for w in value_words).lstrip("=•·▪◦*|-–— :")
    return (xs0, ys0, xs1, ys1), val_text


def _value_right(label_line, lines):
    """Find the nearest text line to the right of a label on the same row."""
    lx0, ly0, lx1, ly1 = label_line["box"]
    lh = max(1.0, ly1 - ly0)
    cands = []
    for o in lines:
        if o is label_line:
            continue
        ox0, oy0, ox1, oy1 = o["box"]
        overlap = min(ly1, oy1) - max(ly0, oy0)
        if overlap > 0.4 * lh and ox0 >= lx1 - 0.3 * lh:
            cands.append((ox0 - lx1, o))
    if not cands:
        return None, ""
    cands.sort(key=lambda t: t[0])
    o = cands[0][1]
    return o["box"], o["text"]


def _clip_to_column(line, col_x0, lh):
    """Return (box, text) for just the words of `line` that belong to the column
    starting near `col_x0` — from the first word at/after that x, up to the first
    large horizontal gap. On a digital invoice each cell is already its own line,
    so this returns the whole line unchanged. On a SCANNED invoice Tesseract
    merges columns into one line ("A Inc.  B Warehouse"); this keeps only the
    left part so a left-column address block doesn't span into the right column.
    """
    ws = sorted(line.get("words", []), key=lambda w: w[0])
    ws = [w for w in ws if w[0] >= col_x0 - 1.0 * lh]
    if not ws:
        return line["box"], line["text"]
    kept = [ws[0]]
    for prev, cur in zip(ws, ws[1:]):
        if (cur[0] - prev[2]) > 1.5 * lh:          # big gap -> next column
            break
        kept.append(cur)
    xs0 = min(w[0] for w in kept); ys0 = min(w[1] for w in kept)
    xs1 = max(w[2] for w in kept); ys1 = max(w[3] for w in kept)
    return (xs0, ys0, xs1, ys1), " ".join(w[4] for w in kept)


def _value_below(label_line, lines, tables=None):
    """Box the label plus the address block sitting beneath it (bill/ship to).

    The block is kept tight: it stops at the first big vertical gap, at the
    next section keyword, after a few lines, never extends into a detected table
    region, and is clipped to the label's column so it can't span into an
    adjacent column (important for scanned invoices where OCR merges columns).
    """
    lx0, ly0, lx1, ly1 = label_line["box"]
    lh = max(1.0, ly1 - ly0)

    # y-ceiling: top of the nearest table that begins below this label.
    ceiling = float("inf")
    for (tx, ty, tw, th) in (tables or []):
        if ty > ly0:
            ceiling = min(ceiling, ty)

    lbox, _ = _clip_to_column(label_line, lx0, lh)   # clip label to its column
    block = [lbox]
    texts = []
    prev_bottom = ly1
    count = 0
    for o in sorted(lines, key=lambda l: l["box"][1]):
        ox0, oy0, ox1, oy1 = o["box"]
        if oy0 <= ly1:                         # at/above the label
            continue
        if oy0 >= ceiling - 0.3 * lh:          # would enter a table -> stop
            break
        # Headings often sit further above their address block than the block's
        # own line spacing, so allow a bigger gap before the FIRST line.
        gap_limit = 4.0 * lh if count == 0 else 2.5 * lh
        if (oy0 - prev_bottom) > gap_limit:    # big gap -> address block ended
            break
        if count >= 5:                         # safety cap on block height
            break
        if abs(ox0 - lx0) > 4 * lh:            # different column -> skip
            continue
        if _STOP_RE.search(o["text"]):         # hit the next section -> stop
            break
        cbox, ctext = _clip_to_column(o, lx0, lh)   # left-column part only
        block.append(cbox)
        texts.append(ctext)
        prev_bottom = oy1
        count += 1

    xs0 = min(b[0] for b in block); ys0 = min(b[1] for b in block)
    xs1 = max(b[2] for b in block); ys1 = max(b[3] for b in block)
    return (xs0, ys0, xs1, ys1), " ".join(texts)


def classify(lines, tables=None):
    """
    Run keyword + regex rules over the lines and return a list of detections:
      {type, label, box:(x0,y0,x1,y1), text}
    """
    detections = []
    seen = set()

    for line in lines:
        low = line["text"].lower()

        # keyword-based fields -> tag the value (same line, or to the right/below)
        for ftype, patterns in KEYWORD_RULES.items():
            matched = next((re.search(p, low) for p in patterns
                            if re.search(p, low)), None)
            if not matched:
                continue
            # "From"/"Customer" etc. are header labels; ignore long sentences
            # that merely contain the word (e.g. a footer note).
            if ftype == "from_addr" and len(line["text"].split()) > 4:
                continue
            box, val = _value_box_after(line, matched.end())
            # If an address label's same-line value is actually another section
            # heading (e.g. OCR merged "Bill To:  Ship To:" onto one line),
            # discard it so the address-below / right-cell logic runs instead.
            if ftype in ("bill_to", "ship_to", "from_addr") and val and _STOP_RE.search(val):
                box = None
            # money fields should land on a currency value; if the same-line
            # text after the label isn't money-like, look to the right.
            if ftype in ("total", "tax") and (val and not _is_money(val)):
                box = None
            if box is None:
                if ftype in ("bill_to", "ship_to", "from_addr"):
                    box, val = _value_below(line, lines, tables)
                    if not val:           # address may sit beside the label
                        rbox, rval = _value_right(line, lines)
                        # but never grab a neighbouring section heading
                        # (e.g. Bill-To sitting left of Ship-To on the same row)
                        if rval and not _STOP_RE.search(rval):
                            box, val = rbox, rval
                else:
                    box, val = _value_right(line, lines)
            if box is None:
                box, val = line["box"], line["text"]
            # Don't emit a "value" that is only punctuation/bullets (e.g. "•").
            if not any(c.isalnum() for c in val):
                break
            # If an address field found nothing but the label itself, drop it
            # rather than boxing the heading ("Bill To" with value "Bill to").
            if ftype in ("bill_to", "ship_to", "from_addr") and box == line["box"]:
                break
            # Accuracy guard: only emit a field when its value is the right type.
            if ftype == "total" and not _is_money(val):
                break
            if ftype == "tax" and not _is_money(val):
                break
            if ftype == "tax_id" and not _is_taxid(val):
                break
            key = (ftype, round(box[0]), round(box[1]))
            if key not in seen:
                seen.add(key)
                detections.append({"type": ftype, "label": LABELS[ftype],
                                   "box": box, "text": val})
            break  # one keyword field per line

        # regex-based fields (email, phone) -> box just the matching word(s)
        for ftype, rgx in REGEX_RULES.items():
            for m in rgx.finditer(line["text"]):
                frag = m.group(0).strip()
                if ftype == "phone" and not _looks_like_phone(frag):
                    continue
                hit = [w for w in line["words"]
                       if w[4] in frag or frag in w[4]]
                if not hit:
                    continue
                xs0 = min(w[0] for w in hit); ys0 = min(w[1] for w in hit)
                xs1 = max(w[2] for w in hit); ys1 = max(w[3] for w in hit)
                key = (ftype, round(xs0), round(ys0))
                if key not in seen:
                    seen.add(key)
                    detections.append({"type": ftype, "label": LABELS[ftype],
                                       "box": (xs0, ys0, xs1, ys1),
                                       "text": frag})
    return detections


_VENDOR_REJECT = re.compile(
    r"receipt|invoice|number|\bno\b|\bdate\b|bill|ship|amount|total|tax|"
    r"details|register|application|payment|\bgst\b|name|terms|campus|"
    r"program|year", re.I)


def detect_vendor(page, zoom, page_height):
    """Heuristic: a *prominent* name near the top of the page = vendor.

    Requires the candidate's font size to be clearly larger than the body text
    (a company header/logo text stands out). Skips labels and numeric spans.
    Returns None when nothing qualifies (e.g. the logo is an image), which is
    safer than mistaking an ordinary name for the vendor.
    """
    d = page.get_text("dict")
    cutoff = page_height / zoom * 0.30

    sizes = [sp["size"] for b in d.get("blocks", [])
             for ln in b.get("lines", []) for sp in ln.get("spans", [])
             if sp["text"].strip()]
    if not sizes:
        return None
    sizes.sort()
    body = sizes[len(sizes) // 2]          # median font size ~ body text
    threshold = body * 1.4                 # vendor must clearly stand out

    cands = []
    for block in d.get("blocks", []):
        for ln in block.get("lines", []):
            for sp in ln.get("spans", []):
                txt = sp["text"].strip()
                if sp["bbox"][1] > cutoff or len(txt) < 3:
                    continue
                if any(ch.isdigit() for ch in txt):
                    continue
                if _VENDOR_REJECT.search(txt):
                    continue
                if sp["size"] < threshold:
                    continue
                cands.append((sp["size"], sp))
    if not cands:
        return None
    cands.sort(key=lambda t: -t[0])
    sp = cands[0][1]
    x0, y0, x1, y1 = [c * zoom for c in sp["bbox"]]
    return {"type": "vendor", "label": LABELS["vendor"],
            "box": (x0, y0, x1, y1), "text": sp["text"].strip()}


def ocr_vendor(img, top_frac=0.22):
    """Best-effort vendor extraction from a *logo image* via OCR.

    Renders nothing new — it OCRs the top band of the already-rendered page
    image and returns the most prominent (largest) non-label text line, which
    is usually the company name inside a logo. Requires Tesseract; callers
    guard against its absence. Returns a detection dict or None.

    Honest limitation: clean logo lettering reads well, but highly stylised
    or purely graphical logos may be misread or unreadable.
    """
    import pytesseract
    from pytesseract import Output

    h = img.shape[0]
    band = img[0:int(h * top_frac)]
    data = pytesseract.image_to_data(band, output_type=Output.DICT)

    lines = {}
    for i in range(len(data["text"])):
        txt = data["text"][i].strip()
        try:
            conf = float(data["conf"][i])
        except ValueError:
            conf = -1.0
        if not txt or conf < 40:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(
            (data["left"][i], data["top"][i],
             data["width"][i], data["height"][i], txt))

    best = None
    for ws in lines.values():
        text = " ".join(t[4] for t in ws).strip()
        if len(text) < 3 or any(ch.isdigit() for ch in text):
            continue
        if _VENDOR_REJECT.search(text):
            continue
        height = max(t[3] for t in ws)        # bigger text = more prominent
        if best is None or height > best[0]:
            x0 = min(t[0] for t in ws); y0 = min(t[1] for t in ws)
            x1 = max(t[0] + t[2] for t in ws); y1 = max(t[1] + t[3] for t in ws)
            best = (height, (x0, y0, x1, y1), text)
    if not best:
        return None
    return {"type": "vendor", "label": LABELS["vendor"],
            "box": best[1], "text": best[2]}


# ---------------------------------------------------------------------------
# Table detection (the OpenCV core)
# ---------------------------------------------------------------------------
def detect_tables(img):
    """
    Detect *real* tables via morphological line detection.

    A bordered address box is also a rectangle of lines, so to avoid false
    positives we require an actual grid: a candidate region must contain
    several intersecting horizontal and vertical lines (a header + rows + at
    least one column separator), not just a 4-sided border.
    Returns a list of (x, y, w, h) boxes.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    thresh = cv2.adaptiveThreshold(~gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY, 15, -2)

    hk = cv2.getStructuringElement(cv2.MORPH_RECT, (max(10, w // 30), 1))
    horiz = cv2.dilate(cv2.erode(thresh, hk), hk)
    vk = cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(10, h // 30)))
    vert = cv2.dilate(cv2.erode(thresh, vk), vk)

    joints = cv2.bitwise_and(horiz, vert)          # grid crossing points
    grid = cv2.add(horiz, vert)                     # no extra dilation -> keep
    contours, _ = cv2.findContours(grid, cv2.RETR_EXTERNAL,  # boxes separate
                                   cv2.CHAIN_APPROX_SIMPLE)

    def count_lines(mask, span_min):
        n, _, stats, _ = cv2.connectedComponentsWithStats(mask)
        return n, stats

    boxes = []
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        if bw < w * 0.25 or bh < h * 0.05:          # too small to be a table
            continue

        # how many grid crossing points fall inside this region?
        jroi = joints[y:y + bh, x:x + bw]
        n_joints = cv2.connectedComponentsWithStats(jroi)[0] - 1

        # how many full-width horizontal / full-height vertical lines inside?
        hroi = horiz[y:y + bh, x:x + bw]
        n_h, hstats = count_lines(hroi, bw)
        h_lines = sum(1 for i in range(1, n_h)
                      if hstats[i, cv2.CC_STAT_WIDTH] > 0.5 * bw)
        vroi = vert[y:y + bh, x:x + bw]
        n_v, vstats = count_lines(vroi, bh)
        v_lines = sum(1 for i in range(1, n_v)
                      if vstats[i, cv2.CC_STAT_HEIGHT] > 0.5 * bh)

        # a real table: >=3 horizontal rules, >=2 vertical rules, many joints.
        if h_lines >= 3 and v_lines >= 2 and n_joints >= 6:
            boxes.append((x, y, bw, bh))

    boxes.sort(key=lambda b: -b[2] * b[3])
    boxes = boxes[:4]
    boxes.sort(key=lambda b: b[1])
    return boxes


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
def _norm_tok(s):
    """Normalise a token for matching: lowercase, drop currency/commas/punct."""
    s = s.lower().replace(",", "")
    s = re.sub(r"[₹$€£]", "", s)
    s = re.sub(r"[^\w./@+-]", "", s)
    return s


def locate_values(page, fields, zoom=2.0, use_ocr=False):
    """Map LLM-extracted {name, value} fields back to boxes on the page.

    The LLM returns text only (no coordinates), so we find where each value
    sits by matching it against the page's word boxes. Returns draw-ready
    detections [{label, text, box, color, type}]. Values that can't be located
    on the page (e.g. inferred/normalised by the model) are simply skipped.
    """
    has_text = bool(page.get_text("words"))
    lines = get_lines(page, zoom) if (has_text and not use_ocr) \
        else ocr_lines(page_to_image(page, zoom))

    words = []                                   # (x0,y0,x1,y1, norm_token)
    for ln in lines:
        for w in ln["words"]:
            nt = _norm_tok(w[4])
            if nt:
                words.append((w[0], w[1], w[2], w[3], nt))

    def tok_match(wt, vt):
        if wt == vt:
            return True
        return (len(vt) >= 4 and len(wt) >= 4
                and (wt.startswith(vt) or vt.startswith(wt)))

    used = set()

    def find_run(vtoks):
        n = len(vtoks)
        if n == 0:
            return None
        for i in range(len(words) - n + 1):
            if any((i + j) in used for j in range(n)):
                continue
            if all(tok_match(words[i + j][4], vtoks[j]) for j in range(n)):
                run = words[i:i + n]
                for j in range(n):
                    used.add(i + j)
                return (min(w[0] for w in run), min(w[1] for w in run),
                        max(w[2] for w in run), max(w[3] for w in run))
        return None

    def find_in_line(nv):
        for ln in lines:
            if nv and nv in _norm_tok(ln["text"]):
                return ln["box"]
        return None

    COLOR = (150, 110, 10)                        # teal-ish (BGR)
    dets = []
    for fld in fields:
        name = (fld.get("name") or "").strip()
        val = (fld.get("value") or "").strip()
        if not name or not val or val.lower() in ("n/a", "na", "none", "null", "-", "nil"):
            continue
        vtoks = [_norm_tok(t) for t in val.split()]
        vtoks = [t for t in vtoks if t]
        box = find_run(vtoks) or find_in_line(_norm_tok(val.replace(" ", "")))
        if box:
            dets.append({"label": name, "text": val, "box": box,
                         "color": COLOR, "type": "llm"})
    return dets


def draw(img, detections, tables, show_labels=True):
    out = img.copy()
    for t in tables:
        x, y, w, h = t
        cv2.rectangle(out, (x, y), (x + w, y + h), COLORS["table"], 3)
        if show_labels:
            _label(out, "TABLE", x, y, COLORS["table"], scale=0.7, thick=2)
    for d in detections:
        x0, y0, x1, y1 = [int(round(v)) for v in d["box"]]
        color = d.get("color") or COLORS.get(d["type"], (180, 70, 200))
        cv2.rectangle(out, (x0, y0), (x1, y1), color, 2)
        if show_labels:
            _label(out, d["label"], x0, y0, color)
    return out


def _label(img, text, x, y, color, scale=0.5, thick=1):
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)
    y_top = max(th + 4, y)
    cv2.rectangle(img, (x, y_top - th - 4), (x + tw + 4, y_top), color, -1)
    cv2.putText(img, text, (x + 2, y_top - 3), cv2.FONT_HERSHEY_SIMPLEX,
                scale, (255, 255, 255), thick, cv2.LINE_AA)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def _inside_address(box, detections):
    """True if `box` lies mostly within a Bill-To/Ship-To/From box."""
    bx0, by0, bx1, by1 = box
    bcx, bcy = (bx0 + bx1) / 2, (by0 + by1) / 2
    for d in detections:
        if d["type"] in ("bill_to", "ship_to", "from_addr"):
            ax0, ay0, ax1, ay1 = d["box"]
            if ax0 <= bcx <= ax1 and ay0 <= bcy <= ay1:
                return True
    return False


def process_page(page, zoom=2.0, use_ocr=False, draw_labels=True):
    """Full pipeline for one page. Returns dict with images + detections."""
    img = page_to_image(page, zoom)
    has_text = bool(page.get_text("words"))

    if has_text and not use_ocr:
        lines = get_lines(page, zoom)
        vendor = detect_vendor(page, zoom, img.shape[0])
    else:
        lines = ocr_lines(img)        # raises a clear error if tesseract missing
        vendor = None

    # If the text layer had no vendor (logo is likely an image), try OCR on the
    # logo region. Guarded so a missing Tesseract simply leaves vendor unset.
    if vendor is None:
        try:
            vendor = ocr_vendor(img)
        except Exception:
            vendor = None

    tables = detect_tables(img)
    detections = classify(lines, tables)
    # Vendor is the only purely-heuristic field, so only trust it when the
    # document actually looks like an invoice (some anchored field was found).
    anchors = {"invoice_number", "total", "tax", "tax_id", "bill_to", "ship_to"}
    has_anchor = any(d["type"] in anchors for d in detections)
    if vendor and has_anchor and not _inside_address(vendor["box"], detections):
        detections.insert(0, vendor)
    annotated = draw(img, detections, tables, show_labels=draw_labels)

    return {
        "original": img,
        "annotated": annotated,
        "detections": detections,
        "tables": tables,
        "used_ocr": (use_ocr or not has_text),
    }


def process_file(path, zoom=2.0, use_ocr=False, draw_labels=True,
                 work_dir="."):
    """Process every page of a PDF/DOCX. Returns a list of per-page results."""
    if path.lower().endswith(".docx"):
        path = docx_to_pdf(path, work_dir)
    doc = load_pdf(path)
    return [process_page(doc[i], zoom, use_ocr, draw_labels)
            for i in range(len(doc))]


def page_text(page, zoom=2.0, use_ocr=False):
    """Return the full plain text of a page, for the LLM extraction path.

    Uses the PDF text layer when present (accurate, no OCR). For scanned/image
    pages, or when use_ocr is forced, falls back to Tesseract OCR. Returns a
    tuple (text, used_ocr) so the UI can show which source produced it.
    """
    has_text = bool(page.get_text("words"))
    if has_text and not use_ocr:
        # Build the text from the SAME word boxes the rule-based engine reads,
        # so the LLM always gets text whenever the rule-based does. (Relying on
        # get_text("text") can return empty on some PDFs even when words exist,
        # which left Gemini with nothing while the boxes still worked.)
        txt = "\n".join(l["text"] for l in get_lines(page, zoom))
        if not txt.strip():                      # last-ditch fallback
            txt = page.get_text("text")
        if txt.strip():
            return txt, False
    img = page_to_image(page, zoom)
    lines = ocr_lines(img)                       # raises if Tesseract missing
    return "\n".join(l["text"] for l in lines), True


if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else "sample_invoice.pdf"
    results = process_file(src)
    for i, r in enumerate(results):
        cv2.imwrite(f"annotated_page_{i + 1}.png", r["annotated"])
        print(f"page {i+1}: {len(r['detections'])} fields, "
              f"{len(r['tables'])} table(s), ocr={r['used_ocr']}")
        for d in r["detections"]:
            print(f"   [{d['label']:>11}] {d['text'][:50]}")
