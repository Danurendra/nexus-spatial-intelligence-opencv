#!/usr/bin/env python
"""Test suite for M3 Adaptive Vision Analysis."""

import unittest
import tempfile
from pathlib import Path
import sys
import json
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.video_analyzer import VideoReader, MotionAnalyzer, HeatmapGenerator, ReportBuilder
from src.main import analyze_video
from src.adaptive_analysis import AdaptiveAnalysisPolicy, AdaptiveAnalysisEngine, compare_analysis_results


class TestAdaptivePolicy(unittest.TestCase):
    """Tests for adaptive analysis policy logic."""
    
    def test_policy_initialization(self):
        """Policy should initialize with name and threshold."""
        policy = AdaptiveAnalysisPolicy(policy_name="low_activity_refinement", threshold=5.0)
        
        self.assertEqual(policy.policy_name, "low_activity_refinement")
        self.assertEqual(policy.threshold, 5.0)
        self.assertEqual(policy.policy_version, "1.0")
    
    def test_low_activity_triggers_followup(self):
        """Low activity (below threshold) should trigger follow-up."""
        policy = AdaptiveAnalysisPolicy(threshold=5.0)
        
        metrics = {
            "avg_foreground_percentage": 3.0,
            "min_foreground_percentage": 0.0,
            "max_foreground_percentage": 10.0,
            "std_foreground_percentage": 2.0,
        }
        
        self.assertTrue(policy.should_trigger_followup(metrics))
    
    def test_high_activity_skips_followup(self):
        """High activity (above threshold) should skip follow-up."""
        policy = AdaptiveAnalysisPolicy(threshold=5.0)
        
        metrics = {
            "avg_foreground_percentage": 8.0,
            "min_foreground_percentage": 0.0,
            "max_foreground_percentage": 20.0,
            "std_foreground_percentage": 5.0,
        }
        
        self.assertFalse(policy.should_trigger_followup(metrics))
    
    def test_threshold_boundary(self):
        """Activity exactly at threshold should not trigger."""
        policy = AdaptiveAnalysisPolicy(threshold=5.0)
        
        metrics_at_threshold = {
            "avg_foreground_percentage": 5.0,
        }
        
        self.assertFalse(policy.should_trigger_followup(metrics_at_threshold))
    
    def test_configurable_threshold(self):
        """Threshold should be configurable."""
        policy = AdaptiveAnalysisPolicy(threshold=10.0)
        
        low_metrics = {"avg_foreground_percentage": 8.0}
        high_metrics = {"avg_foreground_percentage": 12.0}
        
        self.assertTrue(policy.should_trigger_followup(low_metrics))
        self.assertFalse(policy.should_trigger_followup(high_metrics))


class TestAdaptiveEngine(unittest.TestCase):
    """Tests for adaptive analysis engine decision trace."""
    
    def setUp(self):
        """Create engine for each test."""
        policy = AdaptiveAnalysisPolicy(threshold=5.0)
        self.engine = AdaptiveAnalysisEngine(policy)
    
    def test_decision_trace_structure_followup_triggered(self):
        """Decision trace should have required fields when follow-up triggered."""
        metrics = {"avg_foreground_percentage": 3.0, "min_foreground_percentage": 0.0,
                   "max_foreground_percentage": 10.0, "std_foreground_percentage": 2.0}
        metadata = {"width": 640, "height": 480}
        
        trace = self.engine.make_decision(metrics, metadata)
        
        self.assertIn("policy_name", trace)
        self.assertIn("decision_made", trace)
        self.assertIn("reason", trace)
        self.assertIn("initial_observations", trace)
        self.assertIn("condition_evaluated", trace)
        self.assertIn("followup_configuration", trace)
        
        self.assertEqual(trace["decision_made"], "follow_up_triggered")
        self.assertIsNotNone(trace["followup_configuration"])
    
    def test_decision_trace_structure_followup_skipped(self):
        """Decision trace should have required fields when follow-up skipped."""
        metrics = {"avg_foreground_percentage": 8.0, "min_foreground_percentage": 0.0,
                   "max_foreground_percentage": 20.0, "std_foreground_percentage": 5.0}
        metadata = {"width": 640, "height": 480}
        
        trace = self.engine.make_decision(metrics, metadata)
        
        self.assertIn("policy_name", trace)
        self.assertIn("decision_made", trace)
        self.assertIn("reason", trace)
        
        self.assertEqual(trace["decision_made"], "follow_up_skipped")
        self.assertIsNone(trace["followup_configuration"])
    
    def test_followup_results_recording(self):
        """Engine should record follow-up results correctly."""
        metrics = {"avg_foreground_percentage": 3.0}
        metadata = {}
        
        self.engine.make_decision(metrics, metadata)
        
        followup_metrics = {"avg_foreground_percentage": 3.5}
        self.engine.record_followup_results(
            followup_metrics=followup_metrics,
            processing_duration=0.5,
            comparison={"note": "test"}
        )
        
        trace = self.engine.get_trace()
        self.assertEqual(trace["status"], "complete")
        self.assertIsNotNone(trace["followup_results"])
        self.assertEqual(trace["followup_results"]["processing_duration_seconds"], 0.5)
    
    def test_followup_error_recording(self):
        """Engine should record follow-up errors correctly."""
        metrics = {"avg_foreground_percentage": 3.0}
        metadata = {}
        
        self.engine.make_decision(metrics, metadata)
        self.engine.record_followup_error("Test error", "Details")
        
        trace = self.engine.get_trace()
        self.assertEqual(trace["status"], "followup_failed")
        self.assertTrue(len(trace["warnings"]) > 0)


