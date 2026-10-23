"""
Video analysis pipeline using OpenCV 5.

Modules:
- VideoReader: Extract metadata and read frames
- MotionAnalyzer: Calculate motion metrics using background subtraction
- HeatmapGenerator: Create spatial activity visualization
- ReportBuilder: Generate JSON reports with measurements
"""

import cv2
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class VideoReader:
    """Read video files and extract metadata using OpenCV."""
    
    def __init__(self, video_path: str):
        """Initialize video reader.
        
        Args:
            video_path: Path to input video file
            
        Raises:
            FileNotFoundError: If video file does not exist
            ValueError: If video cannot be opened
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        self.video_path = video_path
        self.cap = cv2.VideoCapture(str(video_path))
        
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """Extract video metadata.
        
        Returns:
            Dictionary containing video properties
        """
        return {
            "filename": self.video_path.name,
            "path": str(self.video_path.absolute()),
            "frame_count": int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "fps": float(self.cap.get(cv2.CAP_PROP_FPS)),
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fourcc": int(self.cap.get(cv2.CAP_PROP_FOURCC)),
        }
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read next frame from video.
        
        Returns:
            Tuple of (success, frame) where frame is BGR numpy array or None
        """
        ret, frame = self.cap.read()
        return ret, frame
    
    def seek_frame(self, frame_num: int) -> bool:
        """Seek to specific frame number.
        
        Args:
            frame_num: Frame index (0-based)
            
        Returns:
            True if seek was successful
        """
        return self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    
    def release(self):
        """Release video capture resources."""
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.release()


class MotionAnalyzer:
    """Analyze video motion using background subtraction (MOG2)."""
    
    def __init__(self, history: int = 500, var_threshold: float = 16):
        """Initialize motion analyzer.
        
        Args:
            history: Number of frames to use for background model
            var_threshold: Variance threshold for foreground detection
        """
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True,
            history=history,
            varThreshold=var_threshold
        )
        self.motion_data = []
        self.frame_count = 0
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
        """Process single frame for motion.
        
        Args:
            frame: Input frame (BGR numpy array)
            
        Returns:
            Tuple of (foreground_mask, metrics) where metrics contains
            motion statistics for the frame
        """
        self.frame_count += 1
        
        # Apply background subtraction
        foreground = self.bg_subtractor.apply(frame, learningRate=0.005)
        
        # Remove shadows (value 128) - keep only foreground (255) and background (0)
        foreground = cv2.threshold(foreground, 200, 255, cv2.THRESH_BINARY)[1]
        
        # Calculate metrics
        total_pixels = frame.shape[0] * frame.shape[1]
        foreground_pixels = cv2.countNonZero(foreground)
        foreground_percentage = (foreground_pixels / total_pixels) * 100
        
        metrics = {
            "frame": self.frame_count,
            "foreground_pixels": int(foreground_pixels),
            "foreground_percentage": float(foreground_percentage),
            "total_pixels": int(total_pixels),
        }
        
        self.motion_data.append(metrics)
        return foreground, metrics
    
    def get_statistics(self) -> Dict[str, float]:
        """Get aggregated motion statistics.
        
        Returns:
            Dictionary with motion statistics
        """
        if not self.motion_data:
            return {
                "total_frames": 0,
                "avg_foreground_percentage": 0.0,
                "min_foreground_percentage": 0.0,
                "max_foreground_percentage": 0.0,
                "std_foreground_percentage": 0.0,
            }
        
        foreground_values = [m["foreground_percentage"] for m in self.motion_data]
        
        return {
            "total_frames": len(self.motion_data),
            "avg_foreground_percentage": float(np.mean(foreground_values)),
            "min_foreground_percentage": float(np.min(foreground_values)),
            "max_foreground_percentage": float(np.max(foreground_values)),
            "std_foreground_percentage": float(np.std(foreground_values)),
        }


