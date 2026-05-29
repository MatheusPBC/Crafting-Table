# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp",
#     "requests",
#     "docker",
# ]
# ///

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any

import docker
import requests
from docker.errors import APIError, DockerException, NotFound
from mcp.server.fastmcp import FastMCP


LOGGER = logging.getLogger("qdrant_mcp_server")
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=getattr(
            logging, os.getenv("QDRANT_MCP_LOG_LEVEL", "INFO").upper(), logging.INFO
        ),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


COLLECTION_NAME_REGEX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,254}$")
CONTAINER_NAME_REGEX = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}$")


@dataclass(frozen=True)
class QdrantMcpConfig:
    base_url: str
    timeout_seconds: int
    docker_timeout_seconds: int
    max_limit: int


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


def _load_config() -> QdrantMcpConfig:
    base_url = os.getenv("QDRANT_BASE_URL", "http://localhost:6333").strip()
    if not base_url:
        base_url = "http://localhost:6333"

    return QdrantMcpConfig(
        base_url=base_url.rstrip("/"),
        timeout_seconds=_get_env_int(
            "QDRANT_TIMEOUT_SECONDS", default=8, minimum=1, maximum=60
        ),
        docker_timeout_seconds=_get_env_int(
            "QDRANT_DOCKER_TIMEOUT_SECONDS", default=5, minimum=1, maximum=30
        ),
        max_limit=_get_env_int(
            "QDRANT_MAX_LIMIT", default=100, minimum=1, maximum=1000
        ),
    )


CONFIG = _load_config()


def _error_payload(code: str, message: str) -> str:
    return json.dumps({"error": {"code": code, "message": message}}, ensure_ascii=False)


def _validate_collection_name(collection_name: str) -> str:
    if not isinstance(collection_name, str):
        raise ValueError("collection_name must be a string")

    normalized = collection_name.strip()
    if not normalized:
        raise ValueError("collection_name cannot be empty")

    if not COLLECTION_NAME_REGEX.fullmatch(normalized):
        raise ValueError("collection_name contains invalid characters")

    return normalized


def _validate_container_name(container_name: str) -> str:
    if not isinstance(container_name, str):
        raise ValueError("container_name must be a string")

    normalized = container_name.strip()
    if not normalized:
        raise ValueError("container_name cannot be empty")

    if not CONTAINER_NAME_REGEX.fullmatch(normalized):
        raise ValueError("container_name contains invalid characters")

    return normalized


