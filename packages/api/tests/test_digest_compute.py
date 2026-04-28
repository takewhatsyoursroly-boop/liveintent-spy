from datetime import datetime, timedelta, timezone
from liveintent_api.digest_compute import top_advertisers_by_vertical

def test_top_advertisers_grouped_and_ranked(db_with_impressions):
    now = datetime.now(timezone.utc)
    result = top_advertisers_by_vertical(
        db_with_impressions, window_start=now - timedelta(days=2), window_end=now, top_n=10
    )
    # Result is dict[vertical -> list[(domain, count)]]
    assert "supplements" in result
    supps = result["supplements"]
    assert [d for d, _ in supps] == ["a1.com", "a2.com"]  # ordered by count desc
    assert supps[0][1] == 10
    assert supps[1][1] == 5
    assert result["finance"] == [("a3.com", 8)]

def test_top_advertisers_excludes_unclassified(db_with_impressions):
    now = datetime.now(timezone.utc)
    result = top_advertisers_by_vertical(
        db_with_impressions, window_start=now - timedelta(days=2), window_end=now, top_n=10
    )
    assert "unclassified" not in result

def test_top_n_limits_per_vertical(db_with_impressions):
    now = datetime.now(timezone.utc)
    result = top_advertisers_by_vertical(
        db_with_impressions, window_start=now - timedelta(days=2), window_end=now, top_n=1
    )
    assert len(result["supplements"]) == 1
    assert result["supplements"][0][0] == "a1.com"
