#!/bin/bash
# Gravitron 3.0 Harness Bootstrap
# Location: ~/.gravitron/core/bin/bootstrap.sh

export GRAVITRON_ROOT="$HOME/.gravitron"
export GRAVITRON_CORE="$GRAVITRON_ROOT/core"
export GRAVITRON_USR="$GRAVITRON_ROOT/usr"

# Tools always on PATH (The Master Router)
export PATH="$GRAVITRON_CORE/bin:$PATH"

# Defaults
export GRAVITRON_STATE="${GRAVITRON_STATE:-$HOME/.gemini/antigravity}"
export ANTIGRAVITY_HOME="$GRAVITRON_STATE"

# Welcome message (Interactive only)
if [[ $- == *i* ]]; then
    echo "[Gravitron 3.0] Unified Harness Active"
    echo "Usage: gravitron <command>"
fi
