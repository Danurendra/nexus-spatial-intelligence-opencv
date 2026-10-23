#!/usr/bin/env python
"""Main entry point for Nexus Spatial Intelligence video analysis.

Usage:
    python src/main.py <video_path> [--output-dir <dir>]
    
Example:
    python src/main.py videos/test_synthetic.mp4
    python src/main.py videos/test_synthetic.mp4 --output-dir artifacts/custom
"""

import sys
import argparse
import json
import time
import uuid
from pathlib import Path
from datetime import datetime
import logging

import cv2
import numpy as np

# Handle imports whether run as module or script
try:
    from src.video_analyzer import VideoReader, MotionAnalyzer, HeatmapGenerator, ReportBuilder
except ImportError:
    from video_analyzer import VideoReader, MotionAnalyzer, HeatmapGenerator, ReportBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_video(video_path: str, output_dir: str = None) -> dict:
    """
    Analyze a video file end-to-end.
    
    Args:
        video_path: Path to input video
        output_dir: Output directory for artifacts (default: artifacts/{run_id}/)
        
    Returns:
        Dictionary with analysis results and artifact paths
        
    Raises:
        FileNotFoundError: If video does not exist
        ValueError: If video cannot be processed
    """
    start_time = time.time()
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    # Setup output directory
    if output_dir is None:
        output_dir = Path("artifacts") / run_id
    else:
        output_dir = Path(output_dir) / run_id
    
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Output directory: {output_dir}")
    
    # Step 1: Open and read video metadata
    logger.info(f"Opening video: {video_path}")
    try:
        reader = VideoReader(video_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to open video: {e}")
        raise
    
    metadata = reader.get_metadata()
    logger.info(f"Video info: {metadata['width']}x{metadata['height']}, "
                f"{metadata['fps']} FPS, {metadata['frame_count']} frames")
    
    # Step 2: Initialize analysis components
    analyzer = MotionAnalyzer()
    heatmap_gen = HeatmapGenerator(metadata['width'], metadata['height'], grid_size=8)
    
    # Step 3: Setup video writer for annotated output
    output_video_path = output_dir / "annotated_video.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(
        str(output_video_path),
        fourcc,
        metadata['fps'],
        (metadata['width'], metadata['height'])
    )
    
    if not writer.isOpened():
        logger.error(f"Could not open VideoWriter for {output_video_path}")
        raise ValueError(f"Failed to create output video writer")
    
    # Step 4: Process all frames
    logger.info("Processing frames...")
    frames_processed = 0
    
    try:
        while True:
            ret, frame = reader.read_frame()
            if not ret:
                break
            
            frames_processed += 1
            
            # Analyze motion
            foreground, metrics = analyzer.process_frame(frame)
            heatmap_gen.accumulate_motion(foreground)
            
            # Create annotated frame
            # Overlay foreground mask in green
            overlay = frame.copy()
            green_foreground = np.zeros_like(frame)
            green_foreground[:, :, 1] = foreground  # Green channel
            cv2.addWeighted(overlay, 0.7, green_foreground, 0.3, 0, overlay)
            
            # Add text annotations
            fg_percent = metrics["foreground_percentage"]
            cv2.putText(overlay, f"Motion: {fg_percent:.2f}%", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(overlay, f"Frame: {frames_processed}/{metadata['frame_count']}", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            writer.write(overlay)
            
            # Progress logging
            if frames_processed % max(1, metadata['frame_count'] // 10) == 0:
                logger.info(f"  Processed {frames_processed}/{metadata['frame_count']} frames")
    
    finally:
        reader.release()
        writer.release()
    
    logger.info(f"Processed {frames_processed} frames")
    
    # Step 5: Generate heatmap image
    logger.info("Generating heatmap...")
    heatmap_image = heatmap_gen.generate_heatmap_image()
    heatmap_path = output_dir / "heatmap.png"
    cv2.imwrite(str(heatmap_path), heatmap_image)
    logger.info(f"Heatmap saved: {heatmap_path}")
    
    # Step 6: Generate reports
    processing_duration = time.time() - start_time
    motion_stats = analyzer.get_statistics()
    
    artifacts = {
        "annotated_video": str(output_video_path.relative_to(output_dir.parent)),
        "heatmap": str(heatmap_path.relative_to(output_dir.parent)),
    }
    
    report = ReportBuilder.build_report(
        run_id=run_id,
        video_metadata=metadata,
        motion_stats=motion_stats,
        processing_duration=processing_duration,
        artifacts=artifacts,
        frames_processed=frames_processed,
    )
    
    # Step 7: Save reports
    report_path = output_dir / "report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved: {report_path}")
    
    # Step 8: Save run metadata
    metadata_path = output_dir / "run_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump({
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "video_input": video_path,
            "output_directory": str(output_dir),
            "processing_duration_seconds": processing_duration,
            "frames_processed": frames_processed,
        }, f, indent=2)
    logger.info(f"Metadata saved: {metadata_path}")
    
    logger.info(f"Analysis complete in {processing_duration:.2f} seconds")
    
    return {
        "run_id": run_id,
        "success": True,
        "output_directory": str(output_dir),
        "artifacts": artifacts,
        "report": report,
        "processing_duration": processing_duration,
    }


def main():
    """Parse arguments and run analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze video for spatial motion/activity using OpenCV 5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py videos/test_synthetic.mp4
  python src/main.py videos/test_synthetic.mp4 --output-dir custom_artifacts
        """
    )
    
    parser.add_argument(
        "video_path",
        help="Path to input video file"
    )
    
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for artifacts (default: artifacts/)"
    )
    
    args = parser.parse_args()
    
    try:
        result = analyze_video(args.video_path, args.output_dir)
        
        logger.info("\n" + "="*60)
        logger.info("ANALYSIS COMPLETE")
        logger.info("="*60)
        logger.info(f"Run ID: {result['run_id']}")
        logger.info(f"Output directory: {result['output_directory']}")
        logger.info(f"Frames processed: {result['report']['processing']['frames_processed']}")
        logger.info(f"Processing duration: {result['processing_duration']:.2f} seconds")
        logger.info(f"Avg motion: {result['report']['analysis']['metrics']['avg_foreground_percentage']:.2f}%")
        logger.info("="*60)
        
        return 0
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
