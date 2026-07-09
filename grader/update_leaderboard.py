#!/usr/bin/env python3
"""
update_leaderboard.py

Merges the latest grading results into leaderboard.json (persistent score
store) and regenerates leaderboard.md (human-readable table), sorted by
total challenges solved then total tests passed.
"""
import argparse
import json
import os

LEADERBOARD_JSON = "leaderboard.json"
LEADERBOARD_MD = "leaderboard.md"


def load_leaderboard() -> dict:
    if os.path.isfile(LEADERBOARD_JSON):
        with open(LEADERBOARD_JSON) as f:
            return json.load(f)
    return {}


def save_leaderboard(data: dict):
    with open(LEADERBOARD_JSON, "w") as f:
        json.dump(data, f, indent=2)


def render_markdown(data: dict):
    rows = []
    for student, info in data.items():
        solved = sum(1 for c in info["challenges"].values() if c["passed"] == c["total"] and c["total"] > 0)
        total_tests_passed = sum(c["passed"] for c in info["challenges"].values())
        rows.append((student, solved, total_tests_passed))

    rows.sort(key=lambda r: (-r[1], -r[2]))

    lines = ["# Leaderboard", "", "| Rank | Student | Challenges Solved | Tests Passed |",
             "|------|---------|--------------------|--------------|"]
    for i, (student, solved, tests) in enumerate(rows, start=1):
        lines.append(f"| {i} | {student} | {solved} | {tests} |")

    with open(LEADERBOARD_MD, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    args = parser.parse_args()

    with open(args.results) as f:
        results = json.load(f)

    student = results["student"]
    data = load_leaderboard()
    data.setdefault(student, {"challenges": {}})

    for detail in results["details"]:
        if "error" in detail and detail.get("total", 0) == 0:
            continue
        data[student]["challenges"][detail["challenge"]] = {
            "passed": detail["passed"],
            "total": detail["total"],
        }

    save_leaderboard(data)
    render_markdown(data)


if __name__ == "__main__":
    main()
