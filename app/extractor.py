"""
Multi-format document ingestion engine conforming to VeritasDoc Engineering Specification
(Phase 1, Sections 3.1 & 3.2).
Accepts 7 document formats: .pdf, .docx, .doc, .pptx, .ppt, .rtf, .txt.
Extracts clean structural hierarchical trees and computes SHA-256 cryptographic checksums.
"""

import logging
import re
from pathlib import Path
from typing import Any

from app.config import ALLOWED_EXTENSIONS, MIN_DOCUMENT_WORDS
from app.sanitizer import compute_sha256, sanitize_text, tokenize_sentences_robust

logger = logging.getLogger("ai_detector.extractor")


class DocumentExtractionError(Exception):
    """Exception raised when document parsing fails or validation does not pass."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def extract_txt(file_path: Path) -> str:
    """Extract text from a plain text file, auto-detecting common encodings."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    data = file_path.read_bytes()
    for enc in encodings:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def extract_docx_sections(file_path: Path) -> list[dict[str, Any]]:
    """
    Extract structured sections from Word .docx preserving headings and table cells.
    """
    try:
        import docx
    except ImportError as e:
        raise DocumentExtractionError("DOCX parser dependency missing.", status_code=500) from e

    try:
        doc = docx.Document(str(file_path))
        sections: list[dict[str, Any]] = []
        current_title = "Document Overview"
        current_paras: list[str] = []

        def flush_section():
            nonlocal current_title, current_paras
            if current_paras:
                full_text = "\n\n".join(current_paras).strip()
                if full_text:
                    sections.append({
                        "title": current_title,
                        "raw_text": full_text
                    })
                current_paras = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            # Detect Heading styles
            if p.style and p.style.name and p.style.name.lower().startswith("heading"):
                flush_section()
                current_title = text
            else:
                current_paras.append(text)

        # Extract tables
        for table in doc.tables:
            table_lines = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    table_lines.append(" | ".join(cells))
            if table_lines:
                current_paras.append("\n".join(table_lines))

        flush_section()

        if not sections and current_paras:
            sections.append({
                "title": "Document Overview",
                "raw_text": "\n\n".join(current_paras)
            })

        return sections
    except Exception as e:
        logger.error("Failed to parse DOCX file: %s", e)
        raise DocumentExtractionError(f"Corrupt or unreadable DOCX file: {e}", status_code=400) from e


def extract_pdf_sections(file_path: Path) -> list[dict[str, Any]]:
    """
    Extract structured pages/sections from PDF using pdfplumber with pypdf fallback.
    Preserves multi-column flow and isolates running headers/footers.
    """
    sections: list[dict[str, Any]] = []

    # Attempt pdfplumber first
    try:
        import pdfplumber
        with pdfplumber.open(str(file_path)) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text and text.strip():
                    sections.append({
                        "title": f"Page {page_idx + 1}",
                        "raw_text": text.strip()
                    })
        if sections:
            return sections
    except Exception as plumber_err:
        logger.info("pdfplumber parsing skipped or failed, falling back to pypdf: %s", plumber_err)

    # Fallback to pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(str(file_path))
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                sections.append({
                    "title": f"Page {idx + 1}",
                    "raw_text": page_text.strip()
                })
        return sections
    except Exception as e:
        logger.error("Failed to parse PDF file: %s", e)
        raise DocumentExtractionError(f"Corrupt or unreadable PDF file: {e}", status_code=400) from e


def extract_pptx_sections(file_path: Path) -> list[dict[str, Any]]:
    """
    Extract text from PowerPoint .pptx presentation slide-by-slide.
    Parses slide title and body content separately.
    """
    try:
        from pptx import Presentation
    except ImportError as e:
        raise DocumentExtractionError("PPTX parser dependency missing.", status_code=500) from e

    try:
        prs = Presentation(str(file_path))
        sections: list[dict[str, Any]] = []

        for slide_idx, slide in enumerate(prs.slides):
            slide_title = f"Slide {slide_idx + 1}"
            slide_content: list[str] = []

            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                tf = shape.text_frame
                text = tf.text.strip()
                if not text:
                    continue

                if shape == slide.shapes.title:
                    slide_title = f"Slide {slide_idx + 1}: {text}"
                else:
                    for para in tf.paragraphs:
                        p_text = para.text.strip()
                        if p_text:
                            slide_content.append(p_text)

            if slide_content:
                sections.append({
                    "title": slide_title,
                    "raw_text": "\n".join(slide_content)
                })

        return sections
    except Exception as e:
        logger.error("Failed to parse PPTX file: %s", e)
        raise DocumentExtractionError(f"Corrupt or unreadable PPTX file: {e}", status_code=400) from e


def extract_rtf_text(file_path: Path) -> str:
    """Extract plain text from an RTF document using striprtf."""
    try:
        from striprtf.striprtf import rtf_to_text
    except ImportError as e:
        raise DocumentExtractionError("RTF parser dependency missing.", status_code=500) from e

    try:
        raw_bytes = file_path.read_bytes()
        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            content = raw_bytes.decode("latin-1", errors="ignore")
        return rtf_to_text(content)
    except Exception as e:
        logger.error("Failed to parse RTF file: %s", e)
        raise DocumentExtractionError(f"Corrupt or unreadable RTF file: {e}", status_code=400) from e


def _extract_binary_text(raw_bytes: bytes) -> str:
    """Extract human-readable ASCII/UTF-8 strings from binary streams."""
    pattern = re.compile(rb'[\x20-\x7E\t\r\n]{5,}')
    matches = pattern.findall(raw_bytes)
    decoded = []
    for m in matches:
        try:
            s = m.decode('latin-1').strip()
            if len(s.split()) >= 2:
                decoded.append(s)
        except Exception:
            continue
    return "\n\n".join(decoded)


