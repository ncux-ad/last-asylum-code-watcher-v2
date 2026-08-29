import json
import sys
from pathlib import Path

import tools.verify_codes as verify_codes


def _chdir_with_state(tmp_path, monkeypatch, state):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "state.json").write_text(json.dumps(state), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(verify_codes, "STATE_PATH", Path("data/state.json"))
    monkeypatch.setattr(verify_codes, "VERIFICATIONS_PATH", Path("data/manual_verifications.json"))


def test_load_candidates_skips_expired_status_and_already_verified(tmp_path, monkeypatch):
    state = {
        "codes": {
            "LA26ALLY": {"status": "confirmed"},
            "LA26FOOL": {"status": "probable"},
            "LAW10A7C": {"status": "candidate"},
            "STALE1": {"status": "not_seen"},
        }
    }
    _chdir_with_state(tmp_path, monkeypatch, state)
    verify_codes.save_verification("LA26FOOL", "invalid", None)

    codes = verify_codes.load_candidates()

    assert codes == ["LA26ALLY", "LAW10A7C"]


def test_save_verification_roundtrip(tmp_path, monkeypatch):
    _chdir_with_state(tmp_path, monkeypatch, {"codes": {}})

    verify_codes.save_verification("LA26ALLY", "ok", "500 Gold")
    data = verify_codes.load_verifications()

    assert data["LA26ALLY"]["result"] == "ok"
    assert data["LA26ALLY"]["reward"] == "500 Gold"
    assert "verified_at" in data["LA26ALLY"]


def test_prompt_result_rejects_unknown_then_accepts(capsys):
    answers = iter(["bogus", "ok", "500 Gold"])
    result, reward = verify_codes.prompt_result("LA26ALLY", input_fn=lambda _: next(answers))

    assert result == "ok"
    assert reward == "500 Gold"
    assert "Не понял" in capsys.readouterr().out


def test_prompt_result_skip_has_no_reward():
    answers = iter(["skip"])
    result, reward = verify_codes.prompt_result("LA26ALLY", input_fn=lambda _: next(answers))

    assert result == "skip"
    assert reward is None


def test_apply_to_public_state_ok_overwrites_reward(tmp_path, monkeypatch):
    state = {"codes": {"LA26ALLY": {"code": "LA26ALLY", "reward": "guessed reward", "expired": None}}}
    _chdir_with_state(tmp_path, monkeypatch, state)

    verify_codes.apply_to_public_state("LA26ALLY", "ok", "100 Diamonds, confirmed", verified_at="2026-08-29T18:00:00+00:00")

    item = json.loads((tmp_path / "data" / "state.json").read_text())["codes"]["LA26ALLY"]
    assert item["manual_verification"] == {
        "result": "ok",
        "reward": "100 Diamonds, confirmed",
        "verified_at": "2026-08-29T18:00:00+00:00",
    }
    # A real redeem confirmation beats the page-text heuristic guess.
    assert item["reward"] == "100 Diamonds, confirmed"


def test_apply_to_public_state_expired_sets_expired_flag(tmp_path, monkeypatch):
    state = {"codes": {"LA26LOVE": {"code": "LA26LOVE", "reward": None, "expired": None}}}
    _chdir_with_state(tmp_path, monkeypatch, state)

    verify_codes.apply_to_public_state("LA26LOVE", "expired", None)

    item = json.loads((tmp_path / "data" / "state.json").read_text())["codes"]["LA26LOVE"]
    assert item["manual_verification"]["result"] == "expired"
    assert item["expired"] is True


def test_apply_to_public_state_invalid_does_not_touch_reward_or_expired(tmp_path, monkeypatch):
    state = {"codes": {"LAW10A7C": {"code": "LAW10A7C", "reward": None, "expired": None}}}
    _chdir_with_state(tmp_path, monkeypatch, state)

    verify_codes.apply_to_public_state("LAW10A7C", "invalid", None)

    item = json.loads((tmp_path / "data" / "state.json").read_text())["codes"]["LAW10A7C"]
    assert item["manual_verification"]["result"] == "invalid"
    assert item["reward"] is None
    assert item["expired"] is None


def test_apply_to_public_state_unknown_code_is_a_noop(tmp_path, monkeypatch):
    state = {"codes": {}}
    _chdir_with_state(tmp_path, monkeypatch, state)

    verify_codes.apply_to_public_state("GHOSTCODE1", "ok", "500 Gold")

    assert json.loads((tmp_path / "data" / "state.json").read_text())["codes"] == {}
