#!/bin/bash
# Push updated tracked files to GitHub

cd "$(dirname "$0")/.."

git add -u

if git diff --staged --quiet; then
  echo "無變更，略過"
  exit 0
fi

git commit -m "Update data $(date '+%Y-%m-%d %H:%M')"
git pull --rebase origin master
git push

gh workflow run fetch.yml
echo "✅ 已觸發 GitHub Action: Fetch RSS Feeds"
