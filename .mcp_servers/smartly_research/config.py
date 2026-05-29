from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


DEFAULT_WORKSPACE_ROOT = Path(
    "/home/matheus/Documentos/vscode/baseDev/smartly.backend_smartly-dev"
)
DEFAULT_REPO_SCOPE = "smartly.backend_smartly-dev"
DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_COCOINDEX_SITE_PACKAGES = Path(
    "/home/matheus/.local/share/uv/tools/cocoindex-code/lib/python3.11/site-packages"
)
DEFAULT_ALLOWED_EXTENSIONS = (
    ".py",
    ".md",
    ".tf",
    ".toml",
    ".yml",
    ".yaml",
    ".json",
    ".txt",
    ".js",
    ".ts",
)
DEFAULT_IGNORED_SEGMENTS = {
    ".git",
    ".venv",
    ".personal_venv",
    "node_modules",
    "__pycache__",
    ".terraform",
    ".cocoindex_code",
    "build",
    ".pytest_cache",
}


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default

    try:
        value = int(raw)
    except ValueError:
        return default

    return max(minimum, min(maximum, value))


@dataclass(frozen=True)
class ServerConfig:
    workspace_root: Path
    default_repo_scope: str
    cocoindex_site_packages: Path
    rlm_model: str
    rlm_max_depth: int
    rlm_max_iterations: int
    rlm_max_timeout_seconds: int
    semantic_limit: int
    exact_limit: int
    list_limit: int
    read_max_lines: int
    read_max_chars: int
    allowed_extensions: tuple[str, ...]
    ignored_segments: set[str]

    @property
    def openrouter_api_key(self) -> str | None:
        raw = os.getenv("OPENROUTER_API_KEY")
        if raw is None:
            return None
        value = raw.strip()
        return value or None


@lru_cache(maxsize=1)
def get_config() -> ServerConfig:
    workspace_root = Path(
        os.getenv("SMARTLY_RESEARCH_WORKSPACE_ROOT", str(DEFAULT_WORKSPACE_ROOT))
    ).resolve()

    return ServerConfig(
        workspace_root=workspace_root,
        default_repo_scope=os.getenv(
            "SMARTLY_RESEARCH_DEFAULT_REPO", DEFAULT_REPO_SCOPE
        ).strip()
        or DEFAULT_REPO_SCOPE,
        cocoindex_site_packages=Path(
            os.getenv(
                "SMARTLY_RESEARCH_COCOINDEX_SITE_PACKAGES",
                str(DEFAULT_COCOINDEX_SITE_PACKAGES),
            )
        ).resolve(),
        rlm_model=os.getenv("SMARTLY_RESEARCH_RLM_MODEL", DEFAULT_MODEL).strip()
        or DEFAULT_MODEL,
        rlm_max_depth=_env_int("SMARTLY_RESEARCH_RLM_MAX_DEPTH", 2, 1, 3),
        rlm_max_iterations=_env_int("SMARTLY_RESEARCH_RLM_MAX_ITERATIONS", 8, 2, 20),
        rlm_max_timeout_seconds=_env_int(
            "SMARTLY_RESEARCH_RLM_TIMEOUT_SECONDS", 45, 10, 180
        ),
        semantic_limit=_env_int("SMARTLY_RESEARCH_SEMANTIC_LIMIT", 8, 1, 20),
        exact_limit=_env_int("SMARTLY_RESEARCH_EXACT_LIMIT", 12, 1, 50),
        list_limit=_env_int("SMARTLY_RESEARCH_LIST_LIMIT", 200, 10, 1000),
        read_max_lines=_env_int("SMARTLY_RESEARCH_READ_MAX_LINES", 120, 10, 400),
        read_max_chars=_env_int("SMARTLY_RESEARCH_READ_MAX_CHARS", 6000, 500, 20000),
        allowed_extensions=DEFAULT_ALLOWED_EXTENSIONS,
        ignored_segments=set(DEFAULT_IGNORED_SEGMENTS),
    )
