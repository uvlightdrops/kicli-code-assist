#!/usr/bin/env python3
"""Standalone LLM Service for kicli-code-assist.

Runs as separate process and handles all LLM queries.
Allows reloading LLM code without restarting TUI.

Usage:
    python -m kicli_code_assist.services.llm_service [--port 9001]

TUI connects via:
    LLMServiceClient("http://localhost:9001")
"""

import asyncio
import json
import logging
import argparse
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import sys

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("ERROR: FastAPI not installed. Install with: pip install fastapi uvicorn")
    sys.exit(1)

from kicli_code_assist.llm_integration import AsyncLLMIntegration, get_async_integration
from ki_core.core.response_parser import ResponseParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Message(BaseModel):
    """LLM Message."""
    role: str  # "system", "user", "assistant"
    content: str


class LLMQueryRequest(BaseModel):
    """Request to query LLM."""
    messages: List[Message]
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class LLMQueryResponse(BaseModel):
    """Response from LLM."""
    response: str
    tokens_used: Optional[int] = None
    provider: Optional[str] = None
    error: Optional[str] = None


@dataclass
class LLMServiceConfig:
    """Configuration for LLM service."""
    host: str = "127.0.0.1"
    port: int = 9001
    reload_on_change: bool = True


class LLMService:
    """Standalone LLM service."""

    def __init__(self, config: Optional[LLMServiceConfig] = None):
        self.config = config or LLMServiceConfig()
        self.llm = get_async_integration()
        self.parser = ResponseParser()
        self.app = FastAPI(title="KI LLM Service")
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup FastAPI routes."""

        @self.app.get("/health")
        async def health():
            """Health check."""
            return {
                "status": "healthy",
                "service": "LLMService",
                "port": self.config.port,
            }

        @self.app.post("/query", response_model=LLMQueryResponse)
        async def query_llm(req: LLMQueryRequest):
            """Query LLM with messages."""
            try:
                # Convert Pydantic Message to dict
                messages = [{"role": m.role, "content": m.content} for m in req.messages]

                logger.info(f"LLM Query: {len(messages)} messages, system_prompt: {bool(req.system_prompt)}")

                # Query LLM
                response = await self.llm.query(
                    messages=messages,
                    system_prompt=req.system_prompt,
                    temperature=req.temperature,
                    max_tokens=req.max_tokens,
                    on_progress=None,  # Service doesn't stream progress
                )

                logger.info(f"LLM Response: {len(response)} chars")

                return LLMQueryResponse(
                    response=response,
                    provider="ollama/openai",  # TODO: get actual provider
                )
            except Exception as e:
                logger.error(f"LLM Query Error: {e}", exc_info=True)
                return LLMQueryResponse(
                    response="",
                    error=str(e),
                )

        @self.app.post("/reload")
        async def reload_llm():
            """Reload LLM integration (e.g., after code changes)."""
            try:
                logger.info("Reloading LLM integration...")
                self.llm = get_async_integration()
                return {"status": "reloaded"}
            except Exception as e:
                logger.error(f"Reload Error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def run(self) -> None:
        """Start the service."""
        logger.info(f"Starting LLM Service on {self.config.host}:{self.config.port}")
        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info",
        )


class LLMServiceClient:
    """Client for LLM Service (used by TUI)."""

    def __init__(self, service_url: str = "http://127.0.0.1:9001"):
        self.service_url = service_url
        try:
            import httpx
            self.httpx = httpx
        except ImportError:
            logger.warning("httpx not installed, using requests fallback")
            import requests
            self.httpx = requests

    async def query(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Query LLM via service."""
        req = LLMQueryRequest(
            messages=[Message(role=m["role"], content=m["content"]) for m in messages],
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        try:
            async with self.httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.service_url}/query",
                    json=json.loads(req.model_dump_json()),
                    timeout=60.0,
                )
                resp.raise_for_status()
                data = resp.json()

                if data.get("error"):
                    raise RuntimeError(f"LLM Error: {data['error']}")

                return data["response"]
        except Exception as e:
            logger.error(f"Service Query Error: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if service is healthy."""
        try:
            async with self.httpx.AsyncClient() as client:
                resp = await client.get(f"{self.service_url}/health", timeout=5.0)
                return resp.status_code == 200
        except Exception:
            return False

    def reload(self) -> None:
        """Tell service to reload LLM (after code changes)."""
        try:
            import requests
            resp = requests.post(f"{self.service_url}/reload", timeout=10.0)
            resp.raise_for_status()
            logger.info("Service reloaded successfully")
        except Exception as e:
            logger.error(f"Reload Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LLM Service for kicli-code-assist")
    parser.add_argument("--host", default="127.0.0.1", help="Service host")
    parser.add_argument("--port", type=int, default=9001, help="Service port")
    args = parser.parse_args()

    config = LLMServiceConfig(host=args.host, port=args.port)
    service = LLMService(config)
    service.run()


if __name__ == "__main__":
    main()