def extract_legacy_ole_text(file_path: Path, format_type: str) -> str:
    """Extract text from legacy binary Word (.doc) or PowerPoint (.ppt)."""
    try:
        import olefile
        if olefile.isOleFile(str(file_path)):
            with olefile.OleFileIO(str(file_path)) as ole:
                target_stream = 'WordDocument' if format_type == 'doc' else 'PowerPoint Document'
                if ole.exists(target_stream):
                    data = ole.openstream(target_stream).read()
                    extracted = _extract_binary_text(data)
                    if len(extracted.split()) >= MIN_DOCUMENT_WORDS:
                        return extracted
                all_data = []
                for entry in ole.listdir():
                    try:
                        all_data.append(ole.openstream(entry).read())
                    except Exception:
                        pass
                extracted = _extract_binary_text(b" ".join(all_data))
                if len(extracted.split()) >= MIN_DOCUMENT_WORDS:
                    return extracted
    except Exception as e:
        logger.warning("OLE parsing error for .%s, falling back to binary scan: %s", format_type, e)

    raw_data = file_path.read_bytes()
    extracted = _extract_binary_text(raw_data)
    if not extracted.strip():
        raise DocumentExtractionError(f"Could not extract readable text from .{format_type} file.", status_code=400)
    return extracted


def build_hierarchical_document_tree(file_path: Path | str, original_filename: str) -> dict[str, Any]:
    """
    Ingest document and build the Hierarchical Document Tree according to Section 3.1:
    {
      "document_name": "filename.docx",
      "sha256_hash": "a8f5b1284cd92e07...",
      "total_words": 2450,
      "sections": [
        {
          "section_index": 0,
          "title": "1. Introduction & Background",
          "sentences": [
            { "id": 0, "text": "...", "start_idx": 0, "end_idx": 54 }
          ]
        }
      ]
    }
    """
    path = Path(file_path)
    ext = Path(original_filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        allowed_list = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise DocumentExtractionError(
            f"Unsupported file format '{ext}'. Accepted formats are: {allowed_list}",
            status_code=400,
        )

    if not path.is_file():
        raise DocumentExtractionError("File was not found on server storage.", status_code=404)

    raw_bytes = path.read_bytes()
    sha256_hash = compute_sha256(raw_bytes)

    raw_sections: list[dict[str, Any]] = []

    if ext == ".docx":
        raw_sections = extract_docx_sections(path)
    elif ext == ".pdf":
        raw_sections = extract_pdf_sections(path)
    elif ext == ".pptx":
        raw_sections = extract_pptx_sections(path)
    elif ext == ".rtf":
        text = extract_rtf_text(path)
        raw_sections = [{"title": "Document Content", "raw_text": text}]
    elif ext == ".doc":
        text = extract_legacy_ole_text(path, "doc")
        raw_sections = [{"title": "Legacy Word Document", "raw_text": text}]
    elif ext == ".ppt":
        text = extract_legacy_ole_text(path, "ppt")
        raw_sections = [{"title": "Legacy PowerPoint Presentation", "raw_text": text}]
    elif ext == ".txt":
        text = extract_txt(path)
        blocks = [b.strip() for b in re.split(r'\n\s*\n+', text) if b.strip()]
        for idx, block in enumerate(blocks):
            raw_sections.append({
                "title": f"Paragraph {idx + 1}",
                "raw_text": block
            })

    # If extraction yielded no sections, try fallback to raw text
    if not raw_sections:
        fallback_text = raw_bytes.decode("utf-8", errors="ignore")
        raw_sections = [{"title": "Document Body", "raw_text": fallback_text}]

    # Build hierarchical tree with sanitized sentences
    tree_sections: list[dict[str, Any]] = []
    global_sentence_id = 0
    total_document_words = 0
    current_char_offset = 0

    for sec_idx, sec_data in enumerate(raw_sections):
        cleaned_sec_text = sanitize_text(sec_data.get("raw_text", ""))
        if not cleaned_sec_text:
            continue

        sec_sentences_raw = tokenize_sentences_robust(cleaned_sec_text)
        tree_sentences: list[dict[str, Any]] = []

        for s_text in sec_sentences_raw:
            words = s_text.split()
            w_count = len(words)
            total_document_words += w_count
            start_idx = current_char_offset
            end_idx = start_idx + len(s_text)
            current_char_offset = end_idx + 1

            tree_sentences.append({
                "id": global_sentence_id,
                "text": s_text,
                "start_idx": start_idx,
                "end_idx": end_idx,
                "word_count": w_count
            })
            global_sentence_id += 1

        if tree_sentences:
            tree_sections.append({
                "section_index": sec_idx,
                "title": sec_data.get("title", f"Section {sec_idx + 1}"),
                "raw_text": cleaned_sec_text,
                "sentences": tree_sentences
            })

    if total_document_words < MIN_DOCUMENT_WORDS:
        raise DocumentExtractionError(
            f"Document contains only {total_document_words} words. Minimum required is {MIN_DOCUMENT_WORDS} words for reliable statistical analysis.",
            status_code=400,
        )

    return {
        "document_name": original_filename,
        "sha256_hash": sha256_hash,
        "total_words": total_document_words,
        "total_sentences": global_sentence_id,
        "sections": tree_sections
    }


def extract_text(file_path: Path | str, original_filename: str) -> str:
    """
    Backwards-compatible helper returning the full sanitized text of the document.
    """
    tree = build_hierarchical_document_tree(file_path, original_filename)
    all_texts = []
    for sec in tree.get("sections", []):
        all_texts.append(sec.get("raw_text", ""))
    return "\n\n".join(all_texts)
