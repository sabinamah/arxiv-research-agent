"""Research assistant agent: answers questions using arXiv and cites its sources."""
import os
import sys

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from arxiv_tool import search_arxiv

SYSTEM_PROMPT = (
    "You are a research assistant. Use the search_arxiv tool to find relevant papers, "
    "then answer the question in a short summary. Base every claim on the search results "
    "and cite each paper with its title and URL. If the search returns an error or no "
    "relevant papers, say so instead of guessing."
)


def build_agent():
    model = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), temperature=0
    )
    return create_agent(model, [search_arxiv], system_prompt=SYSTEM_PROMPT)


def main() -> None:
    question = " ".join(sys.argv[1:]) or input("Research question: ")
    result = build_agent().invoke({"messages": [{"role": "user", "content": question}]})
    print(result["messages"][-1].text)


if __name__ == "__main__":
    main()
