"""Countdown to prompt-cache expiry.

Anthropic's prompt cache is a sliding window — refreshed on every cache hit — so
'time left' is measured from the most recent assistant turn's timestamp, not from
file mtime or the last user message. The TTL (1 hour vs 5 minutes) is detected from
that turn's `usage.cache_creation` buckets, falling back to the last turn that
actually created cache, then to the 1-hour default Claude Code uses.
"""
import json
import os
from datetime import datetime, timedelta

TTL_1H = 3600
TTL_5M = 300


def _ttl_from_buckets(cache_creation):
    if not cache_creation:
        return None
    if cache_creation.get("ephemeral_1h_input_tokens", 0) > 0:
        return TTL_1H
    if cache_creation.get("ephemeral_5m_input_tokens", 0) > 0:
        return TTL_5M
    return None


def cache_expiry(transcript_path):
    """Wall-clock time the prompt cache goes cold, as a timezone-aware datetime.

    Returns None if it can't be determined (no transcript / no assistant turn yet).
    An absolute time stays correct between status-line refreshes, so the segment
    doesn't need Claude Code to re-run the script on a timer.
    """
    if not transcript_path or not os.path.exists(transcript_path):
        return None
    timestamp = None
    ttl = None        # TTL of the most recent assistant turn (may be unknown)
    last_known_ttl = None  # most recent turn that actually created cache
    try:
        with open(transcript_path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if entry.get("isSidechain") or entry.get("type") != "assistant":
                    continue
                usage = (entry.get("message") or {}).get("usage")
                if not usage:
                    continue
                detected = _ttl_from_buckets(usage.get("cache_creation"))
                if detected:
                    last_known_ttl = detected
                if entry.get("timestamp"):
                    timestamp, ttl = entry["timestamp"], detected
    except Exception:
        return None
    if not timestamp:
        return None
    ttl = ttl or last_known_ttl or TTL_1H
    try:
        anchor = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except Exception:
        return None
    return anchor + timedelta(seconds=ttl)
