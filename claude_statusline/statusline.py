"""Assemble and print the status line.

Each segment is a (label, body) pair; styling — bold label, dimmed body — is
applied in one place (`format_segment`). `build_statusline` is pure (payload in,
string out) so it's easy to test; `main` is the thin I/O wrapper Claude Code calls.
"""
import json
import sys
from datetime import datetime, timezone

from .api import context_window, fetch_usage
from .cache import cache_expiry
from .config import BOLD, LIGHT, RESET, SEPARATOR, SHOW_CACHE
from .context import context_tokens
from .render import bar, clock, reset_in, short

# (label, key in the /usage response)
USAGE_LIMITS = (("5h", "five_hour"), ("wk", "seven_day"))


def context_segment(payload):
    """Return the ('ctx', body) segment."""
    tokens = context_tokens(payload.get("transcript_path"))
    if tokens is None:
        return ("ctx", f"{bar(0)}  —")
    window = context_window((payload.get("model") or {}).get("id"))
    pct = tokens / window * 100
    return ("ctx", f"{bar(pct)} {pct:.0f}% {short(tokens)}/{short(window)}")


def usage_segments(usage):
    """Return [('5h', body), ('wk', body)] for whichever limits are reported."""
    segments = []
    for label, key in USAGE_LIMITS:
        block = (usage or {}).get(key) or {}
        pct = block.get("utilization")
        if pct is None:
            continue
        hint = reset_in(block.get("resets_at"))
        tail = f" {LIGHT}({hint}){RESET}" if hint else ""
        segments.append((label, f"{bar(pct)} {pct:.0f}%{tail}"))
    return segments


def cache_segment(payload):
    """('cache', body) where body is the prompt-cache expiry wall-clock time.

    Absolute time so it stays accurate without Claude Code re-running the script.
    """
    expiry = cache_expiry(payload.get("transcript_path"))
    if expiry is None:
        return None
    if expiry <= datetime.now(timezone.utc):
        return ("cache", "COLD")
    return ("cache", clock(expiry))


def format_segment(label, body):
    """Bold name; body stays bright. (Hints inside the body are pre-styled light.)"""
    return f"{BOLD}{label}{RESET} {body}"


def build_statusline(payload):
    """Return the full status-line string for a Claude Code status payload."""
    segments = [context_segment(payload)]
    segments += usage_segments(fetch_usage()) or [("usage", "—")]
    if SHOW_CACHE:
        cache = cache_segment(payload)
        if cache:
            segments.append(cache)
    return SEPARATOR.join(format_segment(label, body) for label, body in segments)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    print(build_statusline(payload))


if __name__ == "__main__":
    main()
