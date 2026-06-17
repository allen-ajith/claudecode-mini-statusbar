"""Compute the current context size from a Claude Code transcript.

The transcript is JSONL; each assistant turn records a `usage` block. The size of
the live context equals the input partition of the most recent main-chain request:
input + cache-read + cache-creation tokens. This matches what `/context` reports.
"""
import json
import os


def context_tokens(transcript_path):
    """Tokens currently in the context window, or None if it can't be determined."""
    if not transcript_path or not os.path.exists(transcript_path):
        return None
    latest = None
    try:
        with open(transcript_path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if entry.get("isSidechain"):          # skip sub-agent turns
                    continue
                usage = (entry.get("message") or {}).get("usage")
                if usage and entry.get("type") == "assistant":
                    latest = usage
    except Exception:
        return None
    if not latest:
        return None
    return (
        latest.get("input_tokens", 0)
        + latest.get("cache_read_input_tokens", 0)
        + latest.get("cache_creation_input_tokens", 0)
    )
