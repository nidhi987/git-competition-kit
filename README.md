# Git-based Coding Competition Kit

Automates a coding competition where each student pushes to their own
protected branch and GitHub Actions auto-grades every submission.

## How it works

1. You create challenges under `challenges/<name>/` — a `problem.md` and a
   hidden `tests/` folder with pytest tests.
2. Run `setup-student-branches.sh` once. For every student in `students.csv`
   it creates a `submissions/<github-username>` branch and locks it so
   **only that student can push to it** (GitHub branch protection).
3. Students clone the repo, `git checkout submissions/<their-username>`,
   add their solution at `solutions/<challenge>/solution.py`, and push.
4. GitHub Actions (`.github/workflows/autograde.yml`) automatically:
   - detects which challenge(s) they touched
   - runs the hidden tests against their solution
   - posts a pass/fail Check on their commit
   - updates `leaderboard.md` on `main` via a bot commit

## One-time setup

```bash
# 1. Create an empty repo on GitHub, e.g. myorg/coding-comp, and push
#    this kit's contents to its `main` branch first.

# 2. Install & auth the GitHub CLI
brew install gh   # or see https://cli.github.com
gh auth login

# 3. Fill in students.csv with github_username,student_name rows

# 4. Create + lock a branch per student
chmod +x setup-student-branches.sh
./setup-student-branches.sh myorg/coding-comp students.csv
```

## Adding a new challenge

1. `mkdir -p challenges/challenge-2/tests`
2. Write `challenges/challenge-2/problem.md` describing the task and the
   exact function signature students must implement.
3. Write pytest tests in `challenges/challenge-2/tests/test_*.py`. Load the
   student's code like this (see `challenge-1` for a full example):

   ```python
   import importlib.util, os
   spec = importlib.util.spec_from_file_location("solution", os.environ["SOLUTION_PATH"])
   module = importlib.util.module_from_spec(spec)
   spec.loader.exec_module(module)
   ```

4. Commit to `main`. Students will see the new `problem.md` next time they
   pull/rebase from main (see below).

## Keeping student branches in sync with new challenges

Since students work on long-lived branches, periodically merge `main` into
each submission branch so they receive new challenges:

```bash
for b in $(git branch -r | grep submissions/); do
  git checkout "${b#origin/}"
  git merge origin/main --no-edit
  git push
done
```

## Notes & caveats

- **Branch enforcement is done via the "guard" job**, not GitHub's native
  branch-protection push restrictions (those need a paid Team/Enterprise
  plan for private repos). The guard job checks that the pusher's username
  matches the branch name and auto-reverts + flags anything else. This
  works on any plan, public or private repo. It's not instantaneous —
  there's a brief window where an unauthorized commit exists remotely
  before the revert runs — but for a classroom competition (not an
  adversarial security setting) this is normally more than sufficient.
- If you'd rather not manage any of this yourself, **GitHub Classroom**
  (classroom.github.com) is free and gives each student their own private
  repo automatically — worth a look if this is a recurring event rather
  than a one-off.
- The autograder currently supports Python solutions via pytest. To support
  other languages, swap the "Run grader" step for a per-language test
  command (e.g. compile + run a hidden test binary for C++/Java).
- Add per-challenge dependencies to the "Install grading dependencies" step
  in `autograde.yml` (e.g. `pip install numpy` if a challenge needs it).
- All students need at least **write** access as collaborators on the repo
  in order to push at all — add them via repo Settings → Collaborators, or
  `gh api --method PUT /repos/<owner>/<repo>/collaborators/<username> -f permission=push`.
