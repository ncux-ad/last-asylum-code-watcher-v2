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
