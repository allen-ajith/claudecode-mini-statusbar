"""Authenticated, cached access to Claude's usage and model-info endpoints.

The OAuth access token is read live from the credential store Claude Code already
manages, so this never stores or transmits a secret of its own. Both endpoints are
read-only GETs to api.anthropic.com, and every response is cached on disk.
"""
import json
import os
import subprocess
import time
import urllib.request

from .config import (
    USAGE_URL, MODELS_URL, USAGE_CACHE, WINDOW_CACHE,
    USAGE_TTL, WINDOW_TTL, FALLBACK_WINDOW, FORCED_WINDOW,
)

KEYCHAIN_SERVICE = "Claude Code-credentials"
CREDENTIALS_FILE = os.path.expanduser("~/.claude/.credentials.json")


def get_token():
    """Return Claude Code's current OAuth access token, or None.

    Tries the macOS keychain first, then the credentials file used on other
    platforms / setups.
    """
    try:
        raw = subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        if raw:
            return json.loads(raw)["claudeAiOauth"]["accessToken"]
    except Exception:
        pass
    try:
        with open(CREDENTIALS_FILE) as f:
            return json.load(f)["claudeAiOauth"]["accessToken"]
    except Exception:
        return None


def _read(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _write(path, data):
    try:
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except Exception:
        pass


def _api_get(url, token):
    request = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
        "anthropic-version": "2023-06-01",
        "User-Agent": "claudecode-mini-statusbar",
    })
    with urllib.request.urlopen(request, timeout=4) as resp:
        return json.loads(resp.read().decode())


def fetch_usage():
    """Subscription usage JSON (five_hour / seven_day utilization), cached.

    Falls back to the last cached copy on any error so the bars never blank out.
    """
    cached = _read(USAGE_CACHE)
    if cached is not None and os.path.exists(USAGE_CACHE) \
            and time.time() - os.path.getmtime(USAGE_CACHE) < USAGE_TTL:
        return cached
    token = get_token()
    if not token:
        return cached
    try:
        data = _api_get(USAGE_URL, token)
        _write(USAGE_CACHE, data)
        return data
    except Exception:
        return cached


def context_window(model_id):
    """The model's context window in tokens (max_input_tokens).

    Resolution order: forced override env var, then a per-model cached lookup
    against the Models API, then the last cached value, then a safe fallback.
    This is what makes the bar track 200K vs 1M automatically.
    """
    if FORCED_WINDOW:
        return FORCED_WINDOW
    if not model_id:
        return FALLBACK_WINDOW
    cache = _read(WINDOW_CACHE) or {}
    entry = cache.get(model_id)
    if entry and time.time() - entry.get("ts", 0) < WINDOW_TTL:
        return entry["window"]
    token = get_token()
    if token:
        try:
            data = _api_get(MODELS_URL + model_id, token)
            window = int(data.get("max_input_tokens") or FALLBACK_WINDOW)
            cache[model_id] = {"window": window, "ts": time.time()}
            _write(WINDOW_CACHE, cache)
            return window
        except Exception:
            pass
    return entry["window"] if entry else FALLBACK_WINDOW
