"""Ensure sharing the policy preserves the benchmark's original prompt."""

import hashlib
import unittest
from pathlib import Path

from app import assessment_policy
from evaluation import benchmark


class SharedPolicyTests(unittest.TestCase):
    def test_policy_file_is_unchanged_after_move(self):
        policy = Path(assessment_policy.__file__).with_name("assessment_policy.txt")
        # Captured from evaluation/policy.txt before moving it into app/.
        # Normalize newlines so Windows and Linux Git checkouts compare equally.
        self.assertEqual(
            hashlib.sha256(policy.read_text(encoding="utf-8").encode("utf-8")).hexdigest(),
            "f69ec61b080159272ff00a09e078a09ff16fbf00a80a64941e37cd4dc60716f0",
        )

    def test_shared_prompt_matches_original_benchmark(self):
        # Captured from the original benchmark.build_system_prompt() output.
        prompt = assessment_policy.build_system_prompt().encode("utf-8")
        self.assertEqual(
            hashlib.sha256(prompt).hexdigest(),
            "b85b7a504035d34b62b167b9e7c8be9b239d613e779cea23ff16248ca3a9bb55",
        )
        self.assertIs(benchmark.build_system_prompt, assessment_policy.build_system_prompt)


if __name__ == "__main__":
    unittest.main()