def _normalize_limit(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("limit must be an integer")

    return _clamp_int(limit, 1, CONFIG.max_limit)


def _validate_vector(query_vector: list[float]) -> list[float]:
    if not isinstance(query_vector, list):
        raise ValueError("query_vector must be a list of numbers")
    if not query_vector:
        raise ValueError("query_vector cannot be empty")
    if len(query_vector) > 4096:
        raise ValueError("query_vector is too large")

    normalized: list[float] = []
    for value in query_vector:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("query_vector must contain only numbers")
        normalized.append(float(value))

    return normalized


def _qdrant_request(
    method: str, path: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    url = f"{CONFIG.base_url}{path}"
    response: requests.Response | None = None
    try:
        response = requests.request(
            method=method,
            url=url,
            json=payload,
            timeout=CONFIG.timeout_seconds,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("Qdrant request timed out") from exc
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError("Unable to connect to Qdrant") from exc
    except requests.exceptions.HTTPError as exc:
        status_code = response.status_code if response is not None else "unknown"
        detail = (
            response.text.strip()[:1000]
            if response is not None and response.text
            else ""
        )
        raise RuntimeError(f"Qdrant HTTP error {status_code}: {detail}") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError("Unexpected Qdrant request error") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError("Invalid JSON response from Qdrant") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Unexpected response structure from Qdrant")

    return data


def _extract_container_info(container: Any) -> dict[str, Any]:
    attrs = container.attrs or {}
    image = attrs.get("Config", {}).get("Image")
    mounts_raw = attrs.get("Mounts", []) or []
    ports = attrs.get("NetworkSettings", {}).get("Ports", {}) or {}

    mounts: list[dict[str, Any]] = []
    for mount in mounts_raw:
        mounts.append(
            {
                "type": mount.get("Type"),
                "name": mount.get("Name"),
                "source": mount.get("Source"),
                "destination": mount.get("Destination"),
                "readWrite": mount.get("RW"),
            }
        )

    return {
        "id": container.short_id,
        "name": container.name,
        "status": container.status,
        "image": image,
        "ports": ports,
        "storagePathInContainer": "/qdrant/storage",
        "mounts": mounts,
    }


def _looks_like_qdrant_container(container: Any) -> bool:
    attrs = container.attrs or {}
    image = (attrs.get("Config", {}).get("Image") or "").lower()
    if "qdrant" in image:
        return True

    ports = attrs.get("NetworkSettings", {}).get("Ports", {}) or {}
    return "6333/tcp" in ports


def _build_filter(
    payload_filter_key: str | None, payload_filter_value: str | None
) -> dict[str, Any] | None:
    if not payload_filter_key and not payload_filter_value:
        return None

    if not payload_filter_key or not payload_filter_value:
        raise ValueError(
            "payload_filter_key and payload_filter_value must be provided together"
        )

    key = payload_filter_key.strip()
    value = payload_filter_value.strip()

    if not key or not value:
        raise ValueError("payload_filter_key and payload_filter_value cannot be empty")

    return {
        "must": [
            {
                "key": key,
                "match": {
                    "value": value,
                },
            }
        ]
    }


mcp = FastMCP("qdrant-custom")


def _get_docker_client():
    return docker.from_env(timeout=CONFIG.docker_timeout_seconds)


@mcp.tool()
def qdrant_health() -> str:
    """Verifica disponibilidade do Qdrant local."""
    try:
        response = _qdrant_request("GET", "/healthz")
        return json.dumps(
            {"baseUrl": CONFIG.base_url, "health": response},
            indent=2,
            ensure_ascii=False,
        )
    except Exception as exc:
        LOGGER.info("qdrant_health failed: %s", exc)
        return _error_payload("QDRANT_UNAVAILABLE", str(exc))


@mcp.tool()
def list_collections() -> str:
    """Lista as collections existentes no Qdrant."""
    try:
        response = _qdrant_request("GET", "/collections")
        collections = response.get("result", {}).get("collections", [])
        names = [
            item.get("name")
            for item in collections
            if isinstance(item, dict) and item.get("name")
        ]
        return json.dumps(
            {"baseUrl": CONFIG.base_url, "collections": names},
            indent=2,
            ensure_ascii=False,
        )
    except Exception as exc:
        LOGGER.info("list_collections failed: %s", exc)
        return _error_payload("QDRANT_COLLECTIONS_ERROR", str(exc))


@mcp.tool()
def get_collection_info(collection_name: str) -> str:
    """Retorna detalhes de configuração de uma collection."""
    try:
        safe_collection_name = _validate_collection_name(collection_name)
    except ValueError as exc:
        return _error_payload("INVALID_ARGUMENT", str(exc))

    try:
        response = _qdrant_request("GET", f"/collections/{safe_collection_name}")
        return json.dumps(response, indent=2, ensure_ascii=False)
    except Exception as exc:
        LOGGER.info("get_collection_info failed: %s", exc)
        return _error_payload("QDRANT_COLLECTION_INFO_ERROR", str(exc))


@mcp.tool()
def scroll_collection_points(
    collection_name: str,
    limit: int = 10,
    with_payload: bool = True,
    with_vector: bool = False,
    payload_filter_key: str | None = None,
    payload_filter_value: str | None = None,
) -> str:
    """Retorna uma amostra de pontos/chunks de uma collection para inspeção."""
    try:
        safe_collection_name = _validate_collection_name(collection_name)
        safe_limit = _normalize_limit(limit)
        qdrant_filter = _build_filter(payload_filter_key, payload_filter_value)
    except ValueError as exc:
        return _error_payload("INVALID_ARGUMENT", str(exc))

    request_payload: dict[str, Any] = {
        "limit": safe_limit,
        "with_payload": bool(with_payload),
        "with_vector": bool(with_vector),
    }
    if qdrant_filter is not None:
        request_payload["filter"] = qdrant_filter

    try:
        response = _qdrant_request(
            "POST",
            f"/collections/{safe_collection_name}/points/scroll",
            payload=request_payload,
        )
        return json.dumps(response, indent=2, ensure_ascii=False)
    except Exception as exc:
        LOGGER.info("scroll_collection_points failed: %s", exc)
        return _error_payload("QDRANT_SCROLL_ERROR", str(exc))


@mcp.tool()
def search_points_by_vector(
    collection_name: str,
    query_vector: list[float],
    limit: int = 5,
    with_payload: bool = True,
    with_vector: bool = False,
    score_threshold: float | None = None,
    payload_filter_key: str | None = None,
    payload_filter_value: str | None = None,
) -> str:
    """Executa busca vetorial em uma collection já indexada no Qdrant."""
    try:
        safe_collection_name = _validate_collection_name(collection_name)
        safe_vector = _validate_vector(query_vector)
        safe_limit = _normalize_limit(limit)
        qdrant_filter = _build_filter(payload_filter_key, payload_filter_value)

        if score_threshold is not None and not isinstance(
            score_threshold, (int, float)
        ):
            raise ValueError("score_threshold must be a number")
    except ValueError as exc:
        return _error_payload("INVALID_ARGUMENT", str(exc))

    request_payload: dict[str, Any] = {
        "vector": safe_vector,
        "limit": safe_limit,
        "with_payload": bool(with_payload),
        "with_vector": bool(with_vector),
    }
    if score_threshold is not None:
        request_payload["score_threshold"] = float(score_threshold)
    if qdrant_filter is not None:
        request_payload["filter"] = qdrant_filter

    try:
        response = _qdrant_request(
            "POST",
            f"/collections/{safe_collection_name}/points/search",
            payload=request_payload,
        )
        return json.dumps(response, indent=2, ensure_ascii=False)
    except Exception as exc:
        LOGGER.info("search_points_by_vector failed: %s", exc)
        return _error_payload("QDRANT_SEARCH_ERROR", str(exc))


@mcp.tool()
def inspect_qdrant_storage(container_name: str | None = None) -> str:
    """Inspeciona container Qdrant e mostra onde /qdrant/storage está persistido."""
    client = None
    try:
        client = _get_docker_client()

        if container_name:
            safe_container_name = _validate_container_name(container_name)
            container = client.containers.get(safe_container_name)
            container.reload()
            return json.dumps(
                _extract_container_info(container), indent=2, ensure_ascii=False
            )

        candidates = client.containers.list(all=True)
        qdrant_containers = []
        for candidate in candidates:
            candidate.reload()
            if _looks_like_qdrant_container(candidate):
                qdrant_containers.append(_extract_container_info(candidate))

        return json.dumps(
            {
                "hint": "Use docker run -v qdrant_storage:/qdrant/storage to persist index across container recreation",
                "containers": qdrant_containers,
            },
            indent=2,
            ensure_ascii=False,
        )
    except ValueError as exc:
        return _error_payload("INVALID_ARGUMENT", str(exc))
    except NotFound:
        return _error_payload("CONTAINER_NOT_FOUND", "Container not found")
    except (APIError, DockerException, OSError, TimeoutError):
        LOGGER.exception("Docker daemon unavailable while inspecting Qdrant storage")
        return _error_payload(
            "DOCKER_UNAVAILABLE", "Docker daemon unavailable or operation timed out"
        )
    except Exception:
        LOGGER.exception("Unexpected error while inspecting Qdrant storage")
        return _error_payload(
            "INTERNAL_ERROR", "Unexpected error while inspecting Qdrant storage"
        )
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                LOGGER.debug(
                    "Failed to close docker client after inspect_qdrant_storage",
                    exc_info=True,
                )


if __name__ == "__main__":
    mcp.run()
