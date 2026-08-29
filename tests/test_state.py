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
