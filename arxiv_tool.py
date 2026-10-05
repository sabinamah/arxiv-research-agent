"""arXiv search tool for the research agent (standard library only)."""
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from langchain_core.tools import tool

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}
MAX_RESULTS_LIMIT = 10


def build_query(query: str) -> str:
    """Turn 'large language models' into 'all:large AND all:language AND all:models'."""
    return " AND ".join(f"all:{word}" for word in query.split())


def fetch_feed(query: str, max_results: int) -> str:
    params = urllib.parse.urlencode(
        {"search_query": build_query(query), "start": 0, "max_results": max_results}
    )
    with urllib.request.urlopen(f"{ARXIV_API}?{params}", timeout=15) as response:
        return response.read().decode("utf-8")


def parse_feed(xml_text: str, max_summary: int = 500) -> list[dict]:
    root = ET.fromstring(xml_text)
    papers = []
    for entry in root.findall("atom:entry", NS):
        summary = " ".join(entry.findtext("atom:summary", "", NS).split())
        papers.append(
            {
                "title": " ".join(entry.findtext("atom:title", "", NS).split()),
                "authors": [a.findtext("atom:name", "", NS) for a in entry.findall("atom:author", NS)],
                "published": entry.findtext("atom:published", "", NS)[:10],
                "url": entry.findtext("atom:id", "", NS),
                "summary": summary[:max_summary],
            }
        )
    return papers


@tool
def search_arxiv(query: str, max_results: int = 5) -> list[dict]:
    """Search arXiv for papers. Returns title, authors, published date, url and a
    shortened abstract for each result. Use short keyword queries."""
    max_results = max(1, min(max_results, MAX_RESULTS_LIMIT))
    try:
        return parse_feed(fetch_feed(query, max_results))
    except (urllib.error.URLError, TimeoutError, ET.ParseError) as error:
        return [{"error": f"arXiv request failed: {error}"}]
