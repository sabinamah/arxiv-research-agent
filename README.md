# arXiv Research Assistant Agent

A small LangChain agent that answers research questions by searching arXiv and citing the papers it used. It runs on Google Gemini through the free Google AI Studio tier.

## How it works

- `arxiv_tool.py`: a LangChain tool that queries the public arXiv API, parses the Atom feed, and returns title, authors, date, URL, and a shortened abstract. Network errors are returned to the agent as an error result instead of crashing it.
- `agent.py`: builds a tool-calling agent with `create_agent`. The system prompt tells the agent to base every claim on search results and to cite title and URL.
- `tests/`: unit tests for query building, feed parsing, result limits, and error handling. They run offline.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GOOGLE_API_KEY="your-key-from-aistudio.google.com"
```

## Usage

```bash
python agent.py "What are recent approaches to evaluating LLM agents?"
```

Set `GEMINI_MODEL` to use a different Gemini model (default: `gemini-2.5-flash`).

## Tests

```bash
python -m pytest
```

## Limitations

- Only the first page of arXiv results is used, and abstracts are shortened to 500 characters.
- The free tier has rate limits, so a long conversation can hit them.
