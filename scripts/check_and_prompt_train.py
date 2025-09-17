#!/usr/bin/env python3
"""
Periodic heavy-training coordinator with user approval.

Runs a lightweight analysis against the server. If heavy training is
recommended, shows a macOS approval dialog before launching the full
coordination cycle (analyze -> train -> deploy).

Writes logs to hybrid_work/periodic_heavy_training.log.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LOG_DIR = REPO_ROOT / "hybrid_work"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "periodic_heavy_training.log"
STATE_FILE = LOG_DIR / "last_prompt.json"


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} | {msg}\n")


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_state(data: dict):
    STATE_FILE.write_text(json.dumps(data, indent=2))


def should_prompt_again(state: dict, min_hours_between_prompts: int = 12) -> bool:
    last = state.get("last_prompt_at")
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last)
        return datetime.now() - last_dt >= timedelta(hours=min_hours_between_prompts)
    except Exception:
        return True


def show_macos_prompt(message: str, timeout_seconds: int = 300) -> bool:
    """Return True if user clicks Run in the dialog. Requires macOS."""
    # Build AppleScript safely without nested f-string braces
    safe_msg = message.replace('"', '\\"')
    script = 'display dialog "{}" with icon caution buttons {"Cancel","Run"} default button "Run" giving up after {}'.format(
        safe_msg, timeout_seconds
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True
        )
        out = (result.stdout or "") + (result.stderr or "")
        # When default button chosen, stdout contains: button returned:Run
        approved = "button returned:Run" in out
        return approved
    except FileNotFoundError:
        # osascript not present (non-macOS). Fail closed without running.
        log("osascript not found; skipping interactive approval")
        return False


def main():
    log("Starting periodic check")

    # Prefer importing coordinator directly to avoid parsing CLI output
    try:
        from enhanced_hybrid_coordinator import HybridCoordinator
    except Exception as e:
        log(f"Failed to import coordinator: {e}")
        sys.exit(1)

    coord = HybridCoordinator()

    # Sync and analyze data from server
    try:
        import asyncio

        analysis = asyncio.run(coord.sync_and_analyze_server_data())
    except Exception as e:
        log(f"Analyze failed: {e}")
        sys.exit(0)

    if not analysis:
        log("No analysis result; skipping")
        sys.exit(0)

    recommended = bool(analysis.get("training_recommended"))
    log(f"Training recommended: {recommended}")

    if not recommended:
        sys.exit(0)

    state = load_state()
    if not should_prompt_again(state):
        log("Skipping prompt (recently prompted)")
        sys.exit(0)

    # Compose prompt message
    msg = (
        "Heavy ML training is recommended based on new server data.\n"
        "This may take 30–60 minutes and will deploy updated models on success.\n\n"
        "Run the training now?"
    )

    approved = show_macos_prompt(msg)
    state.update({"last_prompt_at": datetime.now().isoformat(), "last_prompt_approved": approved})
    save_state(state)

    if not approved:
        log("User declined training")
        sys.exit(0)

    # Run full coordination cycle (analyze -> train -> deploy)
    try:
        import asyncio

        ok = asyncio.run(coord.run_full_coordination_cycle())
        log(f"Full coordination cycle finished: {ok}")
    except Exception as e:
        log(f"Coordination failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
