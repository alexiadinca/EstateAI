"""Safe download of a single listing page chosen by the user.

Only https pages from supported listing websites are fetched. Every redirect target is
checked again, hosts that resolve to private or local network addresses are refused, and
the response is limited in time and size. EstateAI identifies itself honestly and opens only
the one page the user provided; it never crawls or follows links.
"""

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx2

# Website domain mapped to the parser that understands its pages.
SUPPORTED_SITES = {"storia.ro": "storia", "olx.ro": "olx"}

USER_AGENT = (
    "EstateAI/0.1 (bachelor thesis prototype; imports one listing page at a user's request)"
)
REQUEST_TIMEOUT_SECONDS = 10
MAX_REDIRECTS = 3
# Listing pages are large because they embed their data; 6 MB leaves room without risk.
MAX_PAGE_BYTES = 6_000_000


class UnsupportedListingUrlError(Exception):
    """The link is not an https listing page from a supported website."""


class ListingUnavailableError(Exception):
    """The listing page could not be downloaded or read."""


@dataclass(frozen=True)
class FetchedPage:
    url: str
    site: str
    domain: str
    html: str


def identify_site(url: str) -> tuple[str, str]:
    """Return (parser name, domain) for a supported listing link, or raise an error."""
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or parts.username or parts.password:
        raise UnsupportedListingUrlError("Use the https link of the listing page.")
    if parts.port not in (None, 443):
        raise UnsupportedListingUrlError("This link uses an unsupported port.")
    for domain, site in SUPPORTED_SITES.items():
        if host == domain or host.endswith(f".{domain}"):
            return site, domain
    supported = " and ".join(SUPPORTED_SITES)
    raise UnsupportedListingUrlError(
        f"Links from this website cannot be read automatically. Supported: {supported}. "
        "You can paste the listing text instead."
    )


def resolve_addresses(host: str) -> list[str]:
    """IP addresses a host name resolves to. Kept separate so tests can replace it."""
    return [info[4][0] for info in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)]


def ensure_public_host(host: str) -> None:
    """Refuse hosts that point into a private, local or otherwise non-public network."""
    try:
        addresses = resolve_addresses(host)
    except OSError as error:
        raise ListingUnavailableError("The listing website could not be reached.") from error
    if not addresses or not all(ipaddress.ip_address(a).is_global for a in addresses):
        raise ListingUnavailableError("The listing website could not be reached.")


def create_http_client() -> httpx2.Client:
    return httpx2.Client(
        timeout=REQUEST_TIMEOUT_SECONDS,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8"},
        follow_redirects=False,
    )


def fetch_listing_page(url: str, client: httpx2.Client | None = None) -> FetchedPage:
    owns_client = client is None
    client = client or create_http_client()
    try:
        current_url = url.strip()
        for _ in range(MAX_REDIRECTS + 1):
            site, domain = identify_site(current_url)
            ensure_public_host(urlsplit(current_url).hostname or "")
            with client.stream("GET", current_url) as response:
                if response.is_redirect:
                    current_url = urljoin(current_url, response.headers.get("location", ""))
                    continue
                _raise_for_status(response.status_code)
                return FetchedPage(
                    url=current_url, site=site, domain=domain, html=_read_limited(response)
                )
        raise ListingUnavailableError("The listing link redirects too many times.")
    except httpx2.HTTPError as error:
        raise ListingUnavailableError(
            "The listing website did not respond. Try again later or paste the listing text."
        ) from error
    finally:
        if owns_client:
            client.close()


def _raise_for_status(status_code: int) -> None:
    if status_code in (404, 410):
        raise ListingUnavailableError("This listing was not found. It may have been removed.")
    if status_code in (401, 403, 429):
        raise ListingUnavailableError(
            "The listing website refused automatic access. Paste the listing text instead."
        )
    if status_code >= 400:
        raise ListingUnavailableError(
            "The listing website returned an error. Try again later or paste the listing text."
        )


def _read_limited(response: httpx2.Response) -> str:
    content = bytearray()
    for chunk in response.iter_bytes():
        content.extend(chunk)
        if len(content) > MAX_PAGE_BYTES:
            raise ListingUnavailableError("The listing page is too large to read.")
    return content.decode(response.encoding or "utf-8", errors="replace")