class HeatmapGenerator:
    """Generate spatial activity heatmaps from motion data."""
    
    def __init__(self, video_width: int, video_height: int, grid_size: int = 8):
        """Initialize heatmap generator.
        
        Args:
            video_width: Video frame width
            video_height: Video frame height
            grid_size: Size of analysis grid (divides frame into grid_size x grid_size regions)
        """
        self.video_width = video_width
        self.video_height = video_height
        self.grid_size = grid_size
        self.cell_width = video_width // grid_size
        self.cell_height = video_height // grid_size
        self.heatmap_data = np.zeros((grid_size, grid_size), dtype=np.float32)
    
    def accumulate_motion(self, foreground_mask: np.ndarray):
        """Accumulate motion data into spatial bins.
        
        Args:
            foreground_mask: Binary foreground mask from motion analyzer
        """
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                y_start = i * self.cell_height
                y_end = (i + 1) * self.cell_height
                x_start = j * self.cell_width
                x_end = (j + 1) * self.cell_width
                
                cell_region = foreground_mask[y_start:y_end, x_start:x_end]
                motion_count = cv2.countNonZero(cell_region)
                self.heatmap_data[i, j] += motion_count
    
    def generate_heatmap_image(self) -> np.ndarray:
        """Generate heatmap visualization.
        
        Returns:
            BGR image array suitable for saving with cv2.imwrite
        """
        # Normalize heatmap to 0-255
        heatmap_normalized = cv2.normalize(
            self.heatmap_data,
            None,
            0,
            255,
            cv2.NORM_MINMAX
        ).astype(np.uint8)
        
        # Resize to match video dimensions
        heatmap_resized = cv2.resize(
            heatmap_normalized,
            (self.video_width, self.video_height),
            interpolation=cv2.INTER_LINEAR
        )
        
        # Apply color map
        heatmap_color = cv2.applyColorMap(heatmap_resized, cv2.COLORMAP_JET)
        
        return heatmap_color


class ReportBuilder:
    """Build JSON reports from analysis results."""
    
    @staticmethod
    def build_report(
        run_id: str,
        video_metadata: Dict[str, Any],
        motion_stats: Dict[str, Any],
        processing_duration: float,
        artifacts: Dict[str, str],
        frames_processed: int,
    ) -> Dict[str, Any]:
        """Build a comprehensive analysis report.
        
        Args:
            run_id: Unique run identifier
            video_metadata: Video metadata from VideoReader
            motion_stats: Motion statistics from MotionAnalyzer
            processing_duration: Total processing time in seconds
            artifacts: Dictionary of generated artifact paths
            frames_processed: Number of frames actually processed
            
        Returns:
            Dictionary representing the analysis report
        """
        return {
            "report_version": "1.0",
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "video": {
                "filename": video_metadata.get("filename"),
                "width": video_metadata.get("width"),
                "height": video_metadata.get("height"),
                "fps": video_metadata.get("fps"),
                "total_frames": video_metadata.get("frame_count"),
            },
            "processing": {
                "frames_processed": frames_processed,
                "duration_seconds": float(processing_duration),
                "fps_processed": float(frames_processed / processing_duration) if processing_duration > 0 else 0,
            },
            "analysis": {
                "method": "OpenCV MOG2 background subtraction",
                "description": "Foreground/motion detection using Mixture of Gaussians v2 background model",
                "metrics": {
                    "avg_foreground_percentage": motion_stats.get("avg_foreground_percentage"),
                    "min_foreground_percentage": motion_stats.get("min_foreground_percentage"),
                    "max_foreground_percentage": motion_stats.get("max_foreground_percentage"),
                    "std_foreground_percentage": motion_stats.get("std_foreground_percentage"),
                },
            },
            "artifacts": artifacts,
            "software": {
                "opencv_version": cv2.__version__,
                "numpy_version": np.__version__,
            },
            "notes": "Foreground percentage indicates motion/activity level. Not a person detection system.",
        }
