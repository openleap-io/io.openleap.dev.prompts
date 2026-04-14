#!/usr/bin/env python3
"""
Crawler service — runs crawl-implementation-status.py on a cron schedule.

REST endpoints:
  GET  /schedule        — current cron expression + next run time
  PUT  /schedule        — set cron expression {"cron": "0 6 * * *"}
  POST /run             — trigger immediate crawl
  GET  /status          — last run result
  GET  /health          — liveness check

Env vars:
  GITHUB_TOKEN          — required, GitHub API token
  GIT_REMOTE_URL        — spec repo clone URL (default: https://github.com/openleap-io/io.openleap.spec.git)
  GIT_USER_NAME         — git commit author name (default: crawl-bot)
  GIT_USER_EMAIL        — git commit author email (default: crawl-bot@openleap.io)
  DEFAULT_CRON          — initial cron schedule (default: 0 6 * * *  = daily 6 AM UTC)
  REPO_DIR              — where to clone/keep the spec repo (default: /data/spec-repo)
  PORT                  — server port (default: 8080)
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, jsonify, request

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GIT_REMOTE_URL = os.environ.get(
    "GIT_REMOTE_URL", "https://github.com/openleap-io/io.openleap.spec.git"
)
GIT_USER_NAME = os.environ.get("GIT_USER_NAME", "crawl-bot")
GIT_USER_EMAIL = os.environ.get("GIT_USER_EMAIL", "crawl-bot@openleap.io")
DEFAULT_CRON = os.environ.get("DEFAULT_CRON", "*/5 * * * *")
REPO_DIR = Path(os.environ.get("REPO_DIR", "/data/spec-repo"))
PORT = int(os.environ.get("PORT", "8080"))
CRAWL_SCRIPT = "scripts/crawl-implementation-status.py"

JOB_ID = "crawl-job"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("crawler")

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
app = Flask(__name__)
scheduler = BackgroundScheduler(timezone="UTC")
run_lock = threading.Lock()

last_run: dict = {
    "status": "never",
    "started_at": None,
    "finished_at": None,
    "summary": None,
    "error": None,
}
current_cron: str = DEFAULT_CRON


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------
def git(*args: str, cwd: Path | None = None) -> str:
    """Run a git command and return stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd or REPO_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def ensure_repo() -> None:
    """Clone or pull the spec repo."""
    # Inject token into remote URL for auth
    auth_url = GIT_REMOTE_URL.replace(
        "https://", f"https://x-access-token:{GITHUB_TOKEN}@"
    )

    if not (REPO_DIR / ".git").exists():
        log.info("Cloning spec repo to %s", REPO_DIR)
        REPO_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", auth_url, str(REPO_DIR)],
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
    else:
        # Ensure remote URL is up to date (token may change)
        git("remote", "set-url", "origin", auth_url)

    git("config", "user.name", GIT_USER_NAME)
    git("config", "user.email", GIT_USER_EMAIL)


def pull() -> None:
    """Pull latest from origin/main."""
    log.info("Pulling latest...")
    git("fetch", "origin")
    git("reset", "--hard", "origin/main")


def commit_and_push() -> bool:
    """Commit and push if there are changes. Returns True if pushed."""
    status = git("status", "--porcelain")
    if not status:
        log.info("No changes to commit")
        return False

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    git("add", "landscape/implementation-status.json")
    git("commit", "-m", f"crawl: update implementation-status.json ({today})")
    log.info("Pushing to origin/main...")
    git("push", "origin", "main")
    return True


# ---------------------------------------------------------------------------
# Crawl runner
# ---------------------------------------------------------------------------
def run_crawl() -> dict:
    """Execute the crawl: pull → run script → commit & push."""
    if not run_lock.acquire(blocking=False):
        return {"status": "skipped", "reason": "already running"}

    last_run["status"] = "running"
    last_run["started_at"] = datetime.now(timezone.utc).isoformat()
    last_run["error"] = None
    last_run["summary"] = None

    try:
        ensure_repo()
        pull()

        log.info("Running crawl script...")
        result = subprocess.run(
            ["python3", CRAWL_SCRIPT],
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            timeout=600,
            env={**os.environ, "GITHUB_TOKEN": GITHUB_TOKEN},
        )

        if result.returncode != 0:
            raise RuntimeError(f"Crawl script failed:\n{result.stderr}")

        # Extract summary from output (everything after "## Implementation Status Summary")
        output = result.stdout
        summary_start = output.find("## Implementation Status Summary")
        summary = output[summary_start:] if summary_start >= 0 else output[-2000:]

        pushed = commit_and_push()

        last_run["status"] = "success"
        last_run["summary"] = summary
        last_run["finished_at"] = datetime.now(timezone.utc).isoformat()

        log.info("Crawl complete. Pushed: %s", pushed)
        return {"status": "success", "pushed": pushed, "summary": summary}

    except Exception as e:
        log.exception("Crawl failed")
        last_run["status"] = "error"
        last_run["error"] = str(e)
        last_run["finished_at"] = datetime.now(timezone.utc).isoformat()
        return {"status": "error", "error": str(e)}

    finally:
        run_lock.release()


# ---------------------------------------------------------------------------
# Cron helpers
# ---------------------------------------------------------------------------
def parse_cron(expr: str) -> CronTrigger:
    """Parse a 5-field cron expression into an APScheduler trigger."""
    parts = expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Expected 5-field cron expression, got: {expr}")
    minute, hour, day, month, dow = parts
    return CronTrigger(
        minute=minute, hour=hour, day=day, month=month, day_of_week=dow
    )


def set_schedule(cron_expr: str) -> None:
    """Set or update the crawl schedule."""
    global current_cron
    trigger = parse_cron(cron_expr)
    if scheduler.get_job(JOB_ID):
        scheduler.reschedule_job(JOB_ID, trigger=trigger)
    else:
        scheduler.add_job(run_crawl, trigger=trigger, id=JOB_ID, name="crawl")
    current_cron = cron_expr
    log.info("Schedule set to: %s", cron_expr)


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/schedule", methods=["GET"])
def get_schedule():
    job = scheduler.get_job(JOB_ID)
    next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
    return jsonify({"cron": current_cron, "next_run": next_run})


@app.route("/schedule", methods=["PUT"])
def update_schedule():
    data = request.get_json(silent=True) or {}
    cron_expr = data.get("cron")

    if not cron_expr:
        return jsonify({"error": "Missing 'cron' field"}), 400

    try:
        set_schedule(cron_expr)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    job = scheduler.get_job(JOB_ID)
    next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
    return jsonify({"cron": cron_expr, "next_run": next_run})


@app.route("/run", methods=["POST"])
def trigger_run():
    thread = threading.Thread(target=run_crawl, daemon=True)
    thread.start()
    return jsonify({"status": "started"}), 202


@app.route("/status", methods=["GET"])
def get_status():
    return jsonify(last_run)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
def main() -> None:
    if not GITHUB_TOKEN:
        log.error("GITHUB_TOKEN is required")
        raise SystemExit(1)

    scheduler.start()
    set_schedule(DEFAULT_CRON)

    log.info("Crawler service starting on port %d", PORT)
    log.info("Default schedule: %s", DEFAULT_CRON)

    app.run(host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
