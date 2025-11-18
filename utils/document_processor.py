# utils/document_processor.py
# Extraction robuste + chunking structure-aware (FR/EN) + chunking BCBS par principes

import io
import os
import re
from typing import List, Dict, Tuple

from pypdf import PdfReader
import docx
import pandas as pd

from config import CHUNK_SIZE, CHUNK_OVERLAP

# Optional better PDF text engine (PyMuPDF). If missing, we fallback to pypdf.
try:
    import fitz  # PyMuPDF

    HAS_PYMUPDF = True
except Exception:
    HAS_PYMUPDF = False


# -----------------------
# Extraction
# -----------------------
def extract_text_from_file(uploaded_file, filename: str) -> str:
    name = filename.lower()
    data = uploaded_file.read()
    return _extract_bytes(data, name)


def _extract_bytes(bytes_data: bytes, filename_lower: str) -> str:
    if filename_lower.endswith(".pdf"):
        txt = _pdf_to_text_pypdf(bytes_data)
        if _looks_bad(txt) and HAS_PYMUPDF:
            alt = _pdf_to_text_pymupdf(bytes_data)
            if alt:
                txt = alt
        return txt
    if filename_lower.endswith(".docx"):
        return _docx_to_text(bytes_data)
    if filename_lower.endswith(".csv"):
        return _csv_to_text(bytes_data)
    if filename_lower.endswith((".txt", ".md")):
        try:
            return bytes_data.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    try:
        return bytes_data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _pdf_to_text_pypdf(bytes_data: bytes) -> str:
    out = []
    try:
        reader = PdfReader(io.BytesIO(bytes_data))
        for p in reader.pages:
            try:
                out.append(p.extract_text() or "")
            except Exception:
                pass
    except Exception:
        return ""
    return "\n".join(out)


def _pdf_to_text_pymupdf(bytes_data: bytes) -> str:
    try:
        doc = fitz.open(stream=bytes_data, filetype="pdf")
        out = []
        for page in doc:
            out.append(page.get_text("text"))
        return "\n".join(out)
    except Exception:
        return ""


def _docx_to_text(bytes_data: bytes) -> str:
    f = io.BytesIO(bytes_data)
    d = docx.Document(f)
    return "\n".join([p.text for p in d.paragraphs])


def _csv_to_text(bytes_data: bytes) -> str:
    f = io.BytesIO(bytes_data)
    df = pd.read_csv(f)
    return df.to_csv(index=False)


def _looks_bad(txt: str) -> bool:
    if not txt:
        return True
    return (len(txt) < 200) or (txt.count(" ") < len(txt) * 0.05)


# -----------------------
# Structure-aware chunking
# -----------------------
TITLE_PATTERNS = [
    r"(bcbs\s+principle)\s+\d{1,2}\b.*",          # ex: "BCBS Principle 3: Accuracy and integrity"
    r"(principle|principe)\s+\d{1,2}\b.*",        # ex: "Principle 3 – Accuracy and integrity"
    r"(article|art\.)\s+\d+[a-z]?\b.*",
    r"(section)\s+\d+(?:\.\d+)*\b.*",
    r"(chapter|chapitre)\s+\d+(?:\.\d+)*\b.*",
    r"(annex|annexe|appendix|appendice)\b.*",
    r"(requirement|exigence)\b.*",
    r"(policy|politique)\b.*",
    r"(guideline|lignes? directrices?|directive)\b.*",
    r"(scope|p[ée]rim[èe]tre)\b.*",
    r"(definitions?|d[ée]finitions?)\b.*",
    r"(objective|objectif[s]?)\b.*",
    r"(control[s]?|contr[ôo]le[s]?)\b.*",
]

TITLE_RX = re.compile(rf"^\s*((?:{'|'.join(TITLE_PATTERNS)}))\s*$", re.IGNORECASE)


def _split_by_headings(text: str) -> List[Tuple[str, str]]:
    """Split text into (title, body) blocks by generic headings."""
    lines = (text or "").splitlines()
    blocks: List[Tuple[str, str]] = []
    cur_title, cur_buf = None, []
    for ln in lines:
        if TITLE_RX.match(ln.strip()):
            if cur_title or cur_buf:
                blocks.append((cur_title, "\n".join(cur_buf).strip()))
            cur_title, cur_buf = ln.strip(), []
        else:
            cur_buf.append(ln)
    if cur_title or cur_buf:
        blocks.append((cur_title, "\n".join(cur_buf).strip()))
    return blocks


