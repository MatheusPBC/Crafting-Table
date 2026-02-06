# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp",
#     "boto3",
# ]
# ///

from __future__ import annotations

import boto3
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from botocore.config import Config as BotoConfig
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
    ProfileNotFound,
)
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=os.getenv("AWS_MCP_LOG_LEVEL", "INFO").upper())

MAX_ITEMS_HARD_CAP = 500
MAX_PAGES_HARD_CAP = 50
DEFAULT_MAX_ITEMS = 200
DEFAULT_MAX_PAGES = 10
DEFAULT_PAGE_SIZE = 50

FUNCTION_NAME_REGEX = re.compile(r"^[A-Za-z0-9:_./$-]{1,170}$")
AWS_REGION_REGEX = re.compile(r"^[a-z]{2}-[a-z]+-\d{1}$")
AWS_PROFILE_REGEX = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _read_int_env(name: str, default: int, min_value: int, max_value: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        parsed = int(raw_value)
    except ValueError:
        logger.warning("Invalid integer for %s. Using default=%s.", name, default)
        return default

    return max(min_value, min(parsed, max_value))


@dataclass(frozen=True)
class AwsMcpSettings:
    region: str | None
    profile: str | None
    max_items: int
    max_pages: int
    page_size: int


def _load_settings() -> AwsMcpSettings:
    raw_region = (
        os.getenv("AWS_MCP_REGION")
        or os.getenv("AWS_REGION")
        or os.getenv("AWS_DEFAULT_REGION")
        or None
    )
    raw_profile = os.getenv("AWS_MCP_PROFILE") or os.getenv("AWS_PROFILE") or None

    region = raw_region if raw_region and AWS_REGION_REGEX.fullmatch(raw_region) else None
    if raw_region and not region:
        logger.warning("Invalid AWS region in environment. Falling back to AWS default resolution.")

    profile = (
        raw_profile if raw_profile and AWS_PROFILE_REGEX.fullmatch(raw_profile) else None
    )
    if raw_profile and not profile:
        logger.warning("Invalid AWS profile format in environment. Ignoring configured profile.")

    return AwsMcpSettings(
        region=region,
        profile=profile,
        max_items=_read_int_env(
            name="AWS_MCP_MAX_ITEMS",
            default=DEFAULT_MAX_ITEMS,
            min_value=1,
            max_value=MAX_ITEMS_HARD_CAP,
        ),
        max_pages=_read_int_env(
            name="AWS_MCP_MAX_PAGES",
            default=DEFAULT_MAX_PAGES,
            min_value=1,
            max_value=MAX_PAGES_HARD_CAP,
        ),
        page_size=_read_int_env(
            name="AWS_MCP_PAGE_SIZE",
            default=DEFAULT_PAGE_SIZE,
            min_value=1,
            max_value=100,
        ),
    )


SETTINGS = _load_settings()

logger.info(
    "AWS MCP settings loaded (region=%s, profile=%s, max_items=%s, max_pages=%s, page_size=%s)",
    SETTINGS.region or "<aws-default>",
    "<configured>" if SETTINGS.profile else "<aws-default>",
    SETTINGS.max_items,
    SETTINGS.max_pages,
    SETTINGS.page_size,
)


def _build_session() -> boto3.session.Session:
    session_kwargs: dict[str, str] = {}
    if SETTINGS.profile:
        session_kwargs["profile_name"] = SETTINGS.profile
    if SETTINGS.region:
        session_kwargs["region_name"] = SETTINGS.region

    return boto3.session.Session(**session_kwargs)


SESSION: boto3.session.Session | None = None
SESSION_INIT_ERROR: Exception | None = None
try:
    SESSION = _build_session()
except Exception as exc:
    SESSION_INIT_ERROR = exc
    logger.warning("AWS session initialization failed: %s", exc.__class__.__name__)

BOTO_CLIENT_CONFIG = BotoConfig(
    retries={"max_attempts": 3, "mode": "standard"},
    connect_timeout=3,
    read_timeout=8,
)

ALLOWED_SERVICES = {"s3", "lambda", "dynamodb"}


def _client(service_name: str):
    if service_name not in ALLOWED_SERVICES:
        raise ValueError("Serviço AWS não permitido")
    if SESSION_INIT_ERROR is not None:
        raise SESSION_INIT_ERROR
    if SESSION is None:
        raise RuntimeError("AWS session indisponível")
    return SESSION.client(service_name, config=BOTO_CLIENT_CONFIG)


def _sanitize_exception(operation: str, prefix: str, exc: Exception) -> str:
    if isinstance(exc, (NoCredentialsError, PartialCredentialsError)):
        logger.warning("%s failed due to missing or partial AWS credentials.", operation)
        return f"{prefix}: credenciais AWS ausentes ou incompletas"

    if isinstance(exc, ProfileNotFound):
        logger.warning("%s failed due to AWS profile not found.", operation)
        return f"{prefix}: perfil AWS inválido ou inexistente"

    if isinstance(exc, ClientError):
        code = exc.response.get("Error", {}).get("Code", "ClientError")
        logger.warning("%s failed with AWS ClientError code=%s.", operation, code)
        return f"{prefix}: falha AWS ({code})"

    if isinstance(exc, BotoCoreError):
        logger.warning("%s failed with BotoCoreError=%s.", operation, exc.__class__.__name__)
        return f"{prefix}: falha de comunicação com AWS"

    logger.exception("%s failed with unexpected error.", operation)
    return f"{prefix}: erro interno inesperado"


def _validate_function_name(function_name: str) -> str:
    if not isinstance(function_name, str):
        raise ValueError("nome da função deve ser texto")

    normalized = function_name.strip()
    if not normalized:
        raise ValueError("nome da função é obrigatório")

    if not FUNCTION_NAME_REGEX.fullmatch(normalized):
        raise ValueError("nome da função inválido")

    return normalized

# Cria o servidor MCP
mcp = FastMCP("aws-custom")

def json_serial(obj: Any):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime)):
        return obj.isoformat()
    return str(obj)

