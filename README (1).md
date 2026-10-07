# arXiv Research Assistant Agent

A small LangChain agent that answers research questions by searching arXiv and citing the papers it used. It runs on Google Gemini through the free Google AI Studio tier.

## How it works

- `arxiv_tool.py`: a LangChain tool that queries the public arXiv API, parses the Atom feed, and returns title, authors, date, URL, and a shortened abstract. Network errors are returned to the agent as an error result instead of crashing it.
- `agent.py`: builds a tool-calling agent with `create_agent`. The system prompt tells the agent to base every claim on search results and to cite title and URL.
- `api.py`: a FastAPI service exposing the agent at `/ask` with validation, a timeout, and error responses.
- `tests/`: unit tests for the search tool and the API (validation, success, 502, 503, 504). They run offline with a fake agent.

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

## API

`api.py` wraps the agent in a FastAPI service with an async endpoint.

```bash
uvicorn api:app --reload
curl -X POST localhost:8000/ask -H "Content-Type: application/json" \\
  -d '{"question": "What are recent approaches to evaluating LLM agents?"}'
```

- `GET /health` returns `{"status": "ok"}`.
- `POST /ask` takes a question (3 to 500 characters) and returns the answer and its latency.
- The agent runs with a 60-second timeout. A timeout returns 504, a failure of the model or arXiv returns 502, and a missing model configuration returns 503.
- The agent is created on the first request and injected as a dependency, so tests can replace it with a fake.

## Tests

```bash
python -m pytest
```

## Limitations

- Only the first page of arXiv results is used, and abstracts are shortened to 500 characters.
- The free tier has rate limits, so a long conversation can hit them.
