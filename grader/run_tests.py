#!/usr/bin/env python3
"""
run_tests.py

Runs the hidden pytest suite for each challenge a student touched, and writes
a JSON summary of pass/fail counts.

Assumes this layout:
  challenges/<challenge-name>/tests/test_*.py   <- hidden grading tests
  solutions/<challenge-name>/solution.py         <- student's submission

The hidden tests import the student's solution via a SOLUTION_PATH env var,
so students never need to see or touch the test files themselves.
"""
import argparse
import json
import os
import re
import subprocess
import sys


def run_challenge_tests(challenge: str) -> dict:
    test_dir = os.path.join("challenges", challenge, "tests")
    solution_file = os.path.join("solutions", challenge, "solution.py")

    if not os.path.isdir(test_dir):
        return {"challenge": challenge, "passed": 0, "total": 0,
                "error": f"No test suite found for '{challenge}'"}

    if not os.path.isfile(solution_file):
        return {"challenge": challenge, "passed": 0, "total": 0,
                "error": f"No solution submitted at solutions/{challenge}/solution.py"}

    env = os.environ.copy()
    env["SOLUTION_PATH"] = os.path.abspath(solution_file)

    result = subprocess.run(
        ["pytest", test_dir, "-q", "--tb=short"],
        env=env, capture_output=True, text=True
    )

    passed, total = _parse_pytest_summary(result.stdout)

    return {
        "challenge": challenge,
        "passed": passed,
        "total": total,
        "stdout_tail": result.stdout[-1500:],  # keep logs short
    }


def _parse_pytest_summary(stdout: str) -> tuple[int, int]:
    """
    Parses pytest's final summary line, e.g.:
      "3 passed in 0.12s"
      "2 passed, 1 failed in 0.20s"
      "1 failed, 2 passed in 0.15s"
    Returns (passed_count, total_count).
    """
    passed_match = re.search(r"(\d+) passed", stdout)
    failed_match = re.search(r"(\d+) failed", stdout)
    error_match = re.search(r"(\d+) error", stdout)

    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    errored = int(error_match.group(1)) if error_match else 0

    total = passed + failed + errored
    return passed, total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student", required=True)
    parser.add_argument("--changed", required=True, help="newline-separated challenge names")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    challenges = [c.strip() for c in args.changed.splitlines() if c.strip()]
    if not challenges:
        print("No changed challenges detected; nothing to grade.")
        challenges = []

    details = [run_challenge_tests(c) for c in challenges]
    overall_pass = all(d.get("total", 0) > 0 and d["passed"] == d["total"] for d in details) if details else False

    output = {
        "student": args.student,
        "overall_pass": overall_pass,
        "details": details,
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
