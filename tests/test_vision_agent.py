#!/usr/bin/env python
"""Test suite for M5 Adaptive Vision Agent and GUI endpoints."""

import unittest
import json
import tempfile
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vision_agent import VisionAgent, VisionAgentRecommendation
from src.adaptive_analysis import AdaptiveAnalysisPolicy, AdaptiveAnalysisEngine


class TestVisionAgentRecommendation(unittest.TestCase):
    """Tests for recommendation generation logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.low_metrics = {
            "avg_foreground_percentage": 3.7,
            "min_foreground_percentage": 0.0,
            "max_foreground_percentage": 8.6,
            "std_foreground_percentage": 1.9,
        }
        
        self.high_metrics = {
            "avg_foreground_percentage": 15.0,
            "min_foreground_percentage": 5.0,
            "max_foreground_percentage": 25.0,
            "std_foreground_percentage": 5.0,
        }
        
        self.low_trace = {
            "policy_name": "low_activity_refinement",
            "decision_made": "follow_up_triggered",
            "reason": "Low activity detected",
            "condition_evaluated": {"threshold": 5.0, "actual_value": 3.7},
            "status": "complete",
        }
        
        self.high_trace = {
            "policy_name": "low_activity_refinement",
            "decision_made": "follow_up_skipped",
            "reason": "Sufficient activity detected",
            "condition_evaluated": {"threshold": 5.0, "actual_value": 15.0},
            "status": "complete",
        }
    
    def test_recommendation_low_activity_with_refinement(self):
        """Low activity with successful refinement should generate appropriate recommendation."""
        rec = VisionAgentRecommendation.generate(
            metrics=self.low_metrics,
            decision_trace=self.low_trace,
            followup_performed=True,
            followup_metrics=self.low_metrics,
            followup_error=None,
        )
        
        self.assertEqual(rec["category"], "low_activity_with_refinement")
        self.assertEqual(rec["confidence"], "high")
        self.assertGreater(len(rec["evidence"]), 0)
        self.assertGreater(len(rec["next_steps"]), 0)
        self.assertIsNotNone(rec["notes"])
        # Verify evidence includes actual metrics
        self.assertTrue(any("3.7" in str(e) or "3.70" in str(e) for e in rec["evidence"]))
    
    def test_recommendation_low_activity_refinement_failed(self):
        """Low activity with failed refinement should acknowledge the error."""
        # Create a decision trace with failed status
        failed_trace = {
            "policy_name": "low_activity_refinement",
            "decision_made": "follow_up_triggered",
            "reason": "Low activity detected",
            "condition_evaluated": {"threshold": 5.0, "actual_value": 3.7},
            "status": "followup_failed",
            "warnings": [{"error": "Heatmap generation failed"}],
        }
        
        rec = VisionAgentRecommendation.generate(
            metrics=self.low_metrics,
            decision_trace=failed_trace,
            followup_performed=True,
            followup_metrics=None,
            followup_error="Heatmap generation failed",
        )
        
        self.assertEqual(rec["category"], "low_activity_refinement_failed")
        self.assertEqual(rec["confidence"], "medium")
        # Check that error is mentioned in notes
        self.assertIn("error", rec["notes"].lower())
        self.assertIn("Heatmap generation failed", rec["notes"])
    
    def test_recommendation_sufficient_activity(self):
        """High activity should recommend using baseline grid only."""
        rec = VisionAgentRecommendation.generate(
            metrics=self.high_metrics,
            decision_trace=self.high_trace,
            followup_performed=False,
            followup_metrics=None,
            followup_error=None,
        )
        
        self.assertEqual(rec["category"], "sufficient_activity")
        self.assertEqual(rec["confidence"], "high")
        self.assertGreater(len(rec["next_steps"]), 0)
        # Verify recommendation uses actual metrics
        self.assertTrue(any("15" in str(e) for e in rec["evidence"]))
    
    def test_recommendation_includes_evidence(self):
        """Recommendations should be grounded in actual metrics and policy."""
        rec = VisionAgentRecommendation.generate(
            metrics=self.low_metrics,
            decision_trace=self.low_trace,
            followup_performed=True,
            followup_metrics=self.low_metrics,
            followup_error=None,
        )
        
        # Verify evidence is grounded in actual values
        self.assertTrue(
            any("3.7" in str(e) or "3.70" in str(e) for e in rec["evidence"]),
            "Evidence should include actual avg_foreground value"
        )
        self.assertTrue(
            any("5.0" in str(e) or "threshold" in str(e).lower() for e in rec["evidence"]),
            "Evidence should include threshold"
        )


class TestVisionAgent(unittest.TestCase):
    """Tests for adaptive vision agent orchestration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = VisionAgent()
        
        self.metrics = {
            "avg_foreground_percentage": 3.7,
            "min_foreground_percentage": 0.0,
            "max_foreground_percentage": 8.6,
            "std_foreground_percentage": 1.9,
        }
        
        self.decision_trace = {
            "policy_name": "low_activity_refinement",
            "policy_version": "1.0",
            "decision_made": "follow_up_triggered",
            "reason": "Low activity detected",
            "condition_evaluated": {"threshold": 5.0, "actual_value": 3.7},
            "status": "complete",
            "followup_results": {"metrics": self.metrics},
        }
        
        self.report = {
            "analysis": {"metrics": self.metrics},
            "adaptive_analysis": self.decision_trace,
        }
    
    def test_agent_processes_analysis_result(self):
        """Agent should process analysis results and generate recommendation."""
        execution = self.agent.process_analysis_result(
            metrics=self.metrics,
            decision_trace=self.decision_trace,
            report=self.report,
        )
        
        self.assertIn("agent_version", execution)
        self.assertEqual(execution["agent_version"], "1.0")
        self.assertIn("execution_timestamp", execution)
        self.assertIn("workflow", execution)
        self.assertIn("recommendation", execution)
    
    def test_agent_workflow_structure(self):
        """Agent workflow should follow perception-decision-action-observation pattern."""
        execution = self.agent.process_analysis_result(
            metrics=self.metrics,
            decision_trace=self.decision_trace,
            report=self.report,
        )
        
        workflow = execution["workflow"]
        self.assertIn("observe_1", workflow)
        self.assertIn("decide", workflow)
        self.assertIn("act", workflow)
        self.assertIn("observe_2", workflow)
        self.assertIn("recommend", workflow)
    
    def test_agent_records_decision_details(self):
        """Agent should record policy decision details in workflow."""
        execution = self.agent.process_analysis_result(
            metrics=self.metrics,
            decision_trace=self.decision_trace,
            report=self.report,
        )
        
        decide = execution["workflow"]["decide"]
        self.assertEqual(decide["policy"], "low_activity_refinement")
        self.assertEqual(decide["decision"], "follow_up_triggered")
        self.assertIsNotNone(decide["reason"])


