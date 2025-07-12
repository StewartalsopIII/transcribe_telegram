# Local Setup Guide

This file documents **everything** you do on your *local Mac* to prepare the project for container-based deployment.

---

## Prerequisites

1. **Docker Desktop** (includes Docker Engine & `docker compose`).  
   Download from <https://www.docker.com/products/docker-desktop/> and follow the installer.
2. **Git** ≥ 2.30 (comes with Xcode Command-Line Tools or Homebrew).

---

## 1. Clone the repository & checkout the feature branch

```bash
# If you haven’t cloned it yet
git clone https://github.com/StewartalsopIII/transcribe_telegram.git
cd transcribe_telegram

# Work on (or create) the feature branch
# If it already exists:
git checkout enhanced-pipeline
# …otherwise create it locally:
# git checkout -b enhanced-pipeline
```

---

## 2. Add container-related files (one-time)

You will create **three** new files:

| File | Purpose |
|------|---------|
| `Dockerfile` | Defines the runtime image (Python, FFmpeg, requirements, entry-point). |
| `.dockerignore` | Tells the build context to skip venvs, git metadata, etc. |
| `docker-compose.yml` | Declarative “run spec” for the bot (image, env file, restart policy). |

**👉  We’ll draft these files separately after you approve this guide.**

---

## 3. Stage, commit, and push the changes

```bash
# Stage all newly added files
git add Dockerfile .dockerignore docker-compose.yml

git commit -m "Containerise bot: add Dockerfile, docker-compose, dockerignore"

git push -u origin enhanced-pipeline    # first push sets upstream tracking
```

The branch URL will look like:

```
https://github.com/StewartalsopIII/transcribe_telegram/tree/enhanced-pipeline
```

Share that link with collaborators.

---

## 4. (Optional) Build & run locally for a quick test

```bash
# Build the image (from the current directory)
docker compose build        # or: docker build -t transcribe-telegram .

# Bring up the bot using the compose file (requires a local .env)
docker compose up -d

# Watch logs
docker compose logs -f
```

When you’re happy, commit & push any additional tweaks.

---

## 5. Next step ➜ Server deployment

See `SERVER_DEPLOY.md` for the instructions you will follow on the Ubuntu droplet.  After pushing the branch, SSH into the server and continue there. 