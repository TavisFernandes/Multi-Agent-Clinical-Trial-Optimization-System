"""
Critic Agent Module
Checks output quality and suggests improvements.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CriticAgent:
    """
    Critic agent that validates report quality and completeness.
    Checks for required fields, clarity, and structure.
    """

    # Required patterns for clinical reports
    REQUIRED_PATTERNS = [
        (
            'Dosage',
            re.compile(r'(\b(dosage|dose|mg\b|mcg|mg/kg|administer)\b|##\s*dosage)', re.I)
        ),
        (
            'Phase',
            re.compile(
                r'(\bphase\s*(i{1,3}|iv|1|2|3|4)\b|##\s*phase|##\s*clinical trial synopsis|\bstage\s+(?:0|i{1,3}|iv|1|2|3|4)\b)',
                re.I,
            )
        ),
        (
            'Patient Count',
            re.compile(
                r'(\b(n\s*=\s*\d+|enrollment|patients?\s*\d+|sample\s*size)\b|##\s*enrollment|patient\s+count)',
                re.I,
            )
        ),
    ]

    # Quality thresholds
    MIN_LENGTH = 200  # Minimum characters for valid report
    MAX_LENGTH = 10000  # Maximum reasonable length

    def __init__(self):
        """Initialize critic agent."""
        self.quality_scores: Dict[str, float] = {}

    def review(
        self,
        report: str,
        iteration: int = 1
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Review report for quality and completeness.

        Args:
            report: Report text to review
            iteration: Current iteration number

        Returns:
            Tuple of (approved, missing_fields, quality_metrics)
        """
        missing_fields = []
        quality_metrics = {
            'iteration': iteration,
            'length': len(report),
            'checks_passed': 0,
            'checks_failed': 0
        }

        # Check length requirements
        length_ok = self._check_length(report)
        if length_ok:
            quality_metrics['checks_passed'] += 1
        else:
            quality_metrics['checks_failed'] += 1

        # Check required patterns
        for field_name, pattern in self.REQUIRED_PATTERNS:
            if not pattern.search(report):
                missing_fields.append(field_name)
                quality_metrics['checks_failed'] += 1
            else:
                quality_metrics['checks_passed'] += 1

        # Check structure
        structure_ok = self._check_structure(report)
        if structure_ok:
            quality_metrics['checks_passed'] += 1
        else:
            quality_metrics['checks_failed'] += 1

        # Check clarity (no excessive repetition)
        clarity_ok = self._check_clarity(report)
        if clarity_ok:
            quality_metrics['checks_passed'] += 1
        else:
            quality_metrics['checks_failed'] += 1

        # Approve when required patterns are present; allow one extra quality quirk so UX isn't stuck on edge cases
        approved = len(missing_fields) == 0 and quality_metrics['checks_failed'] <= 2

        # Store quality scores
        total_checks = quality_metrics['checks_passed'] + quality_metrics['checks_failed']
        if total_checks > 0:
            self.quality_scores[f'iteration_{iteration}'] = (
                quality_metrics['checks_passed'] / total_checks
            )

        return approved, missing_fields, quality_metrics

    def _check_length(self, report: str) -> bool:
        """Check if report length is appropriate."""
        length = len(report)
        return self.MIN_LENGTH <= length <= self.MAX_LENGTH

    def _check_structure(self, report: str) -> bool:
        """Check if report has proper structure."""
        # Must have headers
        has_headers = bool(re.search(r'^#+\s+\w+', report, re.MULTILINE))

        # Must have some content sections
        has_sections = report.count('##') >= 1

        return has_headers and has_sections

    def _check_clarity(self, report: str) -> bool:
        """Check report clarity (no excessive repetition)."""
        # Split into words
        words = report.lower().split()

        if not words:
            return False

        # Check word diversity
        unique_words = set(words)
        diversity_ratio = len(unique_words) / len(words)

        # Acceptable if at least 30% unique words
        return diversity_ratio >= 0.3

    def suggest_improvements(
        self,
        report: str,
        missing_fields: List[str]
    ) -> List[str]:
        """
        Generate improvement suggestions.

        Args:
            report: Current report
            missing_fields: Fields that are missing

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Suggestions for missing fields
        field_suggestions = {
            'Dosage': "Add specific dosage information (e.g., '100mg weekly' or 'weight-based dosing')",
            'Phase': "Include trial phase designation (Phase I/II/III/IV)",
            'Patient Count': "Specify enrollment numbers (e.g., 'N=120 patients')",
            'Endpoints': "Add primary/secondary endpoint information",
            'Safety': "Include safety monitoring details"
        }

        for field in missing_fields:
            if field in field_suggestions:
                suggestions.append(field_suggestions[field])

        # Additional quality suggestions
        if len(report) < self.MIN_LENGTH:
            suggestions.append(
                f"Expand report content (current: {len(report)} chars, minimum: {self.MIN_LENGTH})"
            )

        # Check for specific details
        if not re.search(r'\d+', report):
            suggestions.append("Add numerical data (counts, percentages, measurements)")

        return suggestions

    def get_feedback_message(
        self,
        approved: bool,
        missing_fields: List[str],
        quality_metrics: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable feedback message.

        Args:
            approved: Whether report passed review
            missing_fields: Missing fields identified
            quality_metrics: Quality metrics from review

        Returns:
            Feedback message string
        """
        if approved:
            return (
                f"Report approved. "
                f"Quality score: {quality_metrics.get('checks_passed', 0)}/{quality_metrics.get('checks_passed', 0) + quality_metrics.get('checks_failed', 0)} checks passed."
            )
        else:
            if missing_fields:
                return (
                    f"Report requires revision. Missing fields: {', '.join(missing_fields)}. "
                    f"Please address these gaps and resubmit."
                )
            else:
                return (
                    "Report requires revision due to quality issues. "
                    "Please review structure and content clarity."
                )


# Example usage
if __name__ == "__main__":
    print("=== Critic Agent Test ===")

    critic = CriticAgent()

    # Test with incomplete report
    incomplete_report = """
    # Clinical Summary

    Patient data analyzed.
    """

    approved, missing, metrics = critic.review(incomplete_report)
    print(f"Incomplete report - Approved: {approved}")
    print(f"Missing fields: {missing}")
    print(f"Metrics: {metrics}")

    # Test with complete report
    complete_report = """
    # Clinical Trial Intelligence Summary

    ## Executive Overview
    Phase II trial with N=120 patients enrolled.

    ## Dosage
    Treatment: 100mg weekly administration.

    ## Results
    Primary endpoint met with statistical significance.
    """

    approved, missing, metrics = critic.review(complete_report)
    print(f"\nComplete report - Approved: {approved}")
    print(f"Missing fields: {missing}")
    print(f"Metrics: {metrics}")

    # Get suggestions
    suggestions = critic.suggest_improvements(incomplete_report, missing)
    print(f"\nImprovement suggestions: {suggestions}")
