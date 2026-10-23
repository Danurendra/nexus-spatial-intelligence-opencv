"""Adaptive analysis decision engine for Nexus Spatial Intelligence.

Implements configurable decision policies for follow-up analysis based on
initial video observations. The adaptive behavior must be deterministic and
the decision must demonstrably affect the next action taken.
"""

import logging
from typing import Dict, Any, Optional, Tuple
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class AdaptiveAnalysisPolicy:
    """Defines and evaluates adaptive analysis policies."""
    
    def __init__(self, policy_name: str = "low_activity_refinement", threshold: float = 5.0):
        """
        Initialize adaptive policy.
        
        Args:
            policy_name: Name of the policy (e.g., "low_activity_refinement")
            threshold: Foreground percentage threshold for triggering follow-up (default: 5%)
        """
        self.policy_name = policy_name
        self.policy_version = "1.0"
        self.threshold = threshold
    
    def should_trigger_followup(self, initial_metrics: Dict[str, float]) -> bool:
        """
        Determine if follow-up analysis should be triggered based on initial metrics.
        
        Args:
            initial_metrics: Dictionary with avg_foreground_percentage and other metrics
            
        Returns:
            True if follow-up should be triggered, False otherwise
        """
        avg_foreground = initial_metrics.get("avg_foreground_percentage", 0.0)
        
        if self.policy_name == "low_activity_refinement":
            # Trigger if motion is low (below threshold)
            should_trigger = avg_foreground < self.threshold
            logger.info(f"Policy '{self.policy_name}': avg_foreground={avg_foreground:.2f}%, "
                       f"threshold={self.threshold}% -> trigger={should_trigger}")
            return should_trigger
        else:
            logger.warning(f"Unknown policy: {self.policy_name}")
            return False


class AdaptiveAnalysisEngine:
    """Execute and record adaptive analysis decisions and follow-up actions."""
    
    def __init__(self, policy: AdaptiveAnalysisPolicy):
        """
        Initialize adaptive analysis engine.
        
        Args:
            policy: AdaptiveAnalysisPolicy instance
        """
        self.policy = policy
        self.decision_trace = None
    
    def make_decision(self, initial_metrics: Dict[str, float], 
                     metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make adaptive decision based on initial analysis.
        
        Args:
            initial_metrics: Metrics from baseline analysis
            metadata: Video metadata
            
        Returns:
            Decision trace with decision, reason, and follow-up configuration
        """
        decision_timestamp = datetime.now().isoformat()
        should_trigger = self.policy.should_trigger_followup(initial_metrics)
        
        trace = {
            "policy_name": self.policy.policy_name,
            "policy_version": self.policy.policy_version,
            "decision_timestamp": decision_timestamp,
            "initial_observations": {
                "avg_foreground_percentage": initial_metrics.get("avg_foreground_percentage"),
                "min_foreground_percentage": initial_metrics.get("min_foreground_percentage"),
                "max_foreground_percentage": initial_metrics.get("max_foreground_percentage"),
                "std_foreground_percentage": initial_metrics.get("std_foreground_percentage"),
            },
            "condition_evaluated": {
                "description": f"avg_foreground_percentage < {self.policy.threshold}%",
                "threshold": self.policy.threshold,
                "actual_value": initial_metrics.get("avg_foreground_percentage"),
            },
            "decision_made": "follow_up_triggered" if should_trigger else "follow_up_skipped",
            "reason": self._get_reason(should_trigger, initial_metrics),
            "followup_configuration": None,
            "followup_results": None,
            "status": "pending",
            "warnings": [],
        }
        
        if should_trigger:
            trace["followup_configuration"] = {
                "action": "re_analyze_with_finer_grid",
                "baseline_grid_size": 8,
                "followup_grid_size": 16,
                "frames_to_process": "all (same as baseline)",
                "reason": "Low activity detected; refining spatial resolution for better detection",
            }
        
        self.decision_trace = trace
        return trace
    
    def _get_reason(self, should_trigger: bool, metrics: Dict[str, float]) -> str:
        """Generate human-readable reason for the decision."""
        avg_fg = metrics.get("avg_foreground_percentage", 0.0)
        
        if self.policy.policy_name == "low_activity_refinement":
            if should_trigger:
                return (f"Low activity detected (avg {avg_fg:.2f}% < threshold {self.policy.threshold}%). "
                       f"Follow-up analysis will refine spatial grid from 8x8 to 16x16 for better region detection.")
            else:
                return (f"Sufficient activity detected (avg {avg_fg:.2f}% >= threshold {self.policy.threshold}%). "
                       f"Baseline 8x8 spatial grid is adequate; follow-up analysis skipped.")
        
        return "Decision made per policy"
    
    def record_followup_results(self, followup_metrics: Dict[str, float], 
                               processing_duration: float, 
                               comparison: Dict[str, Any] = None):
        """
        Record results from follow-up analysis.
        
        Args:
            followup_metrics: Metrics from follow-up analysis
            processing_duration: Time spent on follow-up analysis
            comparison: Optional comparison between baseline and follow-up
        """
        if not self.decision_trace:
            logger.warning("No decision trace to record follow-up results in")
            return
        
        self.decision_trace["followup_results"] = {
            "metrics": followup_metrics,
            "processing_duration_seconds": float(processing_duration),
            "grid_size_used": 16,
        }
        
        if comparison:
            self.decision_trace["followup_results"]["comparison"] = comparison
        
        self.decision_trace["status"] = "complete"
    
    def record_followup_error(self, error: str, error_details: str = None):
        """
        Record that follow-up analysis failed.
        
        Args:
            error: Error message
            error_details: Optional detailed error information
        """
        if not self.decision_trace:
            logger.warning("No decision trace to record follow-up error in")
            return
        
        self.decision_trace["status"] = "followup_failed"
        self.decision_trace["warnings"].append({
            "type": "followup_error",
            "error": error,
            "details": error_details,
        })
    
    def get_trace(self) -> Dict[str, Any]:
        """
        Get the complete decision trace.
        
        Returns:
            Dictionary with decision trace
        """
        return self.decision_trace


def compare_analysis_results(baseline_metrics: Dict[str, float],
                            followup_metrics: Dict[str, float]) -> Dict[str, Any]:
    """
    Compare baseline and follow-up analysis results.
    
    Args:
        baseline_metrics: Metrics from baseline analysis (8x8 grid)
        followup_metrics: Metrics from follow-up analysis (16x16 grid)
        
    Returns:
        Comparison dictionary with differences and observations
    """
    if not followup_metrics:
        return {
            "note": "Follow-up analysis not performed",
            "differences": None,
        }
    
    comparison = {
        "baseline": {
            "grid_size": 8,
            "avg_foreground_percentage": baseline_metrics.get("avg_foreground_percentage"),
        },
        "followup": {
            "grid_size": 16,
            "avg_foreground_percentage": followup_metrics.get("avg_foreground_percentage"),
        },
        "differences": {
            "avg_foreground_percentage_change": (
                followup_metrics.get("avg_foreground_percentage", 0.0) - 
                baseline_metrics.get("avg_foreground_percentage", 0.0)
            ),
            "note": "Finer grid may detect different spatial patterns; compare carefully",
        },
        "interpretation": (
            "Grid refinement provides higher spatial resolution but processes same frames. "
            "Differences reflect spatial distribution changes, not additional motion detection. "
            "Both results measure foreground activity; neither should be called 'accuracy'."
        ),
    }
    
    return comparison
