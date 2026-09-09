from watcher.add_code import add_code
from watcher.state import State


def test_add_code_creates_unknown_code_and_marks_it_ok(tmp_path):
    s = State(tmp_path / "state.json")

    add_code(s, "LA30W7F2M", "ok", "200 алмазов", verified_at="2026-09-09T00:00:00+00:00")

    item = s.data["codes"]["LA30W7F2M"]
    assert item["status"] == "confirmed"
    assert item["reward"] == "200 алмазов"
    assert item["manual_verification"] == {
        "result": "ok",
        "reward": "200 алмазов",
        "verified_at": "2026-09-09T00:00:00+00:00",
    }
    assert item["sources"]["manual"]["status"] == "reported"


def test_add_code_defaults_source_but_accepts_override(tmp_path):
    s = State(tmp_path / "state.json")

    add_code(s, "LA30W7F2M", "ok", "200 алмазов", source="telegram-manual",
              verified_at="2026-09-09T00:00:00+00:00")

    assert set(s.data["codes"]["LA30W7F2M"]["sources"]) == {"telegram-manual"}


def test_add_code_reuses_existing_scraped_candidate(tmp_path):
    # Mirrors the LA30W7F2M case: the scraper already picked the code up
    # as an unverified candidate before the operator checked it in-game.
    s = State(tmp_path / "state.json")
    s.observe("LA30W7F2M", "lastasylumplague", "https://example.com")

    add_code(s, "LA30W7F2M", "ok", "200 алмазов", verified_at="2026-09-09T00:00:00+00:00")

    item = s.data["codes"]["LA30W7F2M"]
    assert set(item["sources"]) == {"lastasylumplague"}  # not duplicated with "manual"
    assert item["manual_verification"]["result"] == "ok"


def test_add_code_not_found_blocklists_without_creating_it(tmp_path):
    s = State(tmp_path / "state.json")

    add_code(s, "GHOSTCODE1", "not_found", verified_at="2026-09-09T00:00:00+00:00")

    assert "GHOSTCODE1" not in s.data["codes"]
    assert "GHOSTCODE1" in s.data["not_found"]


def test_add_code_expired_sets_flag_without_reward(tmp_path):
    s = State(tmp_path / "state.json")

    add_code(s, "LA26LOVE", "expired", verified_at="2026-09-09T00:00:00+00:00")

    item = s.data["codes"]["LA26LOVE"]
    assert item["expired"] is True
    assert item["reward"] is None
