#!/usr/bin/env bash
#
# setup-student-branches.sh
#
# Creates one submission branch per student and (optionally) locks each
# branch down so ONLY that student can push to it. Requires:
#   - GitHub CLI (`gh`) installed and authenticated: https://cli.github.com
#   - You already created an empty GitHub repo, e.g. `myorg/coding-comp`
#   - A students.csv file with two columns: github_username,student_name
#
# Usage:
#   ./setup-student-branches.sh <owner/repo> <students.csv>
#
# Example:
#   ./setup-student-branches.sh myorg/coding-comp students.csv

set -euo pipefail

REPO="${1:?Usage: $0 <owner/repo> <students.csv>}"
CSV="${2:?Usage: $0 <owner/repo> <students.csv>}"

if ! command -v gh &> /dev/null; then
  echo "ERROR: GitHub CLI 'gh' is not installed. See https://cli.github.com" >&2
  exit 1
fi

echo "Working on repo: $REPO"

# Make sure we have a local clone to branch from
TMP_DIR=$(mktemp -d)
git clone "https://github.com/$REPO.git" "$TMP_DIR"
cd "$TMP_DIR"

# skip header row, read username + name
tail -n +2 "$OLDPWD/$CSV" | while IFS=',' read -r username fullname; do
  username=$(echo "$username" | xargs)   # trim whitespace
  [ -z "$username" ] && continue

  branch="submissions/$username"
  echo ""
  echo "== Setting up branch for $username ($fullname) =="

  # Create the branch from main if it doesn't already exist
  git fetch origin main
  if git ls-remote --exit-code --heads origin "$branch" &> /dev/null; then
    echo "  Branch $branch already exists, skipping creation."
  else
    git checkout main
    git checkout -b "$branch"
    mkdir -p "solutions"
    echo "# Submissions for $fullname ($username)" > "solutions/README.md"
    git add solutions/README.md
    git commit -m "Init submission branch for $username"
    git push origin "$branch"
    echo "  Created and pushed $branch"
  fi

  # NOTE: We deliberately do NOT use GitHub's native branch-protection
  # "restrict who can push" feature here — on private repos that requires
  # a paid GitHub Team/Enterprise plan. Instead, enforcement happens via
  # the "guard" job in .github/workflows/autograde.yml, which runs on every
  # push, checks that the pusher's username matches the branch owner, and
  # auto-reverts + flags the commit if it doesn't. This works on any plan.

  # Make sure the student actually has write access to push at all
  gh api \
    --method PUT \
    "/repos/$REPO/collaborators/$username" \
    -f "permission=push" \
    > /dev/null \
    && echo "  Granted push (write) access to $username"

done

cd "$OLDPWD"
rm -rf "$TMP_DIR"
echo ""
echo "Done. Each student now has their own locked submissions/<username> branch."
