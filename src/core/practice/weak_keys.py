"""
TypeRead Weak-Key & Bigram Aggregator
Tracks character and bigram error rates and common substitutions.
"""

from __future__ import annotations
from collections import defaultdict, Counter
from typing import List, Dict, Tuple

from src.contracts.types import (
    TypingErrorRecord,
    WeakKeyAggregate,
    WeakBigramAggregate,
    SubstitutionCount,
)


class WeakKeyAggregator:
    @classmethod
    def aggregate_errors(
        cls,
        errors: List[TypingErrorRecord],
        character_totals: Dict[str, int],
        bigram_totals: Dict[str, int],
    ) -> Tuple[List[WeakKeyAggregate], List[WeakBigramAggregate]]:
        """
        Aggregates errors into WeakKeyAggregate and WeakBigramAggregate list.
        """
        key_error_counts: Counter[str] = Counter()
        substitutions: Dict[str, Counter[str]] = defaultdict(Counter)

        for err in errors:
            exp = err.expected_char
            act = err.actual_char
            key_error_counts[exp] += 1
            if act:
                substitutions[exp][act] += 1

        weak_keys: List[WeakKeyAggregate] = []
        for char, err_count in key_error_counts.most_common():
            total_occ = character_totals.get(char, err_count)
            err_rate = round((err_count / max(1, total_occ)) * 100.0, 2)

            subs = [
                SubstitutionCount(substituted_for=sub_char, count=sub_count)
                for sub_char, sub_count in substitutions[char].most_common(5)
            ]

            weak_keys.append(
                WeakKeyAggregate(
                    character=char,
                    error_count=err_count,
                    total_occurrences=total_occ,
                    error_rate_pct=err_rate,
                    common_substitutions=subs,
                )
            )

        # Bigram errors
        weak_bigrams: List[WeakBigramAggregate] = []
        # Error records sorted by timestamp
        sorted_errors = sorted(errors, key=lambda e: e.timestamp_ms)
        bigram_error_counts: Counter[str] = Counter()

        for idx in range(1, len(sorted_errors)):
            prev = sorted_errors[idx - 1]
            curr = sorted_errors[idx]
            # If consecutive position
            if curr.position == prev.position + 1:
                bigram = prev.expected_char + curr.expected_char
                bigram_error_counts[bigram] += 1

        for bg, err_count in bigram_error_counts.most_common():
            total_occ = bigram_totals.get(bg, err_count)
            err_rate = round((err_count / max(1, total_occ)) * 100.0, 2)
            weak_bigrams.append(
                WeakBigramAggregate(
                    bigram=bg,
                    error_count=err_count,
                    total_occurrences=total_occ,
                    error_rate_pct=err_rate,
                )
            )

        return weak_keys, weak_bigrams
