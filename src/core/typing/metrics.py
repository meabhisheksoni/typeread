"""
TypeRead Typing Metrics Calculator
Mathematical standards adhering strictly to ARCH_DECISIONS.md:
- Gross WPM = ((total_chars / 5) / (active_seconds / 60))
- Net WPM = max(0.0, ((correct_chars / 5) / (active_seconds / 60)))
- Accuracy (%) = (correct_keystrokes / total_keystrokes) * 100
- Consistency (%) = 100 * max(0.0, 1.0 - (sigma / (mu + epsilon)))
"""

from __future__ import annotations
import math
from typing import List, Optional

from src.contracts.types import KeystrokeEvaluation, TypingMetrics


class MetricsCalculator:
    def __init__(self, pause_threshold_seconds: float = 2.0):
        self.pause_threshold_seconds = pause_threshold_seconds
        self.evaluations: List[KeystrokeEvaluation] = []
        self.correct_count = 0
        self.incorrect_count = 0
        self.backspace_count = 0
        self.active_seconds = 0.0
        self._last_timestamp_ms: Optional[int] = None
        self._interval_wpm_samples: List[float] = []
        self._current_interval_chars = 0
        self._current_interval_seconds = 0.0

    def add_evaluation(self, eval_result: KeystrokeEvaluation) -> None:
        self.evaluations.append(eval_result)

        if eval_result.is_backspace:
            self.backspace_count += 1
        elif eval_result.is_correct:
            self.correct_count += 1
        else:
            self.incorrect_count += 1

        # Track active time
        if self._last_timestamp_ms is not None:
            delta_ms = eval_result.timestamp_ms - self._last_timestamp_ms
            if delta_ms > 0:
                delta_sec = delta_ms / 1000.0
                # If delta is less than pause threshold, accumulate active seconds
                if delta_sec <= self.pause_threshold_seconds:
                    self.active_seconds += delta_sec
                    self._current_interval_seconds += delta_sec
                else:
                    # User paused, only add a nominal active fraction
                    self.active_seconds += 0.2
                    self._current_interval_seconds += 0.2
        else:
            # First keystroke
            self.active_seconds += 0.1
            self._current_interval_seconds += 0.1

        self._last_timestamp_ms = eval_result.timestamp_ms

        if not eval_result.is_backspace:
            self._current_interval_chars += 1

        # Accumulate 1-second burst intervals for consistency calculation
        if self._current_interval_seconds >= 1.0:
            burst_wpm = (self._current_interval_chars / 5.0) / (self._current_interval_seconds / 60.0)
            self._interval_wpm_samples.append(burst_wpm)
            self._current_interval_chars = 0
            self._current_interval_seconds = 0.0

    def compute_metrics(self) -> TypingMetrics:
        total_non_backspace = self.correct_count + self.incorrect_count
        total_keystrokes = total_non_backspace + self.backspace_count

        active_mins = self.active_seconds / 60.0 if self.active_seconds > 0 else 0.0

        if active_mins > 0:
            gross_wpm = round((total_non_backspace / 5.0) / active_mins, 2)
            net_wpm = round(max(0.0, (self.correct_count / 5.0) / active_mins), 2)
        else:
            gross_wpm = 0.0
            net_wpm = 0.0

        if total_keystrokes > 0:
            accuracy_pct = round((self.correct_count / float(total_keystrokes)) * 100.0, 2)
            error_rate_pct = round((self.incorrect_count / float(total_keystrokes)) * 100.0, 2)
        else:
            accuracy_pct = 100.0
            error_rate_pct = 0.0

        # Consistency calculation
        consistency_pct = self._calculate_consistency()

        return TypingMetrics(
            net_wpm=net_wpm,
            gross_wpm=gross_wpm,
            accuracy_pct=accuracy_pct,
            error_rate_pct=error_rate_pct,
            total_keystrokes=total_keystrokes,
            correct_keystrokes=self.correct_count,
            incorrect_keystrokes=self.incorrect_count,
            backspace_count=self.backspace_count,
            active_seconds=round(self.active_seconds, 2),
            consistency_pct=round(consistency_pct, 2),
        )

    def _calculate_consistency(self) -> float:
        samples = list(self._interval_wpm_samples)
        if self._current_interval_seconds > 0.2 and self._current_interval_chars > 0:
            samples.append((self._current_interval_chars / 5.0) / (self._current_interval_seconds / 60.0))

        if len(samples) < 2:
            return 100.0

        mu = sum(samples) / len(samples)
        variance = sum((x - mu) ** 2 for x in samples) / len(samples)
        sigma = math.sqrt(variance)

        epsilon = 1e-6
        coeff_var = sigma / (mu + epsilon)
        consistency = max(0.0, 100.0 * (1.0 - coeff_var))
        return min(100.0, consistency)
