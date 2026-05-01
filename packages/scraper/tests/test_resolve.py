import pytest
import httpx
import respx
from liveintent_scraper.resolve import resolve_final_url, extract_advertiser_domain

@respx.mock
def test_follows_single_redirect():
    respx.get("https://track.liveintent.com/li/r/abc").mock(
        return_value=httpx.Response(302, headers={"location": "https://newchapter.com/landing?utm=x"})
    )
    respx.get("https://newchapter.com/landing").mock(return_value=httpx.Response(200))
    final = resolve_final_url("https://track.liveintent.com/li/r/abc")
    assert final == "https://newchapter.com/landing?utm=x"

@respx.mock
def test_follows_multi_hop_redirects():
    respx.get("https://track.liveintent.com/li/r/abc").mock(
        return_value=httpx.Response(302, headers={"location": "https://hop1.com/x"})
    )
    respx.get("https://hop1.com/x").mock(
        return_value=httpx.Response(302, headers={"location": "https://final.com/lp"})
    )
    respx.get("https://final.com/lp").mock(return_value=httpx.Response(200))
    final = resolve_final_url("https://track.liveintent.com/li/r/abc")
    assert final == "https://final.com/lp"

@respx.mock
def test_caps_at_max_redirects():
    for i in range(15):
        respx.get(f"https://hop{i}.com/").mock(
            return_value=httpx.Response(302, headers={"location": f"https://hop{i+1}.com/"})
        )
    final = resolve_final_url("https://hop0.com/", max_redirects=10)
    assert final is None  # exceeded budget

@respx.mock
def test_returns_none_on_timeout():
    respx.get("https://slow.com").mock(side_effect=httpx.TimeoutException("slow"))
    assert resolve_final_url("https://slow.com") is None

def test_advertiser_domain_extracts_etld_plus_one():
    assert extract_advertiser_domain("https://www.newchapter.com/products/x?u=y") == "newchapter.com"
    assert extract_advertiser_domain("https://shop.example.co.uk/p") == "example.co.uk"
    assert extract_advertiser_domain("invalid") is None

def test_advertiser_domain_blocks_liveintent_infra():
    """LiveIntent's own redirect/AdChoices/pixel domains are never real advertisers.
    A click resolving here means we picked up a privacy link or pixel-only slot."""
    assert extract_advertiser_domain("https://i6.liadm.com/s/section/124305700") is None
    assert extract_advertiser_domain("https://www.liveintent.com/ad-choices/?utm=x") is None
    assert extract_advertiser_domain("https://c.licasd.com/ads/abc/def.jpeg") is None
    assert extract_advertiser_domain("https://he.lijit.com/merge?pid=8105") is None
    assert extract_advertiser_domain("https://thrtle.com/3012?sha256=abc") is None
