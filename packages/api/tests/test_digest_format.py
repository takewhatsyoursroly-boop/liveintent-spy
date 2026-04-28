from liveintent_api.digest_format import format_digest_message

def test_format_digest_groups_by_vertical():
    data = {
        "supplements": [("a1.com", 10), ("a2.com", 5)],
        "finance": [("a3.com", 8)],
    }
    msg = format_digest_message(data, window_label="last 24h")
    assert "supplements" in msg.lower()
    assert "finance" in msg.lower()
    assert "a1.com" in msg
    assert "10" in msg
    assert "last 24h" in msg

def test_format_digest_empty():
    msg = format_digest_message({}, window_label="last 24h")
    assert "no impressions" in msg.lower() or "no activity" in msg.lower()
