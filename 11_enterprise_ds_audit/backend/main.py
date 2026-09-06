"""Enterprise DS Audit API."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.auditor import extract_zip_to_temp, resolve_project_path, run_audit  # noqa: E402
from app.config import ARTIFACTS_DIR, DIMENSION_LABELS, DIMENSIONS, PORT, UPLOAD_DIR  # noqa: E402
from app.schemas import AuditRequest, AuditResponse  # noqa: E402

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Enterprise DS Audit",
    description="Static-analysis auditor for data science project quality & leakage risks",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True, "port": PORT, "service": "enterprise-ds-audit"}


@app.get("/dimensions")
def dimensions():
    return {
        "dimensions": [{"id": d, "label": DIMENSION_LABELS[d]} for d in DIMENSIONS]
    }


@app.post("/audit", response_model=AuditResponse)
def audit_path(req: AuditRequest):
    try:
        root = resolve_project_path(req.path)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e)) from e
    except NotADirectoryError as e:
        raise HTTPException(400, str(e)) from e
    except PermissionError as e:
        raise HTTPException(403, str(e)) from e
    return run_audit(root)


@app.post("/audit/upload", response_model=AuditResponse)
async def audit_upload(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(400, "Upload a .zip archive of the project")
    data = await file.read()
    if len(data) > 80 * 1024 * 1024:
        raise HTTPException(400, "Zip exceeds 80 MB limit")
    try:
        root = extract_zip_to_temp(data)
    except (zipfile.BadZipFile, ValueError, OSError) as e:
        raise HTTPException(400, f"Invalid zip: {e}") from e
    return run_audit(root)
