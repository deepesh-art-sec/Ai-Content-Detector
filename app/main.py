"""
FastAPI application entrypoint for VeritasDoc AI Content Detector & Plagiarism Suite.
Coordinates routes for health, file upload analysis, recalculation, history,
tamper-evident PDF reports, LMS webhooks, and static frontend assets.
"""

import datetime
import logging
import os
import shutil
import sqlite3
import threading
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.analyzer import analyze_text
from app.config import (
    ALLOWED_EXTENSIONS,
    MAX_UPLOAD_BYTES,
    MAX_UPLOAD_MB,
    STATIC_DIR,
    UPLOADS_DIR,
)
from app.database import (
    delete_analysis,
    get_analysis,
    init_db,
    insert_analysis,
    list_analyses,
)
from app.detector import (
    ModelInferenceError,
    ModelUnavailableError,
    get_model_status,
    load_detection_model,
)
from app.extractor import (
    DocumentExtractionError,
    build_hierarchical_document_tree,
    extract_text,
)
from app.reporter import generate_pdf_report

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("veritasdoc.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes database and kicks off background warm-up of detection models.
    """
    logger.info("Initializing VeritasDoc database...")
    init_db()

    logger.info("Starting background model loading...")
    load_thread = threading.Thread(
        target=load_detection_model,
        name="ModelLoaderThread",
        daemon=True,
    )
    load_thread.start()

    yield
    logger.info("VeritasDoc shutting down.")


app = FastAPI(
    title="VeritasDoc AI Content & Plagiarism Detector",
    description="Multi-tier forensic system designed for academic and professional evaluators.",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for cross-origin evaluator clients / LMS extensions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecalculateRequest(BaseModel):
    text: str
    sensitivity: str = "balanced"
    esl_safeguard: bool = True


class LMSWebhookRequest(BaseModel):
    submission_id: str
    student_id: str
    assignment_title: str
    text: str
    sensitivity: str = "balanced"
    esl_safeguard: bool = True


@app.get("/health")
async def health_check():
    """Health check endpoint reporting server and model status."""
    status_info = get_model_status()
    loaded = status_info["model_loaded"]
    return {
        "status": "ok" if loaded else "degraded",
        "model": status_info["model_name"] if loaded else "none",
        "model_loaded": loaded,
        "device": status_info["device"],
        "model_type": status_info["model_type"],
    }


@app.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    sensitivity: str = Form("balanced"),
    esl_safeguard: bool = Form(True)
):
    """
    Upload and analyze a document (.txt, .docx, .pdf, .rtf, .pptx, .ppt, .doc).
    Extracts text, segments sentences & sections into Hierarchical Document Tree,
    computes SHA-256 hash, runs batch inference with Gaussian smoothing and length-weighted attribution,
    persists in SQLite, and returns comprehensive scoring.
    """
    filename = file.filename or "uploaded_document"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed_list = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Accepted formats: {allowed_list}",
        )

    model_status = get_model_status()
    if not model_status["model_loaded"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Forensic neural consensus engine initializing. Please wait a moment.",
        )

    analysis_id = str(uuid.uuid4())
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
    target_path = UPLOADS_DIR / f"{analysis_id}_{safe_name}"

    total_bytes = 0
    try:
        with open(target_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    buffer.close()
                    target_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_MB}MB.",
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        target_path.unlink(missing_ok=True)
        logger.error("File upload save failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file to disk.",
        ) from e

    # Build Hierarchical Document Tree (Phase 1, Section 3.1)
    try:
        doc_tree = build_hierarchical_document_tree(target_path, filename)
        # Extract combined sanitized text
        extracted_text = "\n\n".join(sec.get("raw_text", "") for sec in doc_tree.get("sections", []))
    except DocumentExtractionError as e:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    except Exception as e:
        target_path.unlink(missing_ok=True)
        logger.error("Unexpected error in text extraction: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract text from the uploaded document.",
        ) from e

    # Run VeritasDoc end-to-end analysis
    try:
        analysis_data = analyze_text(
            text=extracted_text,
            sensitivity=sensitivity,
            esl_safeguard=esl_safeguard,
            doc_tree=doc_tree
        )
    except ModelUnavailableError as e:
        target_path.unlink(missing_ok=True)
        raise HTTPException(status_code=e.status_code, detail=e.message) from e
    except ModelInferenceError as e:
        target_path.unlink(missing_ok=True)
        logger.exception("Inference failed for analysis %s: %s", analysis_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during model inference.",
        ) from e
    except Exception as e:
        target_path.unlink(missing_ok=True)
        logger.exception("Unexpected analysis error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while analyzing the document text.",
        ) from e

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = {
        "id": analysis_id,
        "filename": filename,
        "file_path": str(target_path),
        "sha256_hash": doc_tree.get("sha256_hash", ""),
        "verdict": analysis_data["verdict"],
        "verdict_zone": analysis_data.get("verdict_zone", "GREEN"),
        "ai_percentage": analysis_data["ai_percentage"],
        "total_sentences": analysis_data["total_sentences"],
        "ai_sentences": analysis_data["ai_sentences"],
        "total_words": analysis_data.get("total_words", 0),
        "total_chars": analysis_data.get("total_chars", 0),
        "sensitivity_mode": sensitivity,
        "threshold_tau": analysis_data.get("threshold_tau", 0.60),
        "is_short_text": analysis_data.get("is_short_text", False),
        "model_used": analysis_data["model_used"],
        "sentences": analysis_data["sentences"],
        "sections": analysis_data.get("sections", []),
        "attribution": analysis_data.get("attribution", {}),
        "evasion": analysis_data.get("evasion", {}),
        "plagiarism": analysis_data.get("plagiarism", {}),
        "ensemble": analysis_data.get("ensemble", {}),
        "forensic_metrics": analysis_data.get("forensic_metrics", {}),
        "esl_guardrail": analysis_data.get("esl_guardrail", {}),
        "multilingual": analysis_data.get("multilingual", {}),
        "created_at": now_iso,
    }

    try:
        insert_analysis(record)
    except Exception as e:
        logger.error("Failed to persist analysis to database: %s", e)

    return record


@app.post("/recalculate")
def recalculate_analysis(req: RecalculateRequest):
    """
    Real-time dynamic re-calculation endpoint.
    Allows frontend sensitivity toggles (Conservative 75%, Balanced 60%, Aggressive 45%)
    and ESL Safeguard ON/OFF without re-uploading the document!
    """
    model_status = get_model_status()
    if not model_status["model_loaded"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Engine initializing. Please wait.",
        )

    try:
        analysis_data = analyze_text(
            text=req.text,
            sensitivity=req.sensitivity,
            esl_safeguard=req.esl_safeguard,
        )
        return analysis_data
    except Exception as e:
        logger.error("Recalculate failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/lms/webhook")
def lms_webhook_ingest(payload: LMSWebhookRequest):
    """
    Phase 7, Bonus 3: LMS Webhook (Canvas / Moodle integration).
    Receives automated student assignment submission payload and returns instant audit verification.
    """
    model_status = get_model_status()
    if not model_status["model_loaded"]:
        raise HTTPException(status_code=503, detail="Forensic engine initializing.")

    analysis_data = analyze_text(
        text=payload.text,
        sensitivity=payload.sensitivity,
        esl_safeguard=payload.esl_safeguard
    )

    analysis_id = str(uuid.uuid4())
    record = {
        "id": analysis_id,
        "filename": f"{payload.assignment_title}_{payload.submission_id}.txt",
        "file_path": "",
        "sha256_hash": "",
        "verdict": analysis_data["verdict"],
        "verdict_zone": analysis_data["verdict_zone"],
        "ai_percentage": analysis_data["ai_percentage"],
        "total_sentences": analysis_data["total_sentences"],
        "ai_sentences": analysis_data["ai_sentences"],
        "total_words": analysis_data["total_words"],
        "sensitivity_mode": payload.sensitivity,
        "model_used": analysis_data["model_used"],
        "sentences": analysis_data["sentences"],
        "sections": analysis_data["sections"],
        "attribution": analysis_data["attribution"],
        "evasion": analysis_data["evasion"],
        "plagiarism": analysis_data["plagiarism"],
        "ensemble": analysis_data["ensemble"],
        "forensic_metrics": analysis_data["forensic_metrics"],
        "esl_guardrail": analysis_data["esl_guardrail"],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    insert_analysis(record)

    return {
        "status": "success",
        "submission_id": payload.submission_id,
        "student_id": payload.student_id,
        "verdict": analysis_data["verdict"],
        "verdict_zone": analysis_data["verdict_zone"],
        "ai_percentage": analysis_data["ai_percentage"],
        "certificate_id": analysis_id,
        "audit_report_url": f"/history/{analysis_id}/pdf"
    }


@app.get("/history")
async def get_history():
    """Retrieve historical analysis summaries, ordered newest first."""
    try:
        return list_analyses()
    except Exception as e:
        logger.error("Failed to retrieve history: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load analysis history.",
        ) from e


@app.get("/history/{analysis_id}")
def get_history_item(analysis_id: str):
    """Retrieve full analysis report including individual sentence evaluations and forensic audits."""
    try:
        item = get_analysis(analysis_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis with ID '{analysis_id}' was not found.",
            )
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve analysis '%s': %s", analysis_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load analysis record.",
        ) from e


@app.get("/history/{analysis_id}/pdf")
def get_analysis_pdf(analysis_id: str):
    """
    Generate and download a formal PDF audit report certificate for an analysis.
    """
    item = get_analysis(analysis_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' was not found.",
        )

    try:
        pdf_bytes = generate_pdf_report(item)
    except Exception as e:
        logger.exception("Failed to render PDF report: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to render PDF audit report.",
        ) from e

    safe_filename = "".join(c for c in Path(item["filename"]).stem if c.isalnum() or c in "_-")
    download_name = f"VeritasDoc_Audit_{safe_filename or 'document'}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
            "Content-Type": "application/pdf",
        },
    )


@app.delete("/history/{analysis_id}")
def delete_history_item(analysis_id: str):
    """Delete an analysis record from SQLite and remove the uploaded file from disk."""
    try:
        deleted = delete_analysis(analysis_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis with ID '{analysis_id}' was not found.",
            )

        file_path_str = deleted.get("file_path")
        if file_path_str:
            file_path = Path(file_path_str)
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception as file_err:
                    logger.warning("Could not delete file %s: %s", file_path, file_err)

        return {
            "success": True,
            "id": analysis_id,
            "message": "Analysis and associated file deleted successfully.",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete analysis '%s': %s", analysis_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete analysis record.",
        ) from e


# Mount static assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_frontend():
    """Serve the single-page application frontend."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend static index.html not found.")
    return FileResponse(str(index_file))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
