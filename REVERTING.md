# Reverting a Problematic Deployment

This guide explains how to quickly roll back **only** the most recent change if it misbehaves in production.

---

## 1. Identify the last good commit

```bash
# On the server
cd ~/transcribe_telegram

git log --oneline -n 5   # copy the <hash> of the last known-good commit
# At the time of this writing, the commit just *before* the translation/JSON refactor is:
# 32100dd  feat: add AI-generated footer to clarified text
```

## 2. Revert locally (safer) and push

```bash
# On your laptop (recommended)
git revert <bad_commit_hash>
# This opens an editor for a commit message—save & quit.

git push            # sends the revert commit to GitHub
```

## 3. Redeploy on the server

```bash
ssh user@67.205.163.48
cd ~/transcribe_telegram
git pull                      # fetches the revert commit
docker compose build --no-cache
docker compose up -d          # restarts with the previous good code
```

---

### Emergency one-liner (if you can’t revert locally)

```bash
# On the server only—creates a new revert commit and pushes it back
cd ~/transcribe_telegram
git revert <bad_commit_hash> --no-edit

git push

docker compose build --no-cache && docker compose up -d
```

> **Tip:** Avoid `git reset --hard` on the server; it rewrites history and can break collaboration. Always prefer `git revert`, which records an explicit undo commit. 