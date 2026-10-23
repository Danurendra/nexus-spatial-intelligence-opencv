#!/usr/bin/env python
"""Generate a synthetic test video with motion for development and testing."""

import cv2
import numpy as np
from pathlib import Path

def create_synthetic_test_video(output_path: str, duration_seconds: int = 10, fps: int = 30):
    """
    Create a simple synthetic video with moving objects for testing.
    
    Features:
    - Dimensions: 640x480
    - FPS: 30
    - Duration: configurable (default 10 seconds)
    - Content: moving rectangles and circles with gradual changes
    """
    
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not writer.isOpened():
        print(f"ERROR: Could not open VideoWriter for {output_path}")
        return False
    
    total_frames = duration_seconds * fps
    
    for frame_idx in range(total_frames):
        # Create blank frame with slight background activity
        frame = np.ones((height, width, 3), dtype=np.uint8) * 50
        
        # Add some static elements
        cv2.rectangle(frame, (10, 10), (100, 100), (100, 100, 100), -1)
        cv2.rectangle(frame, (width-110, height-110), (width-10, height-10), (100, 100, 100), -1)
        
        # Add moving rectangles
        progress = (frame_idx / total_frames) * 2 * np.pi
        
        # Rectangle 1: horizontal motion
        x1 = int(50 + (width - 100) * (0.5 + 0.4 * np.sin(progress)))
        cv2.rectangle(frame, (x1, 150), (x1 + 100, 250), (0, 255, 0), -1)
        
        # Rectangle 2: vertical motion
        y2 = int(50 + (height - 100) * (0.5 + 0.4 * np.cos(progress)))
        cv2.rectangle(frame, (350, y2), (450, y2 + 100), (0, 0, 255), -1)
        
        # Circle: circular motion
        center_x = int(width / 2 + 100 * np.cos(progress))
        center_y = int(height / 2 + 100 * np.sin(progress))
        cv2.circle(frame, (center_x, center_y), 40, (255, 255, 0), -1)
        
        # Add frame number text
        cv2.putText(frame, f"Frame {frame_idx+1}/{total_frames}", (10, height-20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        writer.write(frame)
    
    writer.release()
    print(f"[OK] Synthetic test video created: {output_path}")
    return True

if __name__ == "__main__":
    output_path = Path("videos/test_synthetic.mp4")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("Generating synthetic test video...")
    if create_synthetic_test_video(str(output_path), duration_seconds=10, fps=30):
        # Verify the video was created
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"[OK] Video file created successfully: {size_mb:.2f} MB")
            
            # Quick verification: try to open it
            cap = cv2.VideoCapture(str(output_path))
            if cap.isOpened():
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                print(f"[OK] Video verification successful: {frame_count} frames, {fps} FPS, {width}x{height}")
            else:
                print("[FAILED] Could not open generated video for verification")
        else:
            print("[FAILED] Video file was not created")
    else:
        print("[FAILED] Could not create synthetic video")
