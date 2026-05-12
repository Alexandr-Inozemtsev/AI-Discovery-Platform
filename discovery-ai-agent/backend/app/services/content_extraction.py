from __future__ import annotations

from io import BytesIO
from docx import Document


def _decode_text(content: bytes) -> str:
    for enc in ("utf-8", "cp1251"):
        try:
            return content.decode(enc)
        except Exception:
            continue
    return ""


def _split_chunks(text: str, chunk_size: int = 2500, max_chunks: int = 10) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    out: list[str] = []
    for i in range(0, len(text), chunk_size):
        out.append(text[i : i + chunk_size])
        if len(out) >= max_chunks:
            break
    return out


def extract_text_from_upload(filename: str, content: bytes, mime_type: str | None = None) -> dict:
    ext = (filename or "").lower().split(".")[-1] if "." in (filename or "") else ""
    if ext == "txt" or (mime_type or "").startswith("text/plain"):
        text = _decode_text(content)
        return {"text": text, "status": "completed" if text.strip() else "empty", "error": None, "chunks": _split_chunks(text)}
    if ext == "docx":
        try:
            doc = Document(BytesIO(content))
            text = "\n".join([p.text for p in doc.paragraphs if (p.text or "").strip()])
            return {"text": text, "status": "completed" if text.strip() else "empty", "error": None, "chunks": _split_chunks(text)}
        except Exception as e:
            return {"text": "", "status": "failed", "error": str(e), "chunks": []}
    if ext == "pdf":
        return {"text": "", "status": "unsupported", "error": "PDF text extraction is not implemented yet", "chunks": []}
    if ext in {"xlsx", "xls"}:
        return {"text": "", "status": "unsupported", "error": "XLSX text extraction is not implemented yet", "chunks": []}
    return {"text": "", "status": "unsupported", "error": f"Unsupported file type: {ext or 'unknown'}", "chunks": []}
