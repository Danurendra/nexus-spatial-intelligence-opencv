"""FastAPI service for Nexus Spatial Intelligence video analysis.

Provides REST API endpoints:
- GET /health: Service health status
- POST /analyze: Upload and analyze video
"""

import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
import os

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import cv2

from src.main import analyze_video
from src.s3_storage import create_s3_storage_client
from src.vision_agent import VisionAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MAX_UPLOAD_SIZE_MB = 100  # 100 MB max file size
ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.flv'}

# Initialize S3 storage client (loaded from environment variables)
s3_storage = create_s3_storage_client()

# Initialize Vision Agent
vision_agent = VisionAgent()

app = FastAPI(
    title="Nexus Spatial Intelligence API",
    description="Video analysis platform for OpenCV AI Competition 2026",
    version="0.3.0"
)

# Add CORS middleware for browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        JSON with service status and version information
    """
    return {
        "status": "healthy",
        "service": "Nexus Spatial Intelligence",
        "api_version": "0.2.0",
        "opencv_version": cv2.__version__,
        "s3_storage_enabled": s3_storage.is_enabled(),
    }


@app.post("/analyze")
async def analyze_uploaded_video(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload and analyze a video file.
    
    Args:
        file: Video file to analyze
        
    Returns:
        JSON response with run ID, status, results, and artifact paths
        
    Raises:
        HTTPException: If file is invalid, too large, or processing fails
    """
    
    # Validation: File name
    if not file.filename:
        logger.warning("Upload attempt with empty filename")
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )
    
    # Validation: File extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        logger.warning(f"Upload rejected: unsupported file type {file_ext}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Create temporary directory for upload
    temp_dir = None
    uploaded_file_path = None
    
    try:
        temp_dir = tempfile.mkdtemp(prefix="nexus_upload_")
        logger.info(f"Created temp directory: {temp_dir}")
        
        # Save uploaded file with safe name
        uploaded_file_path = Path(temp_dir) / f"upload_{Path(file.filename).stem}{file_ext}"
        
        # Write file and validate size
        file_size_mb = 0
        with open(uploaded_file_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)  # 1 MB chunks
                if not chunk:
                    break
                
                file_size_mb += len(chunk) / (1024 * 1024)
                if file_size_mb > MAX_UPLOAD_SIZE_MB:
                    logger.warning(f"Upload rejected: file too large ({file_size_mb:.2f} MB)")
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE_MB} MB"
                    )
                
                f.write(chunk)
        
        logger.info(f"Uploaded file: {file.filename} ({file_size_mb:.2f} MB)")
        
        # Validate video file
        cap = cv2.VideoCapture(str(uploaded_file_path))
        if not cap.isOpened():
            logger.error(f"Invalid video file: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is not a valid video"
            )
        
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count == 0:
            logger.error(f"Video file has no frames: {file.filename}")
            cap.release()
            raise HTTPException(
                status_code=400,
                detail="Video file contains no frames"
            )
        cap.release()
        
        logger.info(f"Video validation passed: {frame_count} frames")
        
        # Run analysis pipeline
        try:
            result = analyze_video(str(uploaded_file_path), output_dir="artifacts")
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Video analysis failed: {str(e)}"
            )
        
        # Upload artifacts to S3 (if enabled)
        output_dir = Path(result["output_directory"])
        run_id = result["run_id"]
        s3_upload_result = s3_storage.upload_artifacts(run_id, output_dir)
        
        # Build response with agent recommendation
        metrics = result["report"]["analysis"]["metrics"]
        decision_trace = result["report"].get("adaptive_analysis", {})
        
        agent_execution = vision_agent.process_analysis_result(
            metrics=metrics,
            decision_trace=decision_trace,
            report=result["report"],
        )
        
        warnings = []
        
        # Check for S3 upload failure and add as warning (non-fatal)
        if s3_upload_result["s3_enabled"] and not s3_upload_result["success"]:
            error_detail = "; ".join(s3_upload_result["errors"])
            logger.warning(f"S3 upload failed for run {run_id}: {error_detail}")
            warnings.append(f"S3 artifact upload failed: {error_detail}. Local artifacts are available.")
        
        response = {
            "status": "success",
            "run_id": result["run_id"],
            "processing": result["report"]["processing"],
            "analysis": result["report"]["analysis"],
            "video": result["report"]["video"],
            "artifacts": result["report"]["artifacts"],
            "warnings": warnings,
            "notes": result["report"]["notes"],
            "adaptive_analysis": decision_trace,
            "agent_recommendation": agent_execution["recommendation"],
        }
        
        # Add S3 storage information to response
        if s3_upload_result["s3_enabled"]:
            response["s3_storage"] = {
                "enabled": True,
                "bucket": s3_storage.config.bucket,
                "uploaded_artifacts": s3_upload_result["uploaded_artifacts"],
                "upload_errors": s3_upload_result["errors"] if not s3_upload_result["success"] else [],
            }
        else:
            response["s3_storage"] = {
                "enabled": False,
            }
        
        logger.info(f"Analysis completed: {result['run_id']}")
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
    
    finally:
        # Cleanup temporary directory
        if temp_dir and Path(temp_dir).exists():
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory {temp_dir}: {e}")


