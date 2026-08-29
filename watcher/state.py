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
        self.data.setdefault("not_found", [])

    def observe(self, code, source, url=None, status="observed", reward=None, expires_at=None, expired=None):
        if code in self.data["not_found"]:
            # A human confirmed the game has never heard of this code
            # (as opposed to expired/invalid, which mean it existed).
            # Aggregator sites keep re-listing it regardless, so every
            # source's observe() call for it is ignored here for good.
            return

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
                "reward": None,
                "expires_at": None,
                "expired": None,
            }
            self.data["codes"][code] = item
            self.event("new", code, source)

        item["last_seen"] = now
        item["sources"][source] = {
            "last_seen": now,
            "url": url,
            "status": status,
        }
        # First useful guess wins; we don't try to arbitrate between
        # sources that disagree on reward/expiry text.
        if reward and not item.get("reward"):
            item["reward"] = reward
        if expires_at and not item.get("expires_at"):
            item["expires_at"] = expires_at
            item["expired"] = expired
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

    def mark_not_found(self, code):
        self.data["codes"].pop(code, None)
        if code not in self.data["not_found"]:
            self.data["not_found"].append(code)
            self.data["not_found"].sort()

    def apply_manual_verification(self, code, result, reward, verified_at):
        """Merge an operator-run redemption check (tools/verify_codes.py)
        into the public record. "not_found" purges the code and
        blocklists it in observe() so aggregator sites can't resurrect
        it; every other result only annotates the existing entry."""
        if result == "not_found":
            self.mark_not_found(code)
            return

        item = self.data["codes"].get(code)
        if item is None:
            return

        item["manual_verification"] = {"result": result, "reward": reward, "verified_at": verified_at}
        if result == "ok" and reward:
            item["reward"] = reward
        if result == "expired":
            item["expired"] = True

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
