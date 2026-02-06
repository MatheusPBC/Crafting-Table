# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp",
#     "docker",
# ]
# ///

from __future__ import annotations

import docker
from docker.errors import APIError, DockerException, NotFound
import json
import logging
import os
import re
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP


LOGGER = logging.getLogger("docker_mcp_server")
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=getattr(logging, os.getenv("DOCKER_MCP_LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


_CONTAINER_IDENTIFIER_REGEX = re.compile(r"^(?:[a-fA-F0-9]{12,64}|[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127})$")


@dataclass(frozen=True)
class DockerMCPConfig:
    docker_timeout_seconds: int
    list_limit: int
    list_include_stopped: bool
    log_tail_default: int
    log_tail_max: int
    max_log_chars: int
    max_image_chars: int
    allowed_container_pattern: str


def _clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def _get_env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        parsed = int(raw_value)
    except ValueError:
        LOGGER.warning("Invalid integer for %s; using default=%s", name, default)
        return default

    clamped = _clamp_int(parsed, minimum, maximum)
    if clamped != parsed:
        LOGGER.warning("Clamped %s from %s to %s", name, parsed, clamped)
    return clamped


def _get_env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    LOGGER.warning("Invalid boolean for %s; using default=%s", name, default)
    return default


def _load_config() -> DockerMCPConfig:
    config = DockerMCPConfig(
        docker_timeout_seconds=_get_env_int("DOCKER_MCP_TIMEOUT_SECONDS", default=5, minimum=1, maximum=30),
        list_limit=_get_env_int("DOCKER_MCP_LIST_LIMIT", default=200, minimum=1, maximum=500),
        list_include_stopped=_get_env_bool("DOCKER_MCP_LIST_INCLUDE_STOPPED", default=True),
        log_tail_default=_get_env_int("DOCKER_MCP_LOG_TAIL_DEFAULT", default=50, minimum=1, maximum=1000),
        log_tail_max=_get_env_int("DOCKER_MCP_LOG_TAIL_MAX", default=200, minimum=1, maximum=5000),
        max_log_chars=_get_env_int("DOCKER_MCP_MAX_LOG_CHARS", default=50000, minimum=500, maximum=200000),
        max_image_chars=_get_env_int("DOCKER_MCP_MAX_IMAGE_CHARS", default=256, minimum=32, maximum=2048),
        allowed_container_pattern=os.getenv("DOCKER_MCP_ALLOWED_CONTAINER_PATTERN", r"^[a-zA-Z0-9_.-]+$").strip(),
    )

    if config.log_tail_default > config.log_tail_max:
        LOGGER.warning(
            "DOCKER_MCP_LOG_TAIL_DEFAULT (%s) exceeds DOCKER_MCP_LOG_TAIL_MAX (%s). Using max value.",
            config.log_tail_default,
            config.log_tail_max,
        )
        return DockerMCPConfig(
            docker_timeout_seconds=config.docker_timeout_seconds,
            list_limit=config.list_limit,
            list_include_stopped=config.list_include_stopped,
            log_tail_default=config.log_tail_max,
            log_tail_max=config.log_tail_max,
            max_log_chars=config.max_log_chars,
            max_image_chars=config.max_image_chars,
            allowed_container_pattern=config.allowed_container_pattern,
        )

    return config


CONFIG = _load_config()

try:
    _ALLOWED_CONTAINER_REGEX = re.compile(CONFIG.allowed_container_pattern)
except re.error:
    LOGGER.warning(
        "Invalid DOCKER_MCP_ALLOWED_CONTAINER_PATTERN; falling back to safe default pattern"
    )
    _ALLOWED_CONTAINER_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+$")


def _error_payload(code: str, message: str) -> str:
    return json.dumps({"error": {"code": code, "message": message}}, ensure_ascii=False)


def _validate_container_identifier(container_name: str) -> str:
    if not isinstance(container_name, str):
        raise ValueError("container_name must be a string")

    normalized = container_name.strip()
    if not normalized:
        raise ValueError("container_name cannot be empty")

    if len(normalized) > 128:
        raise ValueError("container_name is too long")

    if not _CONTAINER_IDENTIFIER_REGEX.fullmatch(normalized):
        raise ValueError("container_name contains invalid characters")

    if not _ALLOWED_CONTAINER_REGEX.fullmatch(normalized):
        raise ValueError("container_name is not allowed by policy")

    return normalized


def _normalize_tail(tail: int) -> int:
    if isinstance(tail, bool) or not isinstance(tail, int):
        raise ValueError("tail must be an integer")

    clamped = _clamp_int(tail, 1, CONFIG.log_tail_max)
    if clamped != tail:
        LOGGER.warning("Clamped tail from %s to %s", tail, clamped)
    return clamped


def _truncate_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[-max_chars:]

# Cria o servidor MCP
mcp = FastMCP("docker-custom")

def get_client():
    return docker.from_env(timeout=CONFIG.docker_timeout_seconds)

@mcp.tool()
def list_containers() -> str:
    """Lista todos os containers ativos e inativos."""
    client = None
    try:
        client = get_client()
        containers = []

        all_containers = client.containers.list(all=CONFIG.list_include_stopped)
        if len(all_containers) > CONFIG.list_limit:
            LOGGER.warning(
                "Container list truncated from %s to %s",
                len(all_containers),
                CONFIG.list_limit,
            )
            all_containers = all_containers[: CONFIG.list_limit]

        for c in all_containers:
            image_str = _truncate_text(str(c.image), CONFIG.max_image_chars)
            containers.append({
                "id": c.short_id,
                "name": c.name,
                "status": c.status,
                "image": image_str,
            })

        return json.dumps(containers, indent=2)
    except (APIError, DockerException, OSError, TimeoutError):
        LOGGER.exception("Docker daemon unavailable while listing containers")
        return _error_payload("DOCKER_UNAVAILABLE", "Docker daemon unavailable or operation timed out")
    except Exception:
        LOGGER.exception("Unexpected error while listing containers")
        return _error_payload("INTERNAL_ERROR", "Unexpected error while listing containers")
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                LOGGER.debug("Failed to close docker client after list_containers", exc_info=True)

@mcp.tool()
def get_logs(container_name: str, tail: int = 50) -> str:
    """Pega os logs recentes de um container."""
    client = None
    try:
        normalized_container_name = _validate_container_identifier(container_name)
        safe_tail = _normalize_tail(tail if tail is not None else CONFIG.log_tail_default)

        client = get_client()
        container = client.containers.get(normalized_container_name)
        logs_bytes = container.logs(tail=safe_tail, stdout=True, stderr=True)
        logs_text = logs_bytes.decode("utf-8", errors="replace") if isinstance(logs_bytes, bytes) else str(logs_bytes)

        if len(logs_text) > CONFIG.max_log_chars:
            LOGGER.warning(
                "Log output truncated for container %s from %s to %s chars",
                normalized_container_name,
                len(logs_text),
                CONFIG.max_log_chars,
            )
            logs_text = _truncate_text(logs_text, CONFIG.max_log_chars)

        return logs_text
    except ValueError:
        LOGGER.info("Invalid input for get_logs")
        return _error_payload("INVALID_ARGUMENT", "Invalid container_name or tail value")
    except NotFound:
        LOGGER.info("Container not found for get_logs")
        return _error_payload("CONTAINER_NOT_FOUND", "Container not found")
    except (APIError, DockerException, OSError, TimeoutError):
        LOGGER.exception("Docker daemon unavailable while fetching logs")
        return _error_payload("DOCKER_UNAVAILABLE", "Docker daemon unavailable or operation timed out")
    except Exception:
        LOGGER.exception("Unexpected error while reading logs")
        return _error_payload("INTERNAL_ERROR", "Unexpected error while reading logs")
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                LOGGER.debug("Failed to close docker client after get_logs", exc_info=True)

if __name__ == "__main__":
    mcp.run()
