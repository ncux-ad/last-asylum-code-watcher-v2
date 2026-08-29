from pathlib import Path
from datetime import datetime, timezone
import json

def utcnow():
    return datetime.now(timezone.utc).isoformat()

class State:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self.data = {"version": 2, "codes": {}, "events": []}

    def observe(self, code, source, url=None, status="observed"):
        now = utcnow()
        item = self.data["codes"].get(code)

        if item is None:
            item = {
                "code": code,
                "first_seen": now,
                "last_seen": now,
                "sources": {},
                "status": "candidate",
                "confidence": 0.0,
                "notified": False,
            }
            self.data["codes"][code] = item
            self.event("new", code, source)

        item["last_seen"] = now
        item["sources"][source] = {
            "last_seen": now,
            "url": url,
            "status": status,
        }
        self.recalculate(code)

    def recalculate(self, code):
        item = self.data["codes"][code]
        n = len(item["sources"])

        # Independent-source heuristic.
        item["confidence"] = round(min(0.99, 0.35 + 0.18 * n), 2)

        if n >= 3:
            item["status"] = "confirmed"
        elif n >= 2:
            item["status"] = "probable"
        else:
            item["status"] = "candidate"

    def mark_missing(self, source, currently_seen):
        for code, item in self.data["codes"].items():
            source_info = item["sources"].get(source)
            if not source_info:
                continue
            if code not in currently_seen:
                source_info["status"] = "not_seen"

    def event(self, kind, code, source):
        self.data["events"].append({
            "at": utcnow(),
            "kind": kind,
            "code": code,
            "source": source,
        })
        self.data["events"] = self.data["events"][-500:]

    def save(self):
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
