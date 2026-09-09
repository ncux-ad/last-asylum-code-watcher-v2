from watcher.state import State

def test_state(tmp_path):
    p = tmp_path / "state.json"
    s = State(p)
    s.observe("LA26ALLY", "source-a", "https://example.com")
    s.observe("LA26ALLY", "source-b", "https://example.org")
    assert s.data["codes"]["LA26ALLY"]["confidence"] == 0.71
    assert s.data["codes"]["LA26ALLY"]["status"] == "probable"

def test_state_reward_and_expiry_first_guess_wins(tmp_path):
    p = tmp_path / "state.json"
    s = State(p)
    s.observe("LA26ALLY", "source-a", "https://example.com", reward="500 Gold",
              expires_at="2026-09-15", expired=False)
    s.observe("LA26ALLY", "source-b", "https://example.org", reward="1000 Gems",
              expires_at="2026-10-01", expired=False)
    item = s.data["codes"]["LA26ALLY"]
    assert item["reward"] == "500 Gold"
    assert item["expires_at"] == "2026-09-15"

def test_state_backfills_missing_reward(tmp_path):
    p = tmp_path / "state.json"
    s = State(p)
    s.observe("LA26ALLY", "source-a", "https://example.com")
    s.observe("LA26ALLY", "source-b", "https://example.org", reward="500 Gold")
    item = s.data["codes"]["LA26ALLY"]
    assert item["reward"] == "500 Gold"

def test_mark_not_found_removes_code_and_blocklists_it(tmp_path):
    p = tmp_path / "state.json"
    s = State(p)
    s.observe("SAVE60", "gamsgo", "https://example.com")

    s.mark_not_found("SAVE60")

    assert "SAVE60" not in s.data["codes"]
    assert "SAVE60" in s.data["not_found"]

def test_observe_ignores_blocklisted_codes(tmp_path):
    # A source that keeps re-listing a code the game has never heard of
    # can't bring it back onto the dashboard.
    p = tmp_path / "state.json"
    s = State(p)
    s.mark_not_found("SAVE60")

    s.observe("SAVE60", "gamsgo", "https://example.com")

    assert "SAVE60" not in s.data["codes"]

def test_apply_manual_verification_expired_sets_flag(tmp_path):
    p = tmp_path / "state.json"
    s = State(p)
    s.observe("LA26LOVE", "pocketgamer", "https://example.com")

    s.apply_manual_verification("LA26LOVE", "expired", None, "2026-08-29T00:00:00+00:00")

    item = s.data["codes"]["LA26LOVE"]
    assert item["expired"] is True
    assert item["manual_verification"] == {
        "result": "expired",
        "reward": None,
        "verified_at": "2026-08-29T00:00:00+00:00",
    }

def test_state_backfills_missing_top_level_keys(tmp_path):
    # A hand-written or pre-"events" state.json shouldn't crash observe().
    p = tmp_path / "state.json"
    p.write_text('{"codes": {}}', encoding="utf-8")
    s = State(p)

    s.observe("LA26ALLY", "source-a", "https://example.com")

    assert s.data["codes"]["LA26ALLY"]["status"] == "candidate"
    assert len(s.data["events"]) == 1

def test_apply_manual_verification_not_found_delegates_to_mark_not_found(tmp_path):
    p = tmp_path / "state.json"
    s = State(p)
    s.observe("SAVE60", "gamsgo", "https://example.com")

    s.apply_manual_verification("SAVE60", "not_found", None, "2026-08-29T00:00:00+00:00")

    assert "SAVE60" not in s.data["codes"]
    assert "SAVE60" in s.data["not_found"]
