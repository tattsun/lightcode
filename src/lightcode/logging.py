"""ログ機能"""

import json
from datetime import datetime
from pathlib import Path


def append_log(log_file: Path, entry: dict) -> None:
    """ログエントリをJSONLファイルに追記"""
    # 必要なフィールドだけを指定順序で出力
    field_order = ["timestamp", "role", "content", "tool_calls", "tool_call_id"]
    log_entry = {"timestamp": datetime.now().isoformat()}
    for field in field_order[1:]:  # timestamp以外
        if field in entry and entry[field] is not None:
            log_entry[field] = entry[field]
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
