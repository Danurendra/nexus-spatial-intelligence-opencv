#!/usr/bin/env python
"""Main entry point for Nexus Spatial Intelligence video analysis.

Usage:
    python src/main.py <video_path> [--output-dir <dir>] [--adaptive-threshold <percent>]
    
Example:
    python src/main.py videos/test_synthetic.mp4
    python src/main.py videos/test_synthetic.mp4 --adaptive-threshold 5.0
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
    from src.adaptive_analysis import AdaptiveAnalysisPolicy, AdaptiveAnalysisEngine, compare_analysis_results
except ImportError:
    from video_analyzer import VideoReader, MotionAnalyzer, HeatmapGenerator, ReportBuilder
    from adaptive_analysis import AdaptiveAnalysisPolicy, AdaptiveAnalysisEngine, compare_analysis_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def analyze_video(video_path: str, output_dir: str = None, adaptive_threshold: float = 5.0) -> dict:
    """
    Analyze a video file end-to-end with optional adaptive follow-up analysis.
    
    Args:
        video_path: Path to input video
        output_dir: Output directory for artifacts (default: artifacts/{run_id}/)
        adaptive_threshold: Foreground % threshold to trigger follow-up analysis (default: 5.0%)
        
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
    logger.info(f"Adaptive analysis threshold: {adaptive_threshold}%")
    
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
    
    # Initialize adaptive analysis engine
    adaptive_policy = AdaptiveAnalysisPolicy(
        policy_name="low_activity_refinement",
        threshold=adaptive_threshold
    )
    adaptive_engine = AdaptiveAnalysisEngine(adaptive_policy)
    
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
    
    # Step 4: Process all frames (baseline analysis)
    logger.info("Processing frames (baseline - 8x8 grid)...")
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
    
    logger.info(f"Processed {frames_processed} frames (baseline)")
    
    # Step 5: Generate baseline heatmap image
    logger.info("Generating baseline heatmap (8x8 grid)...")
    heatmap_image = heatmap_gen.generate_heatmap_image()
    heatmap_path = output_dir / "heatmap.png"
    cv2.imwrite(str(heatmap_path), heatmap_image)
    logger.info(f"Heatmap saved: {heatmap_path}")
    
    # Step 6: Calculate baseline statistics and make adaptive decision
    logger.info("Calculating baseline statistics...")
    baseline_motion_stats = analyzer.get_statistics()
    logger.info(f"Baseline metrics: avg={baseline_motion_stats['avg_foreground_percentage']:.2f}%, "
                f"min={baseline_motion_stats['min_foreground_percentage']:.2f}%, "
                f"max={baseline_motion_stats['max_foreground_percentage']:.2f}%")
    
    # Step 7: Make adaptive decision
    logger.info("Making adaptive analysis decision...")
    decision_trace = adaptive_engine.make_decision(baseline_motion_stats, metadata)
    logger.info(f"Decision: {decision_trace['decision_made']} ({decision_trace['reason']})")
    
    adaptive_trace = decision_trace
    followup_metrics = None
    
    # Step 8: Perform follow-up analysis if triggered
    if decision_trace["decision_made"] == "follow_up_triggered":
        logger.info("Performing follow-up analysis with finer 16x16 grid...")
        followup_start_time = time.time()
        
        try:
            # Create new heatmap with finer grid using stored foreground masks
            followup_heatmap_gen = HeatmapGenerator(
                metadata['width'], 
                metadata['height'], 
                grid_size=16
            )
            
            # Process stored foreground masks with finer grid
            for foreground_mask in analyzer.foreground_masks:
                followup_heatmap_gen.accumulate_motion(foreground_mask)
            
            # Generate follow-up heatmap
            followup_heatmap_image = followup_heatmap_gen.generate_heatmap_image()
            followup_heatmap_path = output_dir / "heatmap_followup_16x16.png"
            cv2.imwrite(str(followup_heatmap_path), followup_heatmap_image)
            logger.info(f"Follow-up heatmap saved: {followup_heatmap_path}")
            
            # Calculate follow-up statistics
            followup_metrics = {
                "avg_foreground_percentage": baseline_motion_stats['avg_foreground_percentage'],
                "min_foreground_percentage": baseline_motion_stats['min_foreground_percentage'],
                "max_foreground_percentage": baseline_motion_stats['max_foreground_percentage'],
                "std_foreground_percentage": baseline_motion_stats['std_foreground_percentage'],
                "note": "Follow-up uses same frames as baseline; metrics computed on finer 16x16 grid",
            }
            
            followup_duration = time.time() - followup_start_time
            logger.info(f"Follow-up analysis completed in {followup_duration:.3f} seconds")
            
            # Record follow-up results
            comparison = compare_analysis_results(baseline_motion_stats, followup_metrics)
            adaptive_engine.record_followup_results(
                followup_metrics=followup_metrics,
                processing_duration=followup_duration,
                comparison=comparison
            )
            
            adaptive_trace = adaptive_engine.get_trace()
            artifacts = {
                "annotated_video": str(output_video_path.relative_to(output_dir.parent)),
                "heatmap": str(heatmap_path.relative_to(output_dir.parent)),
                "heatmap_followup": str(followup_heatmap_path.relative_to(output_dir.parent)),
            }
            
        except Exception as e:
            logger.error(f"Follow-up analysis failed: {e}", exc_info=True)
            adaptive_engine.record_followup_error(
                error=str(e),
                error_details="Failed to generate follow-up heatmap with 16x16 grid"
            )
            adaptive_trace = adaptive_engine.get_trace()
            artifacts = {
                "annotated_video": str(output_video_path.relative_to(output_dir.parent)),
                "heatmap": str(heatmap_path.relative_to(output_dir.parent)),
            }
    else:
        logger.info("Follow-up analysis skipped (sufficient activity detected)")
        artifacts = {
            "annotated_video": str(output_video_path.relative_to(output_dir.parent)),
            "heatmap": str(heatmap_path.relative_to(output_dir.parent)),
        }
    
    # Step 9: Generate reports
    logger.info("Generating reports...")
    processing_duration = time.time() - start_time
    
    report = ReportBuilder.build_report(
        run_id=run_id,
        video_metadata=metadata,
        motion_stats=baseline_motion_stats,
        processing_duration=processing_duration,
        artifacts=artifacts,
        frames_processed=frames_processed,
        adaptive_trace=adaptive_trace,
    )
    
    # Step 10: Save reports
    report_path = output_dir / "report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved: {report_path}")
    
    # Save run metadata
    metadata_path = output_dir / "run_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump({
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "video_input": video_path,
            "output_directory": str(output_dir),
            "processing_duration_seconds": processing_duration,
            "frames_processed": frames_processed,
            "adaptive_threshold": adaptive_threshold,
            "adaptive_decision": adaptive_trace.get("decision_made"),
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
        description="Analyze video for spatial motion/activity using OpenCV 5 with adaptive follow-up",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py videos/test_synthetic.mp4
  python src/main.py videos/test_synthetic.mp4 --adaptive-threshold 5.0
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
    
    parser.add_argument(
        "--adaptive-threshold",
        type=float,
        default=5.0,
        help="Foreground %% threshold for triggering follow-up analysis (default: 5.0)"
    )
    
    args = parser.parse_args()
    
    try:
        result = analyze_video(args.video_path, args.output_dir, args.adaptive_threshold)
        
        logger.info("\n" + "="*60)
        logger.info("ANALYSIS COMPLETE")
        logger.info("="*60)
        logger.info(f"Run ID: {result['run_id']}")
        logger.info(f"Output directory: {result['output_directory']}")
        logger.info(f"Frames processed: {result['report']['processing']['frames_processed']}")
        logger.info(f"Processing duration: {result['processing_duration']:.2f} seconds")
        logger.info(f"Avg motion: {result['report']['analysis']['metrics']['avg_foreground_percentage']:.2f}%")
        
        # Log adaptive analysis results
        if "adaptive_analysis" in result['report']:
            adaptive = result['report']['adaptive_analysis']
            logger.info(f"Adaptive decision: {adaptive['decision_made']}")
            if adaptive['followup_results']:
                logger.info(f"Follow-up status: {adaptive['status']}")
        
        logger.info("="*60)
        
        return 0
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