def _merge_small_blocks(blocks: List[Tuple[str, str]], min_chars: int = 600) -> List[Tuple[str, str]]:
    """Merge too-small sections with their successor to avoid micro-chunks."""
    if not blocks:
        return []
    merged: List[Tuple[str, str]] = []
    buffer_title, buffer_body = None, ""
    for title, body in blocks:
        txt = ((title + "\n") if title else "") + (body or "")
        if buffer_title is None:
            buffer_title, buffer_body = title, body
            continue
        prev_txt = ((buffer_title + "\n") if buffer_title else "") + (buffer_body or "")
        if len(prev_txt) < min_chars:
            new_title = buffer_title or title
            new_body = (buffer_body + "\n\n" + txt).strip()
            buffer_title, buffer_body = new_title, new_body
        else:
            merged.append((buffer_title, buffer_body))
            buffer_title, buffer_body = title, body
    if buffer_title is not None or buffer_body:
        merged.append((buffer_title, buffer_body))
    return merged


def chunk_documents_by_headings(
    text: str,
    source_name: str,
    max_chars: int = CHUNK_SIZE,
    hard_overlap: int = CHUNK_OVERLAP,
    min_section_chars: int = 600,
) -> List[Dict]:
    """
    1) Split by structural headings (FR/EN)
    2) Merge tiny blocks
    3) Enforce max_chars with sliding window (hard cap)
    """
    if not text:
        return []
    raw_blocks = _split_by_headings(_normalize_text(text))
    blocks = _merge_small_blocks(raw_blocks, min_chars=min_section_chars)

    chunks: List[Dict] = []
    idx = 0
    for title, body in blocks:
        full = ((title + "\n") if title else "") + (body or "")
        if not full.strip():
            continue
        start = 0
        while start < len(full):
            end = min(start + max_chars, len(full))
            piece = full[start:end]
            chunks.append({"text": piece, "metadata": {"source": source_name, "chunk": idx}})
            idx += 1
            if end == len(full):
                break
            start = max(end - hard_overlap, start + 1)
    return chunks or chunk_documents(text, source_name)


def chunk_documents(
    text: str,
    source_name: str,
    size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[Dict]:
    chunks: List[Dict] = []
    if not text:
        return chunks
    t = _normalize_text(text)
    n, start, i = len(t), 0, 0
    while start < n:
        end = min(start + size, n)
        piece = t[start:end]
        chunks.append({"text": piece, "metadata": {"source": source_name, "chunk": i}})
        i += 1
        start = end if overlap <= 0 else min(end, max(end - overlap, start + 1))
    return chunks


# ---------- Chunking spécial BCBS239 ----------
def chunk_bcbs_principles(
    text: str,
    source_name: str,
    max_chars: int = 2200,
    overlap: int = 200,
) -> List[Dict]:
    """
    Chunking spécial pour BCBS239 :
    - découpe par 'Principle X' / 'Principe X' / 'BCBS Principle X'
    - chaque principe est un bloc, éventuellement re-splitté s'il est trop long
    - si aucun heading BCBS n'est trouvé, fallback vers chunking par headings génériques
    """
    if not text:
        return []

    t = _normalize_text(text)

    heading_rx = re.compile(
        r"^(?:BCBS\s+)?(Principle|Principe)\s+\d{1,2}\b.*",
        re.IGNORECASE | re.MULTILINE,
    )

    matches = list(heading_rx.finditer(t))
    if not matches:
        # Certains docs (comme RDARR) ne sont pas structurés par principe :
        return chunk_documents_by_headings(text, source_name)

    chunks: List[Dict] = []
    idx = 0

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(t)
        section = t[start:end].strip()
        if not section:
            continue

        if len(section) <= max_chars:
            chunks.append({"text": section, "metadata": {"source": source_name, "chunk": idx}})
            idx += 1
        else:
            s = 0
            while s < len(section):
                e = min(s + max_chars, len(section))
                piece = section[s:e]
                chunks.append({"text": piece, "metadata": {"source": source_name, "chunk": idx}})
                idx += 1
                if e == len(section):
                    break
                s = max(e - overlap, s + 1)

    return chunks or chunk_documents_by_headings(text, source_name)


# -----------------------
# Utilities
# -----------------------
def _normalize_text(t: str) -> str:
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t


def format_citations(sources):
    """
    sources peut être :
      - une liste de str (ancienne version)
      - ou une liste de dicts {label, snippet} (nouvelle version RAG)
    """
    if not sources:
        return ""
    lines = []
    for s in sources:
        if isinstance(s, str):
            lines.append(f"- {s}")
        elif isinstance(s, dict):
            label = s.get("label", "")
            snippet = s.get("snippet", "")
            if snippet:
                lines.append(f"- **{label}** — “{snippet}”")
            else:
                lines.append(f"- {label}")
        else:
            lines.append(f"- {str(s)}")
    return "\n".join(lines)


def load_documents_from_folder(folder_path: str):
    docs = []
    for root, _, files in os.walk(folder_path):
        for fn in files:
            ext = fn.lower()
            if not any(ext.endswith(x) for x in (".pdf", ".docx", ".csv", ".txt", ".md")):
                continue
            p = os.path.join(root, fn)
            with open(p, "rb") as f:
                data = f.read()
            text = _extract_bytes(data, ext)
            docs.append({"filename": fn, "text": text})
    return docs
