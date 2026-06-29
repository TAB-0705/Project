"""
llm_extract.py
--------------
LLM-based invoice field extraction using **LangChain + Google Gemini**.

This is the "AI extraction" path that sits beside the rule-based engine in
invoice_processor.py. It takes the raw text of an invoice (from the PDF text
layer, or from Tesseract OCR for scanned/image invoices) and asks Gemini to
return a clean, validated record via LangChain's structured-output support.

Why this design:
  * Satisfies the "extract with LangChain/LlamaIndex" requirement.
  * Pairs naturally with the rule-based engine so the demo can show
    BOTH approaches on the same invoice (rules = boxes + precision,
    LLM = robust on layouts the rules have never seen).
  * Uses Gemini's FREE tier -> no credit card, no paid subscription.

Get a free API key (no card): https://aistudio.google.com/  ->  "Get API key"

Install:
    python -m pip install langchain langchain-google-genai
"""

from typing import List
from pydantic import BaseModel, Field

# Gemini's free tier. As of mid-2026 the free lineup is the 2.5 family
# (2.0-flash was moved OFF the free tier -> "limit: 0" 429 errors). If a name
# ever stops working, try "gemini-2.5-flash-lite" (higher free quota) or check
# https://ai.google.dev/gemini-api/docs/rate-limits for the current free models.
DEFAULT_MODEL = "gemini-2.5-flash"


class ExtractedField(BaseModel):
    """One labelled field found on the invoice."""
    name: str = Field(
        description="The field's label in Title Case, e.g. 'Invoice Number', "
        "'Date', 'Total', 'Vendor', 'Cashier', 'Manager', 'Server', 'Table No', "
        "'Payment Method', 'GST Number', 'Bill To', 'Due Date'.")
    value: str = Field(
        description="The value for this field, exactly as written in the document "
        "(keep currency symbols on money values).")


class InvoiceData(BaseModel):
    """Adaptive result: only the fields that THIS invoice actually contains.

    The set of fields varies per document — a restaurant receipt may have a
    Cashier or Server, a corporate invoice may have a Manager or PO Number —
    so we let the model return a dynamic list rather than a fixed schema.
    """
    fields: List[ExtractedField] = Field(
        description="Every labelled field that ACTUALLY appears on this specific "
        "invoice/receipt, in the order they appear. Always include these core "
        "fields WHEN PRESENT: Invoice Number, Date, Total, Vendor. Also include "
        "any other labelled detail the document shows — e.g. Cashier, Manager, "
        "Server, Table No, Payment Method, Tax/GST Number, Bill To, Ship To, "
        "Subtotal, Due Date, Terms. CRITICAL: include a field ONLY if it is "
        "genuinely present in the text. NEVER output empty, placeholder, or "
        "'N/A' values, and NEVER invent a field that is not in the document. So "
        "a receipt with a cashier shows a Cashier field and NO Manager field; a "
        "different invoice with a manager shows a Manager field and NO Cashier.")


_PROMPT = (
    "You are a precise invoice/receipt data-extraction system. Read the document "
    "text below and return the labelled fields it contains.\n"
    "Rules:\n"
    " - Use ONLY what literally appears in the document. Do not guess or invent.\n"
    " - Adapt to THIS document: return the fields it actually has. Different "
    "receipts have different fields (one has a Cashier, another a Manager) — "
    "reflect that. Do NOT add a field that isn't present, and do NOT pad with "
    "empty or 'N/A' values.\n"
    " - Always capture the core fields when present: Invoice Number, Date, "
    "Total, Vendor.\n"
    " - The vendor is the party that ISSUED the document (seller), not the "
    "bill-to party (customer).\n"
    " - Keep currency symbols on money values.\n\n"
    "DOCUMENT TEXT:\n"
    "-----------------\n"
    "{text}\n"
    "-----------------"
)


def extract_invoice(text, api_key, model=DEFAULT_MODEL):
    """Run LangChain + Gemini structured extraction.

    Returns (InvoiceData, None) on success, or (None, error_message) on
    failure. Imports happen inside the function so the rest of the app keeps
    working even before langchain is installed.
    """
    if not text or not text.strip():
        return None, "No text to extract from (empty page?)."
    if not api_key:
        return None, ("No Gemini API key provided. Get a free one at "
                      "https://aistudio.google.com/ and paste it in the sidebar.")

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        return None, ("LangChain isn't installed yet. Run:\n"
                      "    python -m pip install langchain langchain-google-genai")

    try:
        # thinking_budget=0 disables Gemini 2.5's reasoning step (not needed for
        # extraction). timeout + low max_retries stop the call from hanging for a
        # long time when the free tier is rate-limited — it fails fast instead.
        common = dict(model=model, google_api_key=api_key, temperature=0,
                      timeout=45, max_retries=1)
        try:
            llm = ChatGoogleGenerativeAI(thinking_budget=0, **common)
        except Exception:
            llm = ChatGoogleGenerativeAI(**common)
        structured_llm = llm.with_structured_output(InvoiceData)
        # Truncate very long invoices to stay comfortably inside free limits.
        result = structured_llm.invoke(_PROMPT.format(text=text[:12000]))
        return result, None
    except Exception as e:
        msg = str(e)
        if "API_KEY" in msg or "API key" in msg or "PERMISSION_DENIED" in msg:
            return None, f"API key problem: {msg}"
        if "limit: 0" in msg or "FreeTier" in msg:
            return None, ("This model has NO free-tier quota (limit: 0) — it's "
                          "likely been moved off the free tier. Edit DEFAULT_MODEL "
                          "in llm_extract.py to a current free model such as "
                          f"'gemini-2.5-flash' or 'gemini-2.5-flash-lite'. ({msg})")
        if "quota" in msg.lower() or "429" in msg:
            return None, (f"Rate limited (free tier per-minute/day cap). Wait a "
                          f"moment and retry, or switch to 'gemini-2.5-flash-lite' "
                          f"for higher quota. ({msg})")
        if "timeout" in msg.lower() or "deadline" in msg.lower():
            return None, ("Gemini took too long (timed out) — usually free-tier "
                          f"congestion. Wait a few seconds and retry. ({msg})")
        return None, f"LLM extraction failed: {msg}"


# Quick CLI test:  python llm_extract.py  (reads sample_invoice.pdf)
if __name__ == "__main__":
    import os
    import sys
    import invoice_processor as ip

    src = sys.argv[1] if len(sys.argv) > 1 else "sample_invoice.pdf"
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    doc = ip.load_pdf(src)
    text, used_ocr = ip.page_text(doc[0])
    print(f"--- extracted text from {src} (ocr={used_ocr}) ---")
    data, err = extract_invoice(text, key)
    if err:
        print("ERROR:", err)
    else:
        for fld in data.fields:
            print(f"  {fld.name:>18}: {fld.value}")
