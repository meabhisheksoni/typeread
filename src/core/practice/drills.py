"""
TypeRead Weak-Key Drill Generator
Deterministic practice drill generation based on error patterns.
Can draw from imported document vocabulary or built-in high-frequency English corpus.
Zero cloud AI dependencies.
"""

from __future__ import annotations
import uuid
import random
from typing import List, Optional, Set

from src.contracts.types import WeakKeyDrillPractice

BUILT_IN_FREQUENCY_WORDS = [
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
    "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
    "system", "reader", "practice", "focus", "typing", "habit", "action", "rhythm",
    "character", "learning", "memory", "strength", "routine", "exercise", "progress",
    "accuracy", "velocity", "keyboard", "technique", "muscle", "retention", "skill"
]


class DrillGenerator:
    @classmethod
    def generate(
        cls,
        target_keys: Optional[List[str]] = None,
        target_bigrams: Optional[List[str]] = None,
        word_count: int = 100,
        document_words: Optional[List[str]] = None,
    ) -> WeakKeyDrillPractice:
        target_keys = target_keys or ["e", "t", "a", "o", "i"]
        target_bigrams = target_bigrams or []
        drill_id = str(uuid.uuid4())

        source_type = "document_vocabulary" if (document_words and len(document_words) >= 20) else "built_in_frequency_corpus"
        vocab = document_words if source_type == "document_vocabulary" else BUILT_IN_FREQUENCY_WORDS

        # Filter words that contain at least one of target_keys or target_bigrams
        lower_keys = [k.lower() for k in target_keys]
        lower_bigrams = [bg.lower() for bg in target_bigrams]

        matching_words: List[str] = []
        fallback_words: List[str] = []

        for w in vocab:
            w_clean = "".join(c for c in w if c.isalpha()).lower()
            if not w_clean or len(w_clean) < 2:
                continue
            fallback_words.append(w_clean)

            has_key = any(k in w_clean for k in lower_keys)
            has_bg = any(bg in w_clean for bg in lower_bigrams)

            if has_key or has_bg:
                matching_words.append(w_clean)

        if not matching_words:
            matching_words = fallback_words or BUILT_IN_FREQUENCY_WORDS

        # Deterministically select words
        # To make it repeatable for same input seed
        rng = random.Random(f"{drill_id}:{','.join(target_keys)}")
        selected_words = []
        for _ in range(word_count):
            selected_words.append(rng.choice(matching_words))

        passage = " ".join(selected_words)

        return WeakKeyDrillPractice(
            drill_id=drill_id,
            target_keys=target_keys,
            target_bigrams=target_bigrams,
            generated_passage=passage,
            word_count=len(selected_words),
            source=source_type,
        )
