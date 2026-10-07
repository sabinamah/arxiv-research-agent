"""FastAPI service around the arXiv research agent."""
import asyncio
import logging
import time
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent import build_agent

logger = logging.getLogger("arxiv_api")
app = FastAPI(title="arXiv Research Agent API")

REQUEST_TIMEOUT_SECONDS = 60


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AskResponse(BaseModel):
    answer: str
    latency_seconds: float


@lru_cache
def _cached_agent():
    return build_agent()


def get_agent():
    try:
        return _cached_agent()
    except Exception:
        logger.exception("agent could not be created")
        raise HTTPException(status_code=503, detail="The model is not configured (check GOOGLE_API_KEY).")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest, agent=Depends(get_agent)) -> AskResponse:
    start = time.perf_counter()
    try:
        result = await asyncio.wait_for(
            agent.ainvoke({"messages": [{"role": "user", "content": request.question}]}),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("agent timed out after %ss", REQUEST_TIMEOUT_SECONDS)
        raise HTTPException(status_code=504, detail="The agent took too long to answer.")
    except Exception:
        logger.exception("agent call failed")
        raise HTTPException(status_code=502, detail="The model or arXiv failed. Please try again.")
    latency = round(time.perf_counter() - start, 2)
    logger.info("question answered in %.2fs", latency)
    return AskResponse(answer=result["messages"][-1].text, latency_seconds=latency)
