import logging
from typing import Any
from pydantic import BaseModel, Field

from . import ToolResult

logger = logging.getLogger("insight_copilot.tools.web_search")


class WebSearchArgs(BaseModel):
    query: str = Field(description="Web search query for external macro context")
    max_results: int = Field(default=3, description="Maximum number of search results to retrieve")


def web_search(args: WebSearchArgs | dict[str, Any]) -> ToolResult:
    """
    Search the live web for external economic, market, industry, or terminology context.

    USE WHEN: the question requires external real-world context outside the dataset
    (e.g., Brazilian macroeconomic trends, currency fluctuations, retail holidays like Black Friday,
    or competitor context).

    DO NOT USE WHEN: the question asks about numbers or entities already in the dataset.
    """
    if isinstance(args, dict):
        args = WebSearchArgs(**args)

    max_r = min(max(1, args.max_results), 5)
    results = []

    try:
        # Attempt via duckduckgo-search / ddgs
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            from ddgs import DDGS

        with DDGS() as ddgs:
            raw_results = list(ddgs.text(args.query, max_results=max_r))
            for item in raw_results:
                results.append({
                    "title": item.get("title", "Untitled"),
                    "snippet": item.get("body", item.get("snippet", "")),
                    "url": item.get("href", item.get("link", "")),
                })

    except Exception as e:
        logger.warning(f"DuckDuckGo search failed or rate-limited: {e}")
        # Graceful fallback so agent does not crash
        return {
            "ok": False,
            "data": [],
            "summary": f"Web search could not be completed for query '{args.query}': {str(e)}",
            "meta": {"query": args.query, "error_type": type(e).__name__},
            "error": str(e),
        }

    if not results:
        return {
            "ok": True,
            "data": [],
            "summary": f"No external web results found for query '{args.query}'.",
            "meta": {"query": args.query, "count": 0},
            "error": None,
        }

    snippets_preview = "; ".join([f"'{r['title']}': {r['snippet'][:100]}..." for r in results[:2]])
    summary = f"Found {len(results)} external result(s) for '{args.query}': {snippets_preview}"

    return {
        "ok": True,
        "data": results,
        "summary": summary,
        "meta": {"query": args.query, "count": len(results)},
        "error": None,
    }