@mcp.tool()
def s3_list_buckets() -> str:
    """Lista todos os buckets S3."""
    try:
        s3 = _client("s3")
        response = s3.list_buckets()
        buckets = [b["Name"] for b in response.get("Buckets", [])]
        return json.dumps(buckets[: SETTINGS.max_items], indent=2)
    except Exception as e:
        return _sanitize_exception("s3_list_buckets", "Erro AWS S3", e)

@mcp.tool()
def lambda_list_functions() -> str:
    """Lista TODAS as funções Lambda (paginado)."""
    try:
        client = _client("lambda")
        paginator = client.get_paginator("list_functions")

        all_funcs = []
        pages_seen = 0

        for page in paginator.paginate(PaginationConfig={"PageSize": SETTINGS.page_size}):
            pages_seen += 1
            if pages_seen > SETTINGS.max_pages:
                break

            for func in page.get("Functions", []):
                function_name = func.get("FunctionName")
                if isinstance(function_name, str):
                    all_funcs.append(function_name)
                if len(all_funcs) >= SETTINGS.max_items:
                    break

            if len(all_funcs) >= SETTINGS.max_items:
                break

        return json.dumps(all_funcs, indent=2)
    except Exception as e:
        return _sanitize_exception("lambda_list_functions", "Erro AWS Lambda", e)

@mcp.tool()
def lambda_get_function(function_name: str) -> str:
    """Retorna a configuração completa de uma função Lambda (incluindo variáveis de ambiente)."""
    try:
        validated_name = _validate_function_name(function_name)
    except ValueError as e:
        return f"Entrada inválida: {str(e)}"

    try:
        client = _client("lambda")
        response = client.get_function(FunctionName=validated_name)

        config = response.get("Configuration", {})

        result = {
            "FunctionName": config.get("FunctionName"),
            "Runtime": config.get("Runtime"),
            "Handler": config.get("Handler"),
            "LastModified": config.get("LastModified"),
            "Environment": config.get("Environment", {}),
            "MemorySize": config.get("MemorySize"),
            "Timeout": config.get("Timeout"),
            "Role": config.get("Role"),
        }

        return json.dumps(result, indent=2)
    except Exception as e:
        return _sanitize_exception(
            "lambda_get_function", "Erro ao buscar função Lambda", e
        )

@mcp.tool()
def dynamodb_list_tables() -> str:
    """Lista as tabelas do DynamoDB."""
    try:
        dyna = _client("dynamodb")

        table_names: list[str] = []
        pages_seen = 0
        last_evaluated_table_name = None

        while pages_seen < SETTINGS.max_pages and len(table_names) < SETTINGS.max_items:
            request = {"Limit": SETTINGS.page_size}
            if last_evaluated_table_name:
                request["ExclusiveStartTableName"] = last_evaluated_table_name

            response = dyna.list_tables(**request)
            pages_seen += 1

            current_names = response.get("TableNames", [])
            remaining = SETTINGS.max_items - len(table_names)
            table_names.extend(current_names[:remaining])

            last_evaluated_table_name = response.get("LastEvaluatedTableName")
            if not last_evaluated_table_name:
                break

        return json.dumps(table_names, indent=2)
    except Exception as e:
        return _sanitize_exception("dynamodb_list_tables", "Erro AWS DynamoDB", e)

if __name__ == "__main__":
    mcp.run()