@app.get("/artifacts/{run_id}/{filename}")
async def get_artifact(run_id: str, filename: str) -> FileResponse:
    """
    Retrieve a generated artifact by run ID and filename.
    
    Prevents path traversal by validating run_id format and whitelisting filenames.
    
    Args:
        run_id: Run identifier (format: run_YYYYMMDD_HHMMSS_xxxxxxxx)
        filename: Artifact filename to retrieve
        
    Returns:
        File response with artifact content
        
    Raises:
        HTTPException: If run_id/filename invalid or artifact not found
    """
    # Validate run_id format (prevent path traversal)
    if not run_id.startswith("run_") or "/" in run_id or "\\" in run_id or ".." in run_id:
        logger.warning(f"Invalid run_id format: {run_id}")
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    
    # Whitelist allowed artifact filenames
    allowed_filenames = {
        "annotated_video.mp4",
        "heatmap.png",
        "heatmap_followup_16x16.png",
        "report.json",
        "run_metadata.json",
    }
    
    if filename not in allowed_filenames:
        logger.warning(f"Artifact not in whitelist: {filename}")
        raise HTTPException(status_code=400, detail="Artifact type not allowed")
    
    # Construct artifact path
    artifact_path = Path("artifacts") / run_id / filename
    
    # Verify path exists and is within artifacts directory
    try:
        artifact_path = artifact_path.resolve()
        artifacts_dir = Path("artifacts").resolve()
        
        if not str(artifact_path).startswith(str(artifacts_dir)):
            logger.warning(f"Path traversal attempt: {artifact_path}")
            raise HTTPException(status_code=400, detail="Invalid artifact path")
        
        if not artifact_path.exists():
            logger.warning(f"Artifact not found: {artifact_path}")
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        # Serve file
        if filename.endswith(".json"):
            return FileResponse(artifact_path, media_type="application/json")
        elif filename.endswith(".png"):
            return FileResponse(artifact_path, media_type="image/png")
        elif filename.endswith(".mp4"):
            return FileResponse(artifact_path, media_type="video/mp4")
        else:
            return FileResponse(artifact_path)
    
    except (ValueError, RuntimeError) as e:
        logger.error(f"Path resolution error: {e}")
        raise HTTPException(status_code=400, detail="Invalid artifact path")


# Serve static UI files from ui/ directory if it exists
ui_dir = Path("ui")
if ui_dir.exists():
    try:
        app.mount("/ui", StaticFiles(directory=str(ui_dir), html=True), name="ui")
        logger.info("UI static files mounted at /ui")
    except Exception as e:
        logger.warning(f"Could not mount UI: {e}")


def create_app() -> FastAPI:
    """
    Create and return the FastAPI application.
    
    Returns:
        Configured FastAPI instance
    """
    return app


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Nexus Spatial Intelligence API server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
