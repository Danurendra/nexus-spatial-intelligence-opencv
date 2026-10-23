"""Adaptive Vision Agent for Nexus Spatial Intelligence.

Orchestrates the vision analysis pipeline and provides grounded recommendations
based on observed metrics, policy decisions, and actual analysis results.

The agent implements a simple perception-decision-action loop:
1. Observe: Run OpenCV analysis and collect metrics
2. Decide: Evaluate the adaptive refinement policy
3. Act: Execute follow-up analysis if metrics warrant it
4. Observe again: Inspect follow-up results if available
5. Recommend: Generate evidence-grounded suggestions for next steps
6. Record: Preserve the complete decision trace for inspection
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class VisionAgentRecommendation:
    """Generates evidence-grounded recommendations from analysis results."""
    
    @staticmethod
    def generate(
        metrics: Dict[str, float],
        decision_trace: Dict[str, Any],
        followup_performed: bool = False,
        followup_metrics: Optional[Dict[str, float]] = None,
        followup_error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a recommendation based on analysis results and policy decision.
        
        Args:
            metrics: Baseline motion metrics from analysis
            decision_trace: Policy decision trace from adaptive engine
            followup_performed: Whether follow-up analysis was attempted
            followup_metrics: Results from follow-up if available
            followup_error: Error message if follow-up failed
            
        Returns:
            Recommendation dict with: category, confidence, evidence, next_steps, notes
        """
        avg_fg = metrics.get("avg_foreground_percentage", 0.0)
        min_fg = metrics.get("min_foreground_percentage", 0.0)
        max_fg = metrics.get("max_foreground_percentage", 0.0)
        std_fg = metrics.get("std_foreground_percentage", 0.0)
        
        decision = decision_trace.get("decision_made", "unknown")
        status = decision_trace.get("status", "unknown")
        
        recommendation = {
            "timestamp": datetime.now().isoformat(),
            "agent_version": "1.0",
            "based_on": {
                "policy": decision_trace.get("policy_name"),
                "threshold": decision_trace.get("condition_evaluated", {}).get("threshold"),
                "actual_avg_foreground": avg_fg,
            },
            "category": None,
            "confidence": "high",  # All observations are from real analysis
            "evidence": [],
            "next_steps": [],
            "notes": None,
        }
        
        # Case 1: Low activity, follow-up triggered and completed successfully
        if decision == "follow_up_triggered" and status == "complete" and not followup_error:
            recommendation["category"] = "low_activity_with_refinement"
            recommendation["evidence"] = [
                f"Average foreground activity: {avg_fg:.2f}%",
                f"Activity range: {min_fg:.2f}% to {max_fg:.2f}%",
                f"Policy threshold: {decision_trace.get('condition_evaluated', {}).get('threshold')}%",
                "Refinement from 8×8 to 16×16 spatial grid performed",
                "Follow-up heatmap generated",
            ]
            recommendation["next_steps"] = [
                "1. Review the refined 16×16 heatmap for localized activity patterns",
                "2. Compare against the baseline 8×8 heatmap",
                "3. Check if low activity is explained by scene characteristics:",
                "   • Static scene or camera fixed on empty area",
                "   • Illumination conditions (shadows, backlighting)",
                "   • Occlusion (obstruction of view, blind spots)",
                "   • Video quality or compression artifacts",
                "4. If patterns suggest monitoring gaps, adjust camera placement or ROI",
            ]
            recommendation["notes"] = (
                "Low activity detected. Grid refinement provides higher spatial resolution "
                "of the same frames—not additional motion detection. Use refined heatmap to "
                "identify whether activity is truly absent or localized to a specific region."
            )
        
        # Case 2: Low activity, follow-up triggered but failed
        elif decision == "follow_up_triggered" and status == "followup_failed":
            recommendation["category"] = "low_activity_refinement_failed"
            recommendation["confidence"] = "medium"
            recommendation["evidence"] = [
                f"Average foreground activity: {avg_fg:.2f}%",
                f"Policy threshold: {decision_trace.get('condition_evaluated', {}).get('threshold')}%",
                "Refinement was triggered but failed",
                f"Error: {followup_error}" if followup_error else "Follow-up error occurred",
            ]
            recommendation["next_steps"] = [
                "1. Review baseline 8×8 heatmap despite refinement failure",
                "2. Log the refinement error for debugging",
                "3. Proceed with baseline analysis for next steps",
                "4. Consider re-running analysis if transient error occurred",
            ]
            recommendation["notes"] = (
                f"Low activity detected but follow-up refinement encountered an error: {followup_error}. "
                "Baseline heatmap is still available for review."
            )
        
        # Case 3: Sufficient activity, follow-up skipped
        elif decision == "follow_up_skipped":
            recommendation["category"] = "sufficient_activity"
            recommendation["evidence"] = [
                f"Average foreground activity: {avg_fg:.2f}%",
                f"Activity range: {min_fg:.2f}% to {max_fg:.2f}%",
                f"Policy threshold: {decision_trace.get('condition_evaluated', {}).get('threshold')}%",
                "Activity level exceeds refinement threshold",
                "Baseline 8×8 grid deemed adequate",
            ]
            recommendation["next_steps"] = [
                "1. Review the baseline 8×8 heatmap",
                "2. Inspect the annotated video overlay",
                "3. Identify hotspots of activity concentration",
                "4. Consider spatial or temporal subsampling for efficiency",
                "5. If specific regions require detail, run targeted re-analysis",
            ]
            recommendation["notes"] = (
                "Sufficient activity detected. The baseline 8×8 spatial grid provides "
                "adequate resolution for this scene. Use the heatmap to identify "
                "activity patterns and concentrate monitoring on high-activity regions."
            )
        
        # Case 4: Unable to make recommendation (missing data)
        else:
            recommendation["category"] = "insufficient_data"
            recommendation["confidence"] = "low"
            recommendation["evidence"] = [
                f"Decision made: {decision}",
                f"Status: {status}",
                f"Follow-up error: {followup_error if followup_error else 'none'}",
            ]
            recommendation["next_steps"] = [
                "1. Verify analysis completed successfully",
                "2. Check logs for errors or warnings",
                "3. Re-run analysis if needed",
            ]
            recommendation["notes"] = (
                "Unable to generate a specific recommendation due to missing or ambiguous data. "
                "Review the complete decision trace and error logs."
            )
        
        return recommendation


