from datetime import date
from watcher.extractor import extract_codes, extract_candidates

def test_extract_codes():
    html = """
    <html><body>
      Active codes: LA26ALLY LA25W8CM
      Not a code: LASTASYLUM
      <script>BADCODE123</script>
    </body></html>
    """
    codes = extract_codes(html)
    assert "LA26ALLY" in codes
    assert "LA25W8CM" in codes
    assert "LASTASYLUM" not in codes
    assert "BADCODE123" not in codes

def test_extract_codes_ignores_plain_words():
    # Long all-letter matches are prose, not codes: real codes mix
    # letters and digits, so a pure-letters candidate must be rejected
    # regardless of length.
    html = """
    <html><body>
      This affiliated construction is a great accordance of content.
      Code: LA26ALLY
    </body></html>
    """
    codes = extract_codes(html)
    assert "AFFILIATED" not in codes
    assert "CONSTRUCTION" not in codes
    assert "ACCORDANCE" not in codes
    assert "CONTENT" not in codes
    assert "LA26ALLY" in codes

def test_extract_codes_ignores_generic_lucky_codes():
    # lota.games recycles generic "lucky number" filler codes across many
    # unrelated games (LOVE666, VIP888, LAPJAP777...) — not game-specific.
    html = """
    <html><body>
      LOVE666 VIP888 LUCK777 LAPJAP777
      Real code: LA26ALLY
    </body></html>
    """
    codes = extract_codes(html)
    assert "LOVE666" not in codes
    assert "VIP888" not in codes
    assert "LUCK777" not in codes
    assert "LAPJAP777" not in codes
    assert "LA26ALLY" in codes

def test_extract_codes_ignores_hex_only_fragments():
    # lota.games embeds game UUIDs in its catalog page; hex-only
    # fragments of those (0-9, A-F) look like codes but aren't.
    html = """
    <html><body>
      B6FCCA4745 D3809EAD49
      Real code: LA26ALLY
    </body></html>
    """
    codes = extract_codes(html)
    assert "B6FCCA4745" not in codes
    assert "D3809EAD49" not in codes
    assert "LA26ALLY" in codes

def test_extract_candidates_reward():
    html = "<html><body><p>LA26ALLY - 500 Gold and 10 Gems</p></body></html>"
    candidates = {c["code"]: c for c in extract_candidates(html)}
    assert candidates["LA26ALLY"]["reward"] == "500 Gold"

def test_extract_candidates_no_reward():
    html = "<html><body><p>Use code LA26ALLY at the settings menu</p></body></html>"
    candidates = {c["code"]: c for c in extract_candidates(html)}
    assert candidates["LA26ALLY"]["reward"] is None

def test_extract_candidates_expiry_with_year():
    html = "<html><body><p>LA26ALLY expires 2026-09-15</p></body></html>"
    candidates = {c["code"]: c for c in extract_candidates(html, today=date(2026, 8, 29))}
    assert candidates["LA26ALLY"]["expires_at"] == "2026-09-15"
    assert candidates["LA26ALLY"]["expired"] is False

def test_extract_candidates_expiry_already_passed():
    html = "<html><body><p>LA26ALLY valid until Aug 1, 2026</p></body></html>"
    candidates = {c["code"]: c for c in extract_candidates(html, today=date(2026, 8, 29))}
    assert candidates["LA26ALLY"]["expires_at"] == "2026-08-01"
    assert candidates["LA26ALLY"]["expired"] is True

def test_extract_candidates_expiry_no_year_rolls_forward():
    # "today" is Aug 29, 2026; "Jan 5" with no year is more than 180 days
    # in the past for this year, so it should be read as Jan 5, 2027.
    html = "<html><body><p>LA26ALLY expires Jan 5</p></body></html>"
    candidates = {c["code"]: c for c in extract_candidates(html, today=date(2026, 8, 29))}
    assert candidates["LA26ALLY"]["expires_at"] == "2027-01-05"

def test_extract_candidates_no_expiry_hint():
    html = "<html><body><p>LA26ALLY is a great code</p></body></html>"
    candidates = {c["code"]: c for c in extract_candidates(html)}
    assert candidates["LA26ALLY"]["expires_at"] is None
    assert candidates["LA26ALLY"]["expired"] is None
