from watcher.state import State

def test_state(tmp_path):
    p = tmp_path / "state.json"
    s = State(p)
    s.observe("LA26ALLY", "source-a", "https://example.com")
    s.observe("LA26ALLY", "source-b", "https://example.org")
    assert s.data["codes"]["LA26ALLY"]["confidence"] == 0.71
    assert s.data["codes"]["LA26ALLY"]["status"] == "probable"