class TestArtifactPathSecurity(unittest.TestCase):
    """Tests for artifact serving security (path traversal prevention)."""
    
    def test_valid_run_id_format(self):
        """Valid run IDs should pass format validation."""
        valid_run_ids = [
            "run_20261023_111911_e964dd98",
            "run_20000101_000000_12345678",
        ]
        
        for run_id in valid_run_ids:
            # Should not raise
            self._validate_run_id(run_id)
    
    def test_invalid_run_id_format(self):
        """Invalid run IDs should be rejected."""
        invalid_run_ids = [
            "../../../etc/passwd",
            "run_20261023_111911_e964dd98/../../../",
            "run_20261023_111911_e964dd98\\..",
            "..\\run_20261023_111911_e964dd98",
        ]
        
        for run_id in invalid_run_ids:
            with self.assertRaises(ValueError):
                self._validate_run_id(run_id)
    
    def test_allowed_filenames(self):
        """Only whitelisted filenames should be accessible."""
        allowed = {
            "annotated_video.mp4",
            "heatmap.png",
            "heatmap_followup_16x16.png",
            "report.json",
            "run_metadata.json",
        }
        
        for filename in allowed:
            # Should not raise
            self._validate_filename(filename)
    
    def test_disallowed_filenames(self):
        """Non-whitelisted filenames should be rejected."""
        disallowed = [
            "config.json",
            "../artifacts/other_run/report.json",
            "report.json.bak",
            "../../etc/passwd",
        ]
        
        for filename in disallowed:
            with self.assertRaises(ValueError):
                self._validate_filename(filename)
    
    @staticmethod
    def _validate_run_id(run_id: str) -> bool:
        """Validate run_id format (mirrors API logic)."""
        if not run_id.startswith("run_") or "/" in run_id or "\\" in run_id or ".." in run_id:
            raise ValueError(f"Invalid run_id format: {run_id}")
        return True
    
    @staticmethod
    def _validate_filename(filename: str) -> bool:
        """Validate filename (mirrors API logic)."""
        allowed = {
            "annotated_video.mp4",
            "heatmap.png",
            "heatmap_followup_16x16.png",
            "report.json",
            "run_metadata.json",
        }
        
        if filename not in allowed:
            raise ValueError(f"Filename not in whitelist: {filename}")
        return True


