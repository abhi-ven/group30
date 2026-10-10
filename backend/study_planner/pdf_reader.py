"""Read PDF text and clean up model JSON. Works with what Streamlit gives you."""
import json
import re
from io import BytesIO


def pdf_text(pdf):
    """pdf can be a file path, raw bytes, or a file-like object
    (such as the object returned by st.file_uploader)."""
    from pypdf import PdfReader
    if isinstance(pdf, (bytes, bytearray)):
        pdf = BytesIO(pdf)
    pages = PdfReader(pdf).pages
    text = "\n".join((page.extract_text() or "") for page in pages).strip()
    if not text:
        raise ValueError("No text found in the PDF (it may be a scanned image).")
    return text


def parse_json(text):
    """Strip code fences / chatter and return the JSON object inside."""
    text = re.sub(r"```(?:json)?", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON found in model output")
    return json.loads(text[start:end + 1])
