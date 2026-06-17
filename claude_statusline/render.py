"""Pure presentation helpers — no I/O, no color, easy to unit-test."""
from datetime import datetime, timezone

from .config import BAR_WIDTH, FILLED, EMPTY


def bar(pct, width=BAR_WIDTH):
    """Render a monochrome progress bar for a 0-100 percentage."""
    pct = max(0.0, min(100.0, pct))
    filled = int(round(pct / 100 * width))
    return FILLED * filled + EMPTY * (width - filled)


def short(n):
    """Human-readable token count: 1234 -> '1K', 1000000 -> '1M'."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1000:
        return f"{n / 1000:.0f}K"
    return str(n)


def clock(dt):
    """Local wall-clock time, compact: 16:07 -> '4:07p', 09:30 -> '9:30a'."""
    local = dt.astimezone()
    return local.strftime("%I:%M%p").lower().lstrip("0")[:-1]


def reset_in(iso):
    """Compact 'resets in' hint from an ISO timestamp, e.g. '3h' or '2d'."""
    if not iso:
        return ""
    try:
        when = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        secs = (when - datetime.now(timezone.utc)).total_seconds()
        if secs <= 0:
            return "now"
        if secs < 3600:
            return f"{int(secs // 60)}m"
        if secs < 86400:
            return f"{int(secs // 3600)}h"
        return f"{int(secs // 86400)}d"
    except Exception:
        return ""