class TestAdaptiveAnalysisIntegration(unittest.TestCase):
    """Integration tests for adaptive analysis with agent."""
    
    def test_low_activity_triggers_followup_and_recommendation(self):
        """Low activity should trigger follow-up and generate recommendation."""
        # Setup policy with low threshold
        policy = AdaptiveAnalysisPolicy(threshold=5.0)
        engine = AdaptiveAnalysisEngine(policy)
        
        # Low activity metrics
        metrics = {
            "avg_foreground_percentage": 3.7,
            "min_foreground_percentage": 0.0,
            "max_foreground_percentage": 8.6,
            "std_foreground_percentage": 1.9,
        }
        
        # Make decision
        decision_trace = engine.make_decision(metrics, {"fps": 30})
        
        # Verify follow-up is triggered
        self.assertEqual(decision_trace["decision_made"], "follow_up_triggered")
        
        # Simulate followup completion
        engine.record_followup_results(
            followup_metrics=metrics,
            processing_duration=0.14,
            comparison=None
        )
        
        # Get the updated trace
        decision_trace = engine.get_trace()
        
        # Process with agent
        agent = VisionAgent()
        execution = agent.process_analysis_result(
            metrics=metrics,
            decision_trace=decision_trace,
            report={"analysis": {"metrics": metrics}, "adaptive_analysis": decision_trace},
        )
        
        # Verify recommendation acknowledges low activity and refinement
        rec = execution["recommendation"]
        self.assertEqual(rec["category"], "low_activity_with_refinement")
        self.assertIn("3.7", str(rec["evidence"]))
    
    def test_high_activity_skips_followup_and_recommendation(self):
        """High activity should skip follow-up and recommend baseline analysis."""
        # Setup policy with high threshold for testing
        policy = AdaptiveAnalysisPolicy(threshold=2.0)
        engine = AdaptiveAnalysisEngine(policy)
        
        # High activity metrics
        metrics = {
            "avg_foreground_percentage": 10.0,
            "min_foreground_percentage": 5.0,
            "max_foreground_percentage": 20.0,
            "std_foreground_percentage": 3.0,
        }
        
        # Make decision
        decision_trace = engine.make_decision(metrics, {"fps": 30})
        
        # Verify follow-up is skipped
        self.assertEqual(decision_trace["decision_made"], "follow_up_skipped")
        
        # Process with agent
        agent = VisionAgent()
        execution = agent.process_analysis_result(
            metrics=metrics,
            decision_trace=decision_trace,
            report={"analysis": {"metrics": metrics}, "adaptive_analysis": decision_trace},
        )
        
        # Verify recommendation acknowledges sufficient activity
        rec = execution["recommendation"]
        self.assertEqual(rec["category"], "sufficient_activity")


if __name__ == "__main__":
    unittest.main()
