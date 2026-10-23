#!/usr/bin/env python
"""Verify generated artifacts from analysis."""

import sys
import json
from pathlib import Path
import cv2

def verify_video(video_path):
    """Verify video file is readable and valid."""
    if not Path(video_path).exists():
        return False, f"File not found: {video_path}"
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return False, f"Could not open video: {video_path}"
    
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Try to read first frame
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return False, "Could not read first frame"
    
    info = f"{frame_count} frames, {fps} FPS, {width}x{height}"
    return True, info

def verify_image(image_path):
    """Verify image file is readable and valid."""
    if not Path(image_path).exists():
        return False, f"File not found: {image_path}"
    
    img = cv2.imread(str(image_path))
    if img is None:
        return False, "Could not read image"
    
    height, width = img.shape[:2]
    info = f"{width}x{height}, shape={img.shape}"
    return True, info

def verify_json(json_path):
    """Verify JSON file is readable and valid."""
    if not Path(json_path).exists():
        return False, f"File not found: {json_path}"
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        return True, f"Valid JSON with {len(data)} top-level keys"
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_artifacts.py <run_directory>")
        sys.exit(1)
    
    run_dir = Path(sys.argv[1])
    
    if not run_dir.exists():
        print(f"Run directory not found: {run_dir}")
        sys.exit(1)
    
    print(f"Verifying artifacts in: {run_dir}\n")
    
    artifacts = {
        "annotated_video.mp4": verify_video,
        "heatmap.png": verify_image,
        "report.json": verify_json,
        "run_metadata.json": verify_json,
    }
    
    all_ok = True
    for artifact_name, verify_func in artifacts.items():
        artifact_path = run_dir / artifact_name
        ok, info = verify_func(str(artifact_path))
        status = "[OK]" if ok else "[FAILED]"
        print(f"{status} {artifact_name}: {info}")
        if not ok:
            all_ok = False
    
    print()
    if all_ok:
        print("[SUCCESS] All artifacts verified!")
        sys.exit(0)
    else:
        print("[FAILED] Some artifacts could not be verified")
        sys.exit(1)
