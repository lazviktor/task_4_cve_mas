#!/usr/bin/env bash
GITHUB_USER="lazviktor"
REPO_NAME="task_4_cve_mas"
BRANCH="main"

git init
git add .
git commit -m "Task 4 — MAS + GigaChat LLM"
git branch -M $BRANCH
git remote add origin https://github.com/$GITHUB_USER/$REPO_NAME.git
git push -u origin $BRANCH
