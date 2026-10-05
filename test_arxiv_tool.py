import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import arxiv_tool

SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2401.00001v1</id>
    <published>2024-01-01T10:00:00Z</published>
    <title>A Study of
      Agents</title>
    <summary>  We study agents.
      They work.  </summary>
    <author><name>Ada Lovelace</name></author>
    <author><name>Alan Turing</name></author>
  </entry>
</feed>"""


def test_build_query_joins_terms_with_and():
    assert arxiv_tool.build_query("llm agents") == "all:llm AND all:agents"


def test_parse_feed_extracts_and_cleans_fields():
    papers = arxiv_tool.parse_feed(SAMPLE_FEED)
    assert papers == [
        {
            "title": "A Study of Agents",
            "authors": ["Ada Lovelace", "Alan Turing"],
            "published": "2024-01-01",
            "url": "http://arxiv.org/abs/2401.00001v1",
            "summary": "We study agents. They work.",
        }
    ]


def test_parse_feed_truncates_summary():
    papers = arxiv_tool.parse_feed(SAMPLE_FEED, max_summary=5)
    assert papers[0]["summary"] == "We st"


def test_search_arxiv_returns_parsed_results(monkeypatch):
    monkeypatch.setattr(arxiv_tool, "fetch_feed", lambda q, n: SAMPLE_FEED)
    result = arxiv_tool.search_arxiv.invoke({"query": "agents"})
    assert result[0]["title"] == "A Study of Agents"


def test_search_arxiv_clamps_max_results(monkeypatch):
    seen = {}

    def fake_fetch(query, max_results):
        seen["n"] = max_results
        return SAMPLE_FEED

    monkeypatch.setattr(arxiv_tool, "fetch_feed", fake_fetch)
    arxiv_tool.search_arxiv.invoke({"query": "agents", "max_results": 500})
    assert seen["n"] == arxiv_tool.MAX_RESULTS_LIMIT


def test_search_arxiv_reports_network_errors(monkeypatch):
    def failing_fetch(query, max_results):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(arxiv_tool, "fetch_feed", failing_fetch)
    result = arxiv_tool.search_arxiv.invoke({"query": "agents"})
    assert "error" in result[0]
