"""Configuration and constants.

Everything tunable lives here. Behaviour can be overridden with environment
variables so the package itself stays free of magic numbers at the call sites.
"""
import os

# --- API endpoints (Claude Code's own; read-only, called with your OAuth token) ---
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
MODELS_URL = "https://api.anthropic.com/v1/models/"

# --- on-disk caches (so the network is hit rarely, not on every render) ---
TMP = os.environ.get("TMPDIR", "/tmp")
USAGE_CACHE = os.path.join(TMP, "claude-statusline-usage.json")
WINDOW_CACHE = os.path.join(TMP, "claude-statusline-window.json")
USAGE_TTL = 60          # seconds: how long to reuse a fetched /usage response
WINDOW_TTL = 86400      # seconds: how long to reuse a model's context window

# --- appearance (monochrome; block glyphs + bold/dim text weight, no color) ---
FILLED, EMPTY = "█", "░"   # █ ░
SEPARATOR = "  │  "             # ' │ '
BAR_WIDTH = int(os.environ.get("CLAUDE_STATUSLINE_WIDTH", "10"))

# Monochrome styling. Bar names are bold; the bars, percents and counts render
# bright (default foreground); only the reset-time hints are a light grayscale
# tone so they recede. Grayscale only — no hue. Set CLAUDE_STATUSLINE_PLAIN to
# disable all styling. CLAUDE_STATUSLINE_DARK sets the hint grayscale level
# (xterm-256 ramp: 232=near-black .. 255=near-white; default 238 — faint, so the
# hints recede on a dark background. Raise it toward 255 for a paler/whiter hint).
_STYLE = "CLAUDE_STATUSLINE_PLAIN" not in os.environ
_GRAY = os.environ.get("CLAUDE_STATUSLINE_DARK", "238")
BOLD = "\033[1m" if _STYLE else ""
LIGHT = f"\033[38;5;{_GRAY}m" if _STYLE else ""
RESET = "\033[0m" if _STYLE else ""

# --- segments ---
# Show the prompt-cache expiry segment ('cache 5:15p' / 'cache COLD').
SHOW_CACHE = "CLAUDE_STATUSLINE_NO_CACHE" not in os.environ

# --- context window ---
FALLBACK_WINDOW = 200000             # used only if the model lookup fails
_forced = os.environ.get("CLAUDE_CONTEXT_LIMIT")
# Force a fixed window (tokens) and skip the per-model API lookup entirely.
FORCED_WINDOW = int(_forced) if _forced and _forced.isdigit() else None
