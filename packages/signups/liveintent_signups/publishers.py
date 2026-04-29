"""Curated list of US publishers running LiveIntent / Zeta ads.

Each entry is a (domain, name, subscribe_url, vertical, frequency) tuple.
Tracked by the spy tool — see `liveintent-spy add-publisher` to register them
in the database after sign-ups complete.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Publisher:
    domain: str
    name: str
    subscribe_url: str
    vertical: str
    frequency: str


PUBLISHERS: list[Publisher] = [
    Publisher("nytimes.com", "NYTimes Newsletters", "https://www.nytimes.com/newsletters", "news", "daily"),
    Publisher("morningbrew.com", "Morning Brew", "https://www.morningbrew.com/daily/subscribe", "finance", "daily"),
    Publisher("marketingbrew.com", "Marketing Brew", "https://www.marketingbrew.com/subscribe", "tech", "weekday"),
    Publisher("retailbrew.com", "Retail Brew", "https://www.retailbrew.com/subscribe", "tech", "weekday"),
    Publisher("hr-brew.com", "HR Brew", "https://www.hr-brew.com/subscribe", "tech", "weekday"),
    Publisher("cfobrew.com", "CFO Brew", "https://www.cfobrew.com/subscribe", "finance", "weekday"),
    Publisher("itbrew.com", "IT Brew", "https://www.itbrew.com/subscribe", "tech", "weekday"),
    Publisher("join1440.com", "1440 Daily Digest", "https://signup.join1440.com/", "news", "daily"),
    Publisher("theskimm.com", "theSkimm", "https://www.theskimm.com/newsletters", "lifestyle", "daily"),
    Publisher("bradsdeals.com", "Brad's Deals", "https://www.bradsdeals.com/deal-alerts", "sweeps", "daily"),
    Publisher("slickdeals.net", "Slickdeals Money", "https://money.slickdeals.net/newsletters/", "sweeps", "weekly"),
    Publisher("cnet.com", "CNET Newsletters", "https://www.cnet.com/newsletters/", "tech", "daily"),
    Publisher("patch.com", "Patch", "https://patch.com/subscribe", "news", "daily"),
    Publisher("nj.com", "NJ.com", "https://www.nj.com/newsletters/", "news", "daily"),
    Publisher("cleveland.com", "Cleveland.com", "https://www.cleveland.com/newsletters/", "news", "daily"),
    Publisher("masslive.com", "MassLive", "https://www.masslive.com/newsletters/", "news", "daily"),
    Publisher("rd.com", "Reader's Digest", "https://www.rd.com/newsletter/", "lifestyle", "weekly"),
    Publisher("allrecipes.com", "Allrecipes", "https://www.allrecipes.com/account/newsletters/", "health", "daily"),
    Publisher("eatingwell.com", "EatingWell", "https://www.eatingwell.com/account/newsletters/", "health", "weekly"),
    Publisher("foodandwine.com", "Food & Wine", "https://www.foodandwine.com/account/newsletters/", "lifestyle", "weekly"),
    Publisher("bhg.com", "Better Homes & Gardens", "https://www.bhg.com/account/newsletters/", "lifestyle", "weekly"),
    Publisher("realsimple.com", "Real Simple", "https://www.realsimple.com/account/newsletters/", "lifestyle", "weekly"),
    Publisher("horoscope.com", "Horoscope.com", "https://www.horoscope.com/us/emails/email-subscription.aspx", "lifestyle", "daily"),
    Publisher("recipelion.com", "RecipeLion", "https://www.recipelion.com/index.php/myhome/eletter", "health", "daily"),
    Publisher("favecrafts.com", "FaveCrafts", "https://www.favecrafts.com/index.php/myhome/eletter", "lifestyle", "daily"),
    Publisher("allfreecrochet.com", "AllFreeCrochet", "https://www.allfreecrochet.com/index.php/myhome/eletter", "lifestyle", "daily"),
    Publisher("marketingdive.com", "Marketing Dive", "https://www.marketingdive.com/signup/", "tech", "weekday"),
    Publisher("healthcaredive.com", "Healthcare Dive", "https://www.healthcaredive.com/signup/", "health", "weekday"),
    Publisher("retaildive.com", "Retail Dive", "https://www.retaildive.com/signup/", "tech", "weekday"),
    Publisher("wellandgood.com", "Well+Good", "https://www.wellandgood.com/newsletter/", "health", "daily"),
]


def by_domain(domain: str) -> Publisher:
    for p in PUBLISHERS:
        if p.domain == domain:
            return p
    raise KeyError(f"Unknown publisher domain: {domain}")
