"""Source route policy for public StackOverflow and Stack Exchange API routes."""

from __future__ import annotations

from urllib.parse import urlparse


ALLOWED_HOSTS = {"stackoverflow.com", "api.stackexchange.com", "stackprinter.appspot.com"}
FORBIDDEN_MARKERS = (
    "/users/login",
    "/users/signup",
    "/users/logout",
    "/users/account",
    "/users/current",
    "/inbox",
    "/revisions/",
    "/posts/",
    "/review/",
    "/search",
    "/questions/ask",
    "/edit",
    "/delete",
    "internal-search",
)


def route_decision(url: str) -> dict[str, object]:
    parsed = urlparse(url)
    lowered = url.lower()
    reasons: list[str] = []
    host = parsed.netloc.lower()
    allowed = parsed.scheme in {"http", "https"} and host in ALLOWED_HOSTS
    if not allowed:
        reasons.append("not an allowed public StackOverflow/Stack Exchange host")
    if any(marker in lowered for marker in FORBIDDEN_MARKERS):
        allowed = False
        reasons.append("forbidden login/account/private/search/write route")
    if host == "stackoverflow.com" and ("/answer" in lowered or "/comment" in lowered):
        allowed = False
        reasons.append("forbidden StackOverflow write route")
    if host == "stackoverflow.com" and not (parsed.path.startswith("/questions/") or parsed.path.startswith("/q/")):
        allowed = False
        reasons.append("not a bounded public question route")
    if host == "api.stackexchange.com" and not parsed.path.startswith("/2."):
        allowed = False
        reasons.append("not a versioned Stack Exchange API route")
    if host == "stackprinter.appspot.com" and "service=stackoverflow" not in lowered:
        allowed = False
        reasons.append("StackPrinter route must be scoped to service=stackoverflow")
    if parsed.query and host == "stackoverflow.com":
        reasons.append("query string requires manual review")
    return {
        "schema": "aoa_stackoverflow_route_decision_v1",
        "url": url,
        "allowed": allowed,
        "reasons": reasons,
        "read_only": True,
        "network_default": "disabled",
    }