class VisionAgent:
    """
    Adaptive Vision Agent orchestrating the analysis pipeline.
    
    Manages the perception-decision-action loop and generates recommendations
    grounded in actual analysis metrics and policy decisions.
    """
    
    def __init__(self):
        """Initialize the agent."""
        self.agent_version = "1.0"
        self.last_execution = None
    
    def process_analysis_result(
        self,
        metrics: Dict[str, float],
        decision_trace: Dict[str, Any],
        report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process analysis results and generate recommendation.
        
        Args:
            metrics: Motion metrics from baseline analysis
            decision_trace: Policy decision and trace from adaptive engine
            report: Complete analysis report (includes adaptive_analysis section)
            
        Returns:
            Agent execution result with recommendation and trace
        """
        self.last_execution = datetime.now().isoformat()
        
        # Extract follow-up status from decision trace
        status = decision_trace.get("status", "unknown")
        followup_performed = decision_trace.get("decision_made") == "follow_up_triggered"
        followup_error = None
        followup_metrics = None
        
        # Check for errors in the decision trace
        if status == "followup_failed":
            warnings = decision_trace.get("warnings", [])
            if warnings and isinstance(warnings, list) and len(warnings) > 0:
                followup_error = warnings[0].get("error", "Unknown error")
        
        # Extract follow-up metrics if available
        if decision_trace.get("followup_results"):
            followup_metrics = decision_trace.get("followup_results", {}).get("metrics")
        
        # Generate recommendation
        recommendation = VisionAgentRecommendation.generate(
            metrics=metrics,
            decision_trace=decision_trace,
            followup_performed=followup_performed,
            followup_metrics=followup_metrics,
            followup_error=followup_error,
        )
        
        # Build agent execution record
        execution = {
            "agent_version": self.agent_version,
            "execution_timestamp": self.last_execution,
            "workflow": {
                "observe_1": {
                    "step": "Run baseline OpenCV analysis",
                    "result": f"Collected metrics: avg={metrics.get('avg_foreground_percentage'):.2f}%",
                },
                "decide": {
                    "step": "Evaluate adaptive refinement policy",
                    "policy": decision_trace.get("policy_name"),
                    "condition": decision_trace.get("condition_evaluated", {}).get("description"),
                    "decision": decision_trace.get("decision_made"),
                    "reason": decision_trace.get("reason"),
                },
                "act": {
                    "step": "Execute follow-up if triggered",
                    "action_taken": "follow-up refinement (16×16 grid)" if decision_trace.get("decision_made") == "follow_up_triggered" else "no follow-up",
                    "status": status,
                },
                "observe_2": {
                    "step": "Inspect follow-up results if available",
                    "followup_performed": followup_performed,
                    "followup_error": followup_error,
                },
                "recommend": {
                    "step": "Generate evidence-grounded recommendation",
                    "category": recommendation.get("category"),
                    "confidence": recommendation.get("confidence"),
                }
            },
            "recommendation": recommendation,
            "decision_trace": decision_trace,
        }
        
        logger.info(f"Agent execution complete: {recommendation.get('category')} "
                   f"(confidence: {recommendation.get('confidence')})")
        
        return execution
    
    def get_trace(self) -> Dict[str, Any]:
        """
        Get the last execution trace for inspection.
        
        Returns:
            Last execution record if available
        """
        return {
            "agent_version": self.agent_version,
            "last_execution": self.last_execution,
        }
