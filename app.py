"""
app.py – FastAPI server for the Livelihood Voice Assistant.

Routes:
  GET  /                → serves static/index.html
  POST /api/analyse     → accepts multipart form (text, audio transcript, image)
                          returns unified analysis JSON
  GET  /api/db/stats    → returns impact statistics from mock_database.json
  GET  /api/db/jobs     → returns all job opportunities
"""

import json
import logging
import os
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
import sys
sys.path.insert(0, str(Path(__file__).parent))

from backend.multimodal_gemma import extract_skill_profile
from backend.career_engine import analyse_career

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("livelihood.app")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Livelihood Voice Assistant API",
    description="Empowering informal workers with AI-powered skill profiles and career pathways.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"
DB_PATH    = Path(__file__).parent / "data" / "mock_database.json"

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ---------------------------------------------------------------------------
# Root – serve SPA
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"status": "Livelihood Assistant API running. Static dir not found."})


# ---------------------------------------------------------------------------
# /api/analyse  – The core endpoint
# ---------------------------------------------------------------------------
@app.post("/api/analyse")
async def analyse(
    text_input : str             = Form(default=""),
    transcript : str             = Form(default=""),
    image      : UploadFile      = File(default=None),
):
    """
    Accept voice transcript, image upload, and/or text input.
    Returns a unified JSON with skill_profile + career analysis.
    """
    if not text_input and not transcript and not image:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one input: text, transcript, or image.",
        )

    # Save uploaded image to a temp file if present
    image_path: str | None = None
    tmp_path: Path | None  = None

    if image and image.filename:
        suffix    = Path(image.filename).suffix or ".jpg"
        tmp       = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        shutil.copyfileobj(image.file, tmp)
        tmp.close()
        image_path = tmp.name
        tmp_path   = Path(tmp.name)
        logger.info(f"Image saved to temp: {image_path}")

    try:
        # Step 1 – Extract skill profile via Gemma 4
        profile = extract_skill_profile(
            transcript  = transcript  or None,
            image_path  = image_path  or None,
            text_input  = text_input  or None,
        )

        # Step 2 – Career analysis
        analysis = analyse_career(profile)

        return JSONResponse({
            "success"      : True,
            "skill_profile": profile,
            "analysis"     : analysis,
        })

    except Exception as exc:
        logger.exception(f"Analysis failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    finally:
        # Cleanup temp image
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


# ---------------------------------------------------------------------------
# /api/db/stats
# ---------------------------------------------------------------------------
@app.get("/api/db/stats")
async def db_stats():
    """Return impact statistics from the mock database."""
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)
        return JSONResponse(db.get("impact_statistics", {}))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Database not found.")


# ---------------------------------------------------------------------------
# /api/db/jobs
# ---------------------------------------------------------------------------
@app.get("/api/db/jobs")
async def db_jobs():
    """Return all job opportunities."""
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)
        return JSONResponse(db.get("job_opportunities", []))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Database not found.")


# ---------------------------------------------------------------------------
# /api/demo  – return pre-built analysis for UI demo / judging
# ---------------------------------------------------------------------------
@app.get("/api/demo")
async def demo(profile_type: str = "carpenter"):
    """Return a fully pre-computed demo result for rapid judging."""
    from backend.multimodal_gemma import _mock_extract
    profile  = _mock_extract(None, None, profile_type)
    analysis = analyse_career(profile)
    return JSONResponse({
        "success"      : True,
        "skill_profile": profile,
        "analysis"     : analysis,
    })


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Livelihood Assistant on http://localhost:{port}")
    uvicorn.run(
        "app:app",
        host     = "0.0.0.0",
        port     = port,
        reload   = True,
        log_level= "info",
    )