class TestAdaptiveEndToEnd(unittest.TestCase):
    """End-to-end tests for adaptive analysis with real video processing."""
    
    @classmethod
    def setUpClass(cls):
        """Create test videos with low and high activity."""
        cls.temp_dir = tempfile.TemporaryDirectory()
        
        # Low activity video (3 frames, minimal motion)
        cls.low_activity_video = Path(cls.temp_dir.name) / "low_activity.mp4"
        cls._create_video(str(cls.low_activity_video), num_frames=10, activity_level="low")
        
        # High activity video (3 frames, lots of motion)
        cls.high_activity_video = Path(cls.temp_dir.name) / "high_activity.mp4"
        cls._create_video(str(cls.high_activity_video), num_frames=10, activity_level="high")
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup temporary files."""
        cls.temp_dir.cleanup()
    
    @staticmethod
    def _create_video(output_path: str, num_frames: int = 10, activity_level: str = "low"):
        """Create synthetic test video with controlled activity level."""
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, 30, (320, 240))
        
        for i in range(num_frames):
            frame = np.ones((240, 320, 3), dtype=np.uint8) * 50
            
            if activity_level == "low":
                # Minimal motion - small, stationary object
                cv2.rectangle(frame, (100, 100), (150, 150), (0, 255, 0), -1)
            
            elif activity_level == "high":
                # High motion - large, fast-moving object
                x = int((i / num_frames) * 320)
                cv2.rectangle(frame, (x, 50), (x+100, 200), (0, 255, 0), -1)
                # Add additional motion
                cv2.circle(frame, (160, 120), int(30 + 20 * (i % 3)), (255, 0, 0), -1)
            
            writer.write(frame)
        writer.release()
    
    def test_low_activity_video_triggers_followup(self):
        """Low activity video should trigger adaptive follow-up."""
        result = analyze_video(str(self.low_activity_video), output_dir=Path(self.temp_dir.name) / "test_low")
        
        report = result['report']
        self.assertIn("adaptive_analysis", report)
        
        adaptive = report['adaptive_analysis']
        self.assertEqual(adaptive['decision_made'], "follow_up_triggered")
    
    def test_high_activity_video_skips_followup(self):
        """High activity video should skip adaptive follow-up."""
        result = analyze_video(str(self.high_activity_video), output_dir=Path(self.temp_dir.name) / "test_high")
        
        report = result['report']
        self.assertIn("adaptive_analysis", report)
        
        adaptive = report['adaptive_analysis']
        self.assertEqual(adaptive['decision_made'], "follow_up_skipped")
    
    def test_followup_heatmap_artifacts_created(self):
        """Follow-up analysis should create heatmap artifacts."""
        result = analyze_video(str(self.low_activity_video), output_dir=Path(self.temp_dir.name) / "test_artifacts")
        
        output_dir = Path(result['output_directory'])
        adaptive = result['report']['adaptive_analysis']
        
        if adaptive['decision_made'] == "follow_up_triggered":
            # Should have follow-up heatmap artifact
            self.assertIn('heatmap_followup', result['artifacts'])
    
    def test_report_includes_decision_trace(self):
        """Report should include complete decision trace."""
        result = analyze_video(str(self.low_activity_video), output_dir=Path(self.temp_dir.name) / "test_trace")
        
        report = result['report']
        adaptive = report['adaptive_analysis']
        
        self.assertEqual(adaptive['policy_version'], "1.0")
        self.assertEqual(adaptive['policy_name'], "low_activity_refinement")
        self.assertIn('reason', adaptive)


class TestReportWithAdaptive(unittest.TestCase):
    """Tests for report builder with adaptive data."""
    
    def test_report_includes_adaptive_section(self):
        """Report should include adaptive_analysis when provided."""
        adaptive_trace = {
            "policy_name": "test_policy",
            "decision_made": "follow_up_triggered",
        }
        
        report = ReportBuilder.build_report(
            run_id="test_run",
            video_metadata={"filename": "test.mp4", "width": 640, "height": 480, "fps": 30, "frame_count": 100},
            motion_stats={"avg_foreground_percentage": 2.0, "min_foreground_percentage": 0.0,
                         "max_foreground_percentage": 10.0, "std_foreground_percentage": 2.0},
            processing_duration=1.0,
            artifacts={"annotated_video": "test.mp4", "heatmap": "heatmap.png"},
            frames_processed=100,
            adaptive_trace=adaptive_trace,
        )
        
        self.assertIn("adaptive_analysis", report)
        self.assertEqual(report['adaptive_analysis']['policy_name'], "test_policy")
    
    def test_report_without_adaptive_section(self):
        """Report should work without adaptive_analysis."""
        report = ReportBuilder.build_report(
            run_id="test_run",
            video_metadata={"filename": "test.mp4", "width": 640, "height": 480, "fps": 30, "frame_count": 100},
            motion_stats={"avg_foreground_percentage": 2.0, "min_foreground_percentage": 0.0,
                         "max_foreground_percentage": 10.0, "std_foreground_percentage": 2.0},
            processing_duration=1.0,
            artifacts={"annotated_video": "test.mp4", "heatmap": "heatmap.png"},
            frames_processed=100,
        )
        
        self.assertNotIn("adaptive_analysis", report)
    
    def test_report_version_updated(self):
        """Report version should be updated for adaptive analysis."""
        report = ReportBuilder.build_report(
            run_id="test_run",
            video_metadata={"filename": "test.mp4", "width": 640, "height": 480, "fps": 30, "frame_count": 100},
            motion_stats={"avg_foreground_percentage": 2.0, "min_foreground_percentage": 0.0,
                         "max_foreground_percentage": 10.0, "std_foreground_percentage": 2.0},
            processing_duration=1.0,
            artifacts={"annotated_video": "test.mp4", "heatmap": "heatmap.png"},
            frames_processed=100,
        )
        
        self.assertEqual(report["report_version"], "1.1")


class TestComparisonFunction(unittest.TestCase):
    """Tests for comparison between baseline and follow-up."""
    
    def test_comparison_includes_differences(self):
        """Comparison should include differences between baseline and follow-up."""
        baseline = {"avg_foreground_percentage": 3.0}
        followup = {"avg_foreground_percentage": 3.5}
        
        comparison = compare_analysis_results(baseline, followup)
        
        self.assertIn("differences", comparison)
        self.assertIn("avg_foreground_percentage_change", comparison["differences"])
        self.assertAlmostEqual(comparison["differences"]["avg_foreground_percentage_change"], 0.5)
    
    def test_comparison_includes_note(self):
        """Comparison should include interpretation note."""
        baseline = {"avg_foreground_percentage": 3.0}
        followup = None
        
        comparison = compare_analysis_results(baseline, followup)
        
        self.assertIn("note", comparison)


def run_tests(verbosity=2):
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptivePolicy))
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveEndToEnd))
    suite.addTests(loader.loadTestsFromTestCase(TestReportWithAdaptive))
    suite.addTests(loader.loadTestsFromTestCase(TestComparisonFunction))
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    import sys
    exit_code = run_tests()
    sys.exit(exit_code)
