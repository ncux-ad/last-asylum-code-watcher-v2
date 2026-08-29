from watcher.extractor import extract_codes

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
