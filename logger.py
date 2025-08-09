import json
from datetime import datetime, timezone
from pathlib import Path
LOG_PATH = Path('/tmp/privacy_firewall_logs.jsonl')

def log_request(data):
    record = {
        "ts": datetime.now(datetime.timezone.utc).isoformat() + "Z",
        "data": data
    }
    with LOG_PATH.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def audit_log(event_type, original, redacted, detected, metadata=None):
    metadata = metadata or {}
    record = {
        "ts": datetime.now(datetime.timezone.utc).isoformat() + "Z",
        "event": event_type,
        "original": original,
        "redacted": redacted,
        "detected": detected,
        "metadata": metadata
    }
    with LOG_PATH.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
