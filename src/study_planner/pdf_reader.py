import json
import re
from io import BytesIO


def pdf_text(pdf):
    from pypdf import PdfReader
    if isinstance(pdf, (bytes, bytearray)):
        pdf = BytesIO(pdf)
    text = '\n'.join(page.extract_text() or '' for page in PdfReader(pdf).pages).strip()
    if not text:
        raise ValueError('No PDF text found. Scanned PDFs need OCR.')
    return text


def parse_json(text):
    if not isinstance(text, str):
        raise ValueError('Expected model text')
    text = re.sub(r'```(?:json)?', '', text)
    start, end = text.find('{'), text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError('No JSON object found')
    result = json.loads(text[start:end + 1])
    if not isinstance(result, dict):
        raise ValueError('Expected a JSON object')
    return result
