# Server Deployment Guide (Ubuntu 24.10)

Use this guide **on the droplet** (67.205.163.48) to run the Telegram bot in a Docker container with *set-and-forget* `docker compose`.

---

## 0. Prerequisites Checklist

* Docker Engine **and** the Compose plugin are installed.  Verify:
  ```bash
  docker --version
  docker compose version
  ```
  If either command is missing, install via:
  ```bash
  sudo apt update
  sudo apt install -y docker.io docker-compose-plugin
  sudo systemctl enable --now docker
  ```
* Outbound HTTPS access (for Telegram & Google Gemini APIs).
* SSH access with a user that can run `sudo`.

---

## 1. Clone the repository & checkout the feature branch

```bash
cd ~
# (choose any directory you like)

git clone -b enhanced-pipeline https://github.com/StewartalsopIII/transcribe_telegram.git
cd transcribe_telegram
```

---

## 2. Create the `.env` file with your secrets

```bash
nano .env
```
Paste **exactly**:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
GOOGLE_API_KEY=your_gemini_api_key_here
```
Save (Ctrl-O → Enter) and exit (Ctrl-X).

**Security tip:** The `.env` file is already in `.gitignore`, so it won’t be committed.

---

## 3. Build (or pull) the container image

### Option A – Build locally (no registry needed)
```bash
docker compose build   # reads the Dockerfile
```

### Option B – Pull a pre-built image (skip build)
Change `image:` in `docker-compose.yml` to your registry tag, then:
```bash
docker compose pull
```

---

## 4. Start the bot (detached)

```bash
docker compose up -d
```
Docker will:
* create a container named `transcribe_telegram-bot-1` (or similar)
* apply `restart: unless-stopped` → auto-start on boot and auto-restart on crash.

---

## 5. Verify it’s running

```bash
docker compose ps

docker compose logs -f   # Ctrl-C to stop tailing
```
You should see log lines like “Application started” and incoming updates.

---

## 6. Routine operations

| Action | Command |
|--------|---------|
| View logs | `docker compose logs -f` |
| Stop the bot | `docker compose down` |
| Update code & rebuild | `git pull` → `docker compose build --no-cache` → `docker compose up -d` |
| Update registry image | `docker compose pull` → `docker compose up -d` |

---

## 7. System updates (optional)

Periodically:
```bash
sudo apt update && sudo apt upgrade -y
```
Reboot if prompted; Docker’s restart policy will bring the bot back automatically.

---

## Done!

Your Telegram bot now runs continuously in a self-healing container.  No web server exposed, no extra ports, just outbound HTTPS traffic. 