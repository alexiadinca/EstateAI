"""Safety rules of the listing page fetcher. No real network requests are made."""

import httpx2
import pytest

from app.extraction import fetcher
from app.extraction.fetcher import (
    ListingUnavailableError,
    UnsupportedListingUrlError,
    fetch_listing_page,
    identify_site,
)

STORIA_URL = "https://www.storia.ro/ro/oferta/apartament-IDabc"


@pytest.fixture(autouse=True)
def public_dns(monkeypatch):
    """Pretend every host resolves to a public address unless a test says otherwise."""
    monkeypatch.setattr(fetcher, "resolve_addresses", lambda host: ["93.184.216.34"])


def client_for(handler) -> httpx2.Client:
    return httpx2.Client(transport=httpx2.MockTransport(handler), follow_redirects=False)


@pytest.mark.parametrize(
    "url, expected",
    [
        (STORIA_URL, ("storia", "storia.ro")),
        ("https://storia.ro/ro/oferta/x", ("storia", "storia.ro")),
        ("https://www.olx.ro/d/oferta/x.html", ("olx", "olx.ro")),
    ],
)
def test_supported_links_are_recognised(url, expected):
    assert identify_site(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "http://www.storia.ro/ro/oferta/x",  # not https
        "https://www.imobiliare.ro/oferta/x",  # unsupported website
        "https://storia.ro.attacker.com/x",  # look-alike domain
        "https://evilstoria.ro/x",  # look-alike domain
        "https://user:pass@www.storia.ro/x",  # credentials in the link
        "https://www.storia.ro:8443/x",  # unexpected port
        "https://127.0.0.1/x",
        "file:///etc/passwd",
    ],
)
def test_other_links_are_refused(url):
    with pytest.raises(UnsupportedListingUrlError):
        identify_site(url)


def test_host_resolving_to_a_private_address_is_refused(monkeypatch):
    monkeypatch.setattr(fetcher, "resolve_addresses", lambda host: ["10.0.0.5"])

    with pytest.raises(ListingUnavailableError):
        fetch_listing_page(STORIA_URL, client_for(lambda request: httpx2.Response(200)))


def test_page_is_downloaded():
    client = client_for(lambda request: httpx2.Response(200, text="<html>listing</html>"))

    page = fetch_listing_page(STORIA_URL, client)

    assert page.site == "storia"
    assert page.html == "<html>listing</html>"


def test_redirect_inside_the_same_website_is_followed():
    def handler(request):
        if request.url.path == "/old":
            return httpx2.Response(301, headers={"location": "/ro/oferta/new"})
        return httpx2.Response(200, text="moved listing")

    page = fetch_listing_page("https://www.storia.ro/old", client_for(handler))

    assert page.url == "https://www.storia.ro/ro/oferta/new"


def test_redirect_to_another_website_is_refused():
    def handler(request):
        return httpx2.Response(302, headers={"location": "https://internal.example/admin"})

    with pytest.raises(UnsupportedListingUrlError):
        fetch_listing_page(STORIA_URL, client_for(handler))


def test_endless_redirects_are_stopped():
    def handler(request):
        return httpx2.Response(302, headers={"location": STORIA_URL})

    with pytest.raises(ListingUnavailableError):
        fetch_listing_page(STORIA_URL, client_for(handler))


@pytest.mark.parametrize("status_code", [404, 403, 429, 500])
def test_error_responses_explain_the_problem(status_code):
    with pytest.raises(ListingUnavailableError):
        fetch_listing_page(STORIA_URL, client_for(lambda request: httpx2.Response(status_code)))


def test_oversized_page_is_refused(monkeypatch):
    monkeypatch.setattr(fetcher, "MAX_PAGE_BYTES", 10)
    client = client_for(lambda request: httpx2.Response(200, text="x" * 100))

    with pytest.raises(ListingUnavailableError):
        fetch_listing_page(STORIA_URL, client)
