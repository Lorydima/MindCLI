# Tavily web search integration for fetching real-time information.

import webbrowser
from tavily import TavilyClient
from mindcli import state
from mindcli.utils import extract_domain


def open_tavily_site():
    """Opens the Tavily API dashboard in the default web browser."""
    webbrowser.open("https://app.tavily.com/")


def format_tavily_context(payload: dict) -> str:
    """Builds a compact context block from Tavily search results."""
    lines = []
    answer = (payload.get("answer") or "").strip()
    if answer:
        lines.append(f"Answer: {answer}")

    results = payload.get("results") or []
    for idx, result in enumerate(results[:5], 1):
        title = (result.get("title") or "").strip()
        url = (result.get("url") or "").strip()
        content = (result.get("content") or result.get("raw_content") or "").strip()
        lines.append(f"[{idx}] {title}")
        if url:
            lines.append(f"URL: {url}")
        if content:
            lines.append(f"Content: {content[:1800]}")
        lines.append("")

    return "\n".join(lines).strip()


def tavily_search(query: str, api_key: str) -> dict:
    """Calls Tavily Search through the official SDK and returns a dict payload."""
    client = TavilyClient(api_key=api_key)

    search_kwargs = {
        "query": query,
        "search_depth": "basic",
        "max_results": 5,
        "include_answer": True,
        "include_raw_content": True,
        "include_favicon": False,
    }

    domain = extract_domain(query)
    if domain:
        search_kwargs["include_domains"] = [domain]

    response = client.search(**search_kwargs)
    if isinstance(response, dict):
        return response

    payload = {}
    for key in ("answer", "query", "results", "images", "response_time"):
        if hasattr(response, key):
            payload[key] = getattr(response, key)
    return payload
