"""resolve(): brand name or website -> Company (name, domain, existing-customer flag).

Knows nothing about any brand in advance: the domain comes from a search, and the
customer flag comes from flowcode_context.md section C, then one search.
"""
import re
from urllib.parse import urlparse

from agent import config
from agent.models import Company, RunStats, Source
from agent.search import SearchProvider

# Sites that are about a brand but are not the brand's own site.
NOT_BRAND_SITES = {
    "wikipedia.org", "linkedin.com", "facebook.com", "instagram.com", "x.com",
    "twitter.com", "youtube.com", "tiktok.com", "crunchbase.com", "yelp.com",
}


def normalize(text: str) -> str:
    """"Dunkin' Donuts!" -> "dunkin donuts": lowercase, no apostrophes, other punctuation to spaces."""
    text = re.sub(r"['’]", "", text.lower())
    return " ".join(re.sub(r"[^a-z0-9+]+", " ", text).split())


def domain_of(url: str) -> str:
    """'https://www.example.com/path' -> 'example.com'."""
    host = urlparse(url if "//" in url else "//" + url).netloc.lower()
    return host.removeprefix("www.")


def load_known_customers() -> dict[str, str]:
    """Section C of flowcode_context.md as {normalized alias: the full line it came from}."""
    text = config.CONTEXT_FILE.read_text(encoding="utf-8")
    match = re.search(r"^## C\.(.*?)^## D\.", text, flags=re.M | re.S)
    if match is None:
        raise ValueError(f"Section C (known customers) not found in {config.CONTEXT_FILE.name}")
    known = {}
    for line in match.group(1).splitlines():
        if line.startswith("- "):
            for alias in line[2:].split(" / "):
                known[normalize(alias)] = line[2:].strip()
    return known


def find_domain(name: str, results: list[Source]) -> str:
    """Pick the brand's own site: a domain containing the name wins, else the first non-directory site."""
    candidates = [domain_of(s.url) for s in results]
    candidates = [d for d in candidates if not any(d == x or d.endswith("." + x) for x in NOT_BRAND_SITES)]
    compact = normalize(name).replace(" ", "")
    return next((d for d in candidates if compact in d.replace("-", "")), candidates[0] if candidates else "")


def mentions_together(text: str, name: str) -> str | None:
    """The first sentence that names both the brand and Flowcode, if any."""
    for sentence in re.split(r"(?<=[.!?])\s+|\n", text):
        words = f" {normalize(sentence)} "
        if f" {normalize(name)} " in words and " flowcode " in words:
            return sentence.strip()[:300]
    return None


async def resolve(query: str, search: SearchProvider, stats: RunStats) -> Company:
    """Turn what the user typed into a Company, flagging likely existing Flowcode customers."""
    query = query.strip()
    if "." in query and " " not in query:  # a website was given
        domain = domain_of(query)
        name = domain.split(".")[0]
    else:
        name = query
        homepage = await search.search(f"{name} official website", stats, recent_only=False)
        domain = find_domain(name, homepage)

    listed = load_known_customers().get(normalize(name))
    if listed:
        evidence = f"Listed in flowcode_context.md known customers: {listed}"
        return Company(name=name, domain=domain, is_existing_customer=True, customer_evidence=evidence)

    for source in await search.search(f"{name} Flowcode", stats, recent_only=False):
        sentence = mentions_together(source.text, name)
        if sentence:
            evidence = f'{source.url}: "{sentence}"'
            return Company(name=name, domain=domain, is_existing_customer=True, customer_evidence=evidence)
    return Company(name=name, domain=domain)
