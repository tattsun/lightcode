"""Logging functionality."""

import json
from datetime import datetime
from pathlib import Path


def append_log(log_file: Path, entry: dict) -> None:
    """Append log entry to JSONL file."""
    # Output only required fields in specified order
    # Supports both Completion API and Responses API formats
    field_order = [
        "timestamp",
        # Completion API fields
        "role", "content", "tool_calls", "tool_call_id",
        # Responses API fields
        "output", "response_id",
    ]
    log_entry = {"timestamp": datetime.now().isoformat()}
    for field in field_order[1:]:  # Exclude timestamp
        if field in entry and entry[field] is not None:
            log_entry[field] = entry[field]
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
