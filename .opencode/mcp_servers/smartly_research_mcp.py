# /// script
# requires-python = "==3.11.*"
# dependencies = [
#     "mcp",
#     "python-dotenv",
#     "rlms @ git+https://github.com/alexzhang13/rlm.git",
# ]
# ///

from __future__ import annotations

import json
import logging
import os
import warnings
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

BASEDEV_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(BASEDEV_ROOT / ".env", override=True)
load_dotenv(override=True)

from smartly_research.services import ResearchError, run_research_tool

warnings.filterwarnings(
    "ignore",
    message=r".*runner_batch_fn_async.*was never awaited.*",
    category=RuntimeWarning,
)

LOGGER = logging.getLogger("smartly_research_mcp")
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=getattr(
            logging,
            os.getenv("SMARTLY_RESEARCH_LOG_LEVEL", "INFO").upper(),
            logging.INFO,
        ),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

mcp = FastMCP(
    "smartly-research",
    instructions=(
        "Pesquisa híbrida RLM + CocoIndex para o workspace local. "
        "Use para investigação de código, impacto, fluxo e testes relacionados."
    ),
)


def _normalize_mode(mode: str) -> str:
    normalized = (mode or "quick").strip().lower()
    if normalized not in {"quick", "structured", "deep"}:
        raise ResearchError("mode deve ser quick, structured ou deep")
    return normalized


def _serialize(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
def research_codebase(
    question: str,
    repo_scope: str = "smartly.backend_smartly-dev",
    mode: str = "quick",
    limit: int = 8,
) -> str:
    """Pesquisa a base de código local com RLM híbrido apoiado por CocoIndex e evidência local."""
    try:
        return _serialize(
            run_research_tool(
                tool_name="research_codebase",
                user_input=question,
                repo_scope=repo_scope,
                mode=_normalize_mode(mode),
                limit=limit,
            )
        )
    except Exception as exc:
        LOGGER.exception("research_codebase failed")
        return _serialize({"tool": "research_codebase", "error": str(exc)})


@mcp.tool()
def analyze_change_impact(
    target: str,
    repo_scope: str = "smartly.backend_smartly-dev",
    mode: str = "deep",
    limit: int = 8,
) -> str:
    """Analisa impacto potencial de uma mudança com apoio de busca semântica, confirmação local e síntese via RLM."""
    try:
        return _serialize(
            run_research_tool(
                tool_name="analyze_change_impact",
                user_input=target,
                repo_scope=repo_scope,
                mode=_normalize_mode(mode),
                limit=limit,
            )
        )
    except Exception as exc:
        LOGGER.exception("analyze_change_impact failed")
        return _serialize({"tool": "analyze_change_impact", "error": str(exc)})


@mcp.tool()
def trace_feature_flow(
    entrypoint_or_symbol: str,
    repo_scope: str = "smartly.backend_smartly-dev",
    mode: str = "deep",
    limit: int = 8,
) -> str:
    """Rastreia o fluxo técnico de uma feature, símbolo ou entrypoint dentro do workspace local."""
    try:
        return _serialize(
            run_research_tool(
                tool_name="trace_feature_flow",
                user_input=entrypoint_or_symbol,
                repo_scope=repo_scope,
                mode=_normalize_mode(mode),
                limit=limit,
            )
        )
    except Exception as exc:
        LOGGER.exception("trace_feature_flow failed")
        return _serialize({"tool": "trace_feature_flow", "error": str(exc)})


@mcp.tool()
def find_related_tests(
    target: str,
    repo_scope: str = "smartly.backend_smartly-dev",
    mode: str = "structured",
    limit: int = 8,
) -> str:
    """Encontra testes relacionados a um alvo técnico usando busca semântica, confirmação local e síntese via RLM."""
    try:
        return _serialize(
            run_research_tool(
                tool_name="find_related_tests",
                user_input=target,
                repo_scope=repo_scope,
                mode=_normalize_mode(mode),
                limit=limit,
            )
        )
    except Exception as exc:
        LOGGER.exception("find_related_tests failed")
        return _serialize({"tool": "find_related_tests", "error": str(exc)})


if __name__ == "__main__":
    mcp.run()
