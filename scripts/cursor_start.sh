#!/bin/bash
# Start Cursor with optimized environment
export SHELL_SESSION_TIMEOUT=10
export DIRENV_WARN_TIMEOUT=5s
cd "$(dirname "$0")"
/Applications/Cursor.app/Contents/MacOS/Cursor . &
