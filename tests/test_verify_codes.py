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
