#!/usr/bin/env bash
set -euo pipefail

# Automates rename and default-branch update after transfer has been approved.
# Requires: gh auth login with repo admin privileges.

SOURCE_OWNER="${1:-byteworthy}"
SOURCE_REPO="${2:-Hafz-Defend}"
TARGET_OWNER="${3:-ByteWorthyLLC}"
TARGET_REPO="${4:-byteworthy-defend}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required" >&2
  exit 1
fi

echo "Renaming repo to ${TARGET_OWNER}/${TARGET_REPO}"
gh repo rename "$TARGET_REPO" --repo "${TARGET_OWNER}/${SOURCE_REPO}" --yes

echo "Setting default branch to main"
gh repo edit "${TARGET_OWNER}/${TARGET_REPO}" --default-branch main

echo "Fetching repository metadata"
gh repo view "${TARGET_OWNER}/${TARGET_REPO}" --json name,owner,url,defaultBranchRef

echo "NOTE: repository transfer from ${SOURCE_OWNER}/${SOURCE_REPO} to ${TARGET_OWNER}/${SOURCE_REPO} must be done in GitHub UI by an admin."
