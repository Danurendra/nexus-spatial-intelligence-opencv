#!/usr/bin/env python
"""Test suite for Nexus Spatial Intelligence video analysis pipeline."""

import unittest
import tempfile
import json
from pathlib import Path
import cv2
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.video_analyzer import VideoReader, MotionAnalyzer, HeatmapGenerator, ReportBuilder
except ImportError:
    # If running from different directory
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from video_analyzer import VideoReader, MotionAnalyzer, HeatmapGenerator, ReportBuilder


class TestVideoReader(unittest.TestCase):
    """Tests for VideoReader class."""
    
    @classmethod
    def setUpClass(cls):
        """Create a temporary test video."""
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.test_video_path = Path(cls.temp_dir.name) / "test.mp4"
        
        # Create simple test video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(cls.test_video_path), fourcc, 30, (320, 240))
        
        for i in range(30):
            frame = np.ones((240, 320, 3), dtype=np.uint8) * (50 + i)
            writer.write(frame)
        writer.release()
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup temporary files."""
        cls.temp_dir.cleanup()
    
    def test_video_reader_opens_valid_video(self):
        """VideoReader should open a valid video file."""
        reader = VideoReader(str(self.test_video_path))
        self.assertIsNotNone(reader.cap)
        reader.release()
    
    def test_video_reader_extracts_metadata(self):
        """VideoReader should extract correct metadata."""
        reader = VideoReader(str(self.test_video_path))
        metadata = reader.get_metadata()
        
        self.assertEqual(metadata['width'], 320)
        self.assertEqual(metadata['height'], 240)
        self.assertEqual(metadata['fps'], 30)
        self.assertEqual(metadata['frame_count'], 30)
        self.assertEqual(metadata['filename'], 'test.mp4')
        
        reader.release()
    
    def test_video_reader_raises_on_missing_file(self):
        """VideoReader should raise FileNotFoundError for missing file."""
        with self.assertRaises(FileNotFoundError):
            VideoReader("nonexistent_video.mp4")
    
    def test_video_reader_reads_frames(self):
        """VideoReader should read frames correctly."""
        reader = VideoReader(str(self.test_video_path))
        
        ret, frame = reader.read_frame()
        self.assertTrue(ret)
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape, (240, 320, 3))
        
        reader.release()
    
    def test_video_reader_seek_frame(self):
        """VideoReader should seek to specific frames."""
        reader = VideoReader(str(self.test_video_path))
        
        # Seek to frame 15
        success = reader.seek_frame(15)
        self.assertTrue(success)
        
        reader.release()


class TestMotionAnalyzer(unittest.TestCase):
    """Tests for MotionAnalyzer class."""
    
    def test_motion_analyzer_initialization(self):
        """MotionAnalyzer should initialize correctly."""
        analyzer = MotionAnalyzer()
        self.assertEqual(analyzer.frame_count, 0)
        self.assertEqual(len(analyzer.motion_data), 0)
    
    def test_motion_analyzer_processes_frame(self):
        """MotionAnalyzer should process frames and return metrics."""
        analyzer = MotionAnalyzer()
        frame = np.ones((240, 320, 3), dtype=np.uint8) * 100
        
        foreground, metrics = analyzer.process_frame(frame)
        
        self.assertIsNotNone(foreground)
        self.assertIn("frame", metrics)
        self.assertIn("foreground_percentage", metrics)
        self.assertIn("foreground_pixels", metrics)
        self.assertEqual(analyzer.frame_count, 1)
    
    def test_motion_analyzer_statistics(self):
        """MotionAnalyzer should compute statistics correctly."""
        analyzer = MotionAnalyzer()
        
        for _ in range(10):
            frame = np.ones((240, 320, 3), dtype=np.uint8) * 100
            analyzer.process_frame(frame)
        
        stats = analyzer.get_statistics()
        
        self.assertEqual(stats["total_frames"], 10)
        self.assertIn("avg_foreground_percentage", stats)
        self.assertIn("min_foreground_percentage", stats)
        self.assertIn("max_foreground_percentage", stats)
        self.assertIn("std_foreground_percentage", stats)
        
        # All values should be non-negative
        for key in ["avg_foreground_percentage", "min_foreground_percentage", 
                   "max_foreground_percentage", "std_foreground_percentage"]:
            self.assertGreaterEqual(stats[key], 0)


class TestHeatmapGenerator(unittest.TestCase):
    """Tests for HeatmapGenerator class."""
    
    def test_heatmap_generator_initialization(self):
        """HeatmapGenerator should initialize correctly."""
        gen = HeatmapGenerator(640, 480, grid_size=8)
        self.assertEqual(gen.video_width, 640)
        self.assertEqual(gen.video_height, 480)
        self.assertEqual(gen.grid_size, 8)
        self.assertEqual(gen.heatmap_data.shape, (8, 8))
    
    def test_heatmap_generator_accumulates_motion(self):
        """HeatmapGenerator should accumulate motion data."""
        gen = HeatmapGenerator(640, 480, grid_size=8)
        foreground = np.zeros((480, 640), dtype=np.uint8)
        foreground[0:100, 0:100] = 255  # Add motion in top-left
        
        gen.accumulate_motion(foreground)
        
        # Heatmap data should have been updated
        self.assertGreater(np.sum(gen.heatmap_data), 0)
    
    def test_heatmap_generator_creates_image(self):
        """HeatmapGenerator should generate valid heatmap image."""
        gen = HeatmapGenerator(640, 480, grid_size=8)
        
        # Add some motion
        for _ in range(5):
            foreground = np.random.randint(0, 256, (480, 640), dtype=np.uint8)
            gen.accumulate_motion(foreground)
        
        heatmap_image = gen.generate_heatmap_image()
        
        self.assertEqual(heatmap_image.shape, (480, 640, 3))
        self.assertEqual(heatmap_image.dtype, np.uint8)


class TestReportBuilder(unittest.TestCase):
    """Tests for ReportBuilder class."""
    
    def test_report_builder_creates_valid_report(self):
        """ReportBuilder should create a valid report structure."""
        video_metadata = {
            "filename": "test.mp4",
            "width": 640,
            "height": 480,
            "fps": 30,
            "frame_count": 300,
        }
        
        motion_stats = {
            "total_frames": 300,
            "avg_foreground_percentage": 5.0,
            "min_foreground_percentage": 0.0,
            "max_foreground_percentage": 10.0,
            "std_foreground_percentage": 2.0,
        }
        
        artifacts = {
            "annotated_video": "test_annotated.mp4",
            "heatmap": "test_heatmap.png",
        }
        
        report = ReportBuilder.build_report(
            run_id="test_run",
            video_metadata=video_metadata,
            motion_stats=motion_stats,
            processing_duration=5.0,
            artifacts=artifacts,
            frames_processed=300,
        )
        
        self.assertEqual(report["run_id"], "test_run")
        self.assertIn("timestamp", report)
        self.assertIn("video", report)
        self.assertIn("processing", report)
        self.assertIn("analysis", report)
        self.assertIn("artifacts", report)
        self.assertIn("software", report)
        
        # Check specific values
        self.assertEqual(report["video"]["filename"], "test.mp4")
        self.assertEqual(report["processing"]["frames_processed"], 300)
        self.assertEqual(report["analysis"]["metrics"]["avg_foreground_percentage"], 5.0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete pipeline."""
    
    @classmethod
    def setUpClass(cls):
        """Create a temporary test video with motion."""
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.test_video_path = Path(cls.temp_dir.name) / "motion_test.mp4"
        
        # Create test video with motion
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(cls.test_video_path), fourcc, 30, (320, 240))
        
        for i in range(30):
            frame = np.ones((240, 320, 3), dtype=np.uint8) * 50
            # Add moving object
            x = int(50 + 100 * i / 30)
            cv2.rectangle(frame, (x, 50), (x+50, 150), (0, 255, 0), -1)
            writer.write(frame)
        writer.release()
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup temporary files."""
        cls.temp_dir.cleanup()
    
    def test_end_to_end_pipeline(self):
        """Complete pipeline should process a video end-to-end."""
        reader = VideoReader(str(self.test_video_path))
        metadata = reader.get_metadata()
        
        analyzer = MotionAnalyzer()
        heatmap_gen = HeatmapGenerator(metadata['width'], metadata['height'])
        
        frames_processed = 0
        while True:
            ret, frame = reader.read_frame()
            if not ret:
                break
            
            foreground, metrics = analyzer.process_frame(frame)
            heatmap_gen.accumulate_motion(foreground)
            frames_processed += 1
        
        reader.release()
        
        # Verify processing
        self.assertEqual(frames_processed, metadata['frame_count'])
        
        # Verify analyzer
        stats = analyzer.get_statistics()
        self.assertEqual(stats["total_frames"], frames_processed)
        self.assertGreater(stats["max_foreground_percentage"], 0)
        
        # Verify heatmap
        heatmap_image = heatmap_gen.generate_heatmap_image()
        self.assertEqual(heatmap_image.shape, (metadata['height'], metadata['width'], 3))


def run_tests(verbosity=2):
    """Run all tests and return exit code."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestVideoReader))
    suite.addTests(loader.loadTestsFromTestCase(TestMotionAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestHeatmapGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestReportBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
