# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp",
#     "mysql-connector-python",
# ]
# ///

from mcp.server.fastmcp import FastMCP
import mysql.connector
import json
import logging
import os
import re
from typing import Any

# Cria o servidor MCP
mcp = FastMCP("mysql-custom")

logger = logging.getLogger(__name__)

_SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {var_name}")
    return value


def _build_db_config() -> dict[str, Any]:
    # Defaults não sensíveis e voltados para ambiente local.
    # Segredos (senha) devem sempre vir do ambiente.
    try:
        port = int(os.getenv("MYSQL_PORT", "3307"))
    except ValueError as exc:
        raise RuntimeError("MYSQL_PORT inválida: deve ser inteiro") from exc

    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": port,
        "user": os.getenv("MYSQL_USER", "root"),
        "password": _require_env("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE", "smartlybrasil_dev"),
    }


DB_CONFIG = _build_db_config()


def _is_safe_identifier(identifier: str) -> bool:
    return bool(_SAFE_IDENTIFIER_RE.fullmatch(identifier))


def _quote_identifier(identifier: str) -> str:
    if not _is_safe_identifier(identifier):
        raise ValueError("Identificador inválido. Use apenas letras, números e underscore.")
    return f"`{identifier}`"


def _sanitize_error_message(operation: str, exc: Exception) -> str:
    logger.exception("Falha em operação MySQL MCP: %s", operation)
    if isinstance(exc, (RuntimeError, ValueError)):
        return f"Erro de validação/configuração: {str(exc)}"
    return "Erro operacional no banco de dados. Consulte logs do servidor."

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

@mcp.tool()
def list_tables() -> str:
    """Lista todas as tabelas do banco de dados conectado."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        return json.dumps(tables, indent=2)
    except Exception as e:
        return _sanitize_error_message("list_tables", e)
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()

@mcp.tool()
def describe_table(table_name: str) -> str:
    """Mostra a estrutura de uma tabela específica."""
    conn = None
    cursor = None
    try:
        safe_table_name = _quote_identifier(table_name)

        conn = get_connection()

        # Allowlist dinâmica para garantir que apenas tabelas existentes sejam descritas.
        allowlist_cursor = conn.cursor()
        allowlist_cursor.execute("SHOW TABLES")
        allowed_tables = {row[0] for row in allowlist_cursor.fetchall()}
        allowlist_cursor.close()

        if table_name not in allowed_tables:
            raise ValueError("Tabela não encontrada no schema configurado.")

        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"DESCRIBE {safe_table_name}")
        schema = cursor.fetchall()
        return json.dumps(schema, indent=2, default=str) # default=str para types de data
    except Exception as e:
        return _sanitize_error_message("describe_table", e)
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()

@mcp.tool()
def run_query(query: str) -> str:
    """Executa uma query SELECT segura (readonly)."""
    conn = None
    cursor = None
    if not query.strip().upper().startswith("SELECT"):
        return "Erro: Apenas queries SELECT são permitidas por segurança."
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        return json.dumps(results, indent=2, default=str)
    except Exception as e:
        return _sanitize_error_message("run_query", e)
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    mcp.run()
