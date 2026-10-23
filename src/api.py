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
from fastapi.responses import JSONResponse
import cv2

from src.main import analyze_video

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MAX_UPLOAD_SIZE_MB = 100  # 100 MB max file size
ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.flv'}

app = FastAPI(
    title="Nexus Spatial Intelligence API",
    description="Video analysis platform for OpenCV AI Competition 2026",
    version="0.2.0"
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
        
        # Build response
        response = {
            "status": "success",
            "run_id": result["run_id"],
            "processing": result["report"]["processing"],
            "analysis": result["report"]["analysis"],
            "video": result["report"]["video"],
            "artifacts": result["report"]["artifacts"],
            "warnings": [],
            "notes": result["report"]["notes"],
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
