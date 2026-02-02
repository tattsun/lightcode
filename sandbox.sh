#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOGS_DIR="${SCRIPT_DIR}/logs"
LOG_FILE="session_$(date +%Y%m%d_%H%M%S).jsonl"

if [ -z "$1" ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

SANDBOX_DIR="$(cd "$1" && pwd)"

mkdir -p "$LOGS_DIR"

docker run -it --rm \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    -e TAVILY_API_KEY="$TAVILY_API_KEY" \
    -v "$SANDBOX_DIR":/sandbox \
    -v "$LOGS_DIR":/logs \
    -w /sandbox \
    lightcode --no-permissions --web-search --log-file "/logs/$LOG_FILE"
