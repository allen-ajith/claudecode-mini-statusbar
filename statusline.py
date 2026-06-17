#!/usr/bin/env python3
"""Zero-install entry point for the Claude Code status line.

Point Claude Code's statusLine command straight at this file — no pip install
needed:

    "statusLine": {
      "type": "command",
      "command": "python3 /path/to/claudecode-mini-statusbar/statusline.py"
    }
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claude_statusline.statusline import main  # noqa: E402

if __name__ == "__main__":
    main()
