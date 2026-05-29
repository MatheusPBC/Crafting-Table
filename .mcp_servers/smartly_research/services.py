from __future__ import annotations

import asyncio
import os
import re
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any

from rlm import RLM

from .config import ServerConfig, get_config
from .prompts import BASE_SYSTEM_PROMPT, build_task_prompt

CONFIG = get_config()
if not os.getenv("COCOINDEX_CODE_ROOT_PATH"):
    os.environ["COCOINDEX_CODE_ROOT_PATH"] = str(CONFIG.workspace_root)
if not os.getenv("COCOINDEX_CODE_EMBEDDING_MODEL"):
    os.environ["COCOINDEX_CODE_EMBEDDING_MODEL"] = (
        "openai/text-embedding-3-small"
    )

if str(CONFIG.cocoindex_site_packages) not in sys.path:
    sys.path.insert(0, str(CONFIG.cocoindex_site_packages))

from cocoindex_code import client as cocoindex_client  # noqa: E402


_INDEX_LOCK = Lock()
_TEXT_FILE_ENCODING = "utf-8"

warnings.filterwarnings(
    "ignore",
    message=r".*runner_batch_fn_async.*was never awaited.*",
    category=RuntimeWarning,
)


class ResearchError(RuntimeError):
    """User-facing research error."""


@dataclass
class EvidenceItem:
    source: str
    repo: str
    path: str
    summary: str
    start_line: int | None = None
    end_line: int | None = None
    score: float | None = None
    query: str | None = None


@dataclass
class EvidenceCollector:
    items: list[EvidenceItem] = field(default_factory=list)
    _keys: set[tuple[str, str, int | None, int | None, str]] = field(
        default_factory=set
    )

    def add(self, item: EvidenceItem) -> None:
        key = (item.source, item.path, item.start_line, item.end_line, item.summary)
        if key in self._keys:
            return
        self._keys.add(key)
        self.items.append(item)

    def to_payload(self, limit: int = 20) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.items[:limit]]


def _run_async(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()


def _ensure_workspace_root(config: ServerConfig) -> Path:
    if not config.workspace_root.exists():
        raise ResearchError(f"Workspace root não encontrado: {config.workspace_root}")
    return config.workspace_root


def _normalize_repo_scopes(repo_scope: str | None, config: ServerConfig) -> list[str]:
    raw_value = repo_scope or config.default_repo_scope
    scopes = [
        segment.strip().strip("/")
        for segment in raw_value.split(",")
        if segment.strip()
    ]
    if not scopes:
        return [config.default_repo_scope]
    return scopes


def _resolve_repo_paths(repo_scope: str | None, config: ServerConfig) -> list[Path]:
    root = _ensure_workspace_root(config)
    repo_paths: list[Path] = []
    for scope in _normalize_repo_scopes(repo_scope, config):
        if scope in {".", root.name}:
            candidate = root
        else:
            candidate = (root / scope).resolve()
        if not candidate.exists():
            raise ResearchError(f"Repo scope não encontrado: {scope}")
        if root not in candidate.parents and candidate != root:
            raise ResearchError(f"Repo scope fora do workspace: {scope}")
        repo_paths.append(candidate)
    return repo_paths


def _path_to_repo(path: Path, repo_paths: list[Path]) -> str:
    for repo_path in repo_paths:
        try:
            path.relative_to(repo_path)
            return repo_path.name
        except ValueError:
            continue
    return path.parts[0] if path.parts else "workspace"


def _is_ignored(path: Path, config: ServerConfig) -> bool:
    return any(part in config.ignored_segments for part in path.parts)


def _is_allowed_file(path: Path, config: ServerConfig) -> bool:
    if not path.is_file():
        return False
    if _is_ignored(path, config):
        return False
    return path.suffix.lower() in config.allowed_extensions


def _resolve_user_path(raw_path: str, config: ServerConfig) -> Path:
    normalized = raw_path.strip()
    if not normalized:
        raise ResearchError("path não pode ser vazio")

    candidate = (config.workspace_root / normalized).resolve()
    if (
        config.workspace_root not in candidate.parents
        and candidate != config.workspace_root
    ):
        raise ResearchError("path fora do workspace permitido")
    if not candidate.exists():
        raise ResearchError(f"Arquivo não encontrado: {normalized}")
    return candidate


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(
            encoding=_TEXT_FILE_ENCODING, errors="replace"
        ).splitlines()
    except OSError as exc:
        raise ResearchError(f"Falha ao ler arquivo {path}: {exc}") from exc


def _snippet_from_lines(
    lines: list[str], start_line: int, end_line: int, max_chars: int
) -> str:
    safe_start = max(start_line, 1)
    safe_end = max(end_line, safe_start)
    excerpt = lines[safe_start - 1 : safe_end]
    content = "\n".join(excerpt).strip()
    if len(content) <= max_chars:
        return content
    return content[: max_chars - 3].rstrip() + "..."


def _relative_path(path: Path, config: ServerConfig) -> str:
    return str(path.resolve().relative_to(config.workspace_root))


def _refresh_cocoindex() -> None:
    with _INDEX_LOCK:
        response = cocoindex_client.index(str(CONFIG.workspace_root))
        if not response.success:
            raise ResearchError(response.message or "Falha ao atualizar índice CocoIndex")


class ResearchToolkit:
    def __init__(
        self, collector: EvidenceCollector, config: ServerConfig, repo_scope: str | None
    ):
        self.collector = collector
        self.config = config
        self.repo_paths = _resolve_repo_paths(repo_scope, config)

    def semantic_search(
        self,
        query: str,
        repo_scope: str | None = None,
        limit: int | None = None,
        refresh_index: bool = False,
    ) -> list[dict[str, Any]]:
        if not isinstance(query, str) or not query.strip():
            raise ResearchError("query deve ser uma string não vazia")

        if refresh_index:
            _refresh_cocoindex()

        safe_limit = max(
            1, min(limit or self.config.semantic_limit, self.config.semantic_limit)
        )
        response = cocoindex_client.search(
            str(self.config.workspace_root),
            query=query.strip(),
            limit=safe_limit,
            offset=0,
        )
        if not response.success:
            raise ResearchError(response.message or "Falha na busca semântica CocoIndex")

        active_repo_paths = (
            _resolve_repo_paths(repo_scope, self.config)
            if repo_scope
            else self.repo_paths
        )

        payload: list[dict[str, Any]] = []
        for result in response.results:
            file_path = (self.config.workspace_root / result.file_path).resolve()
            if not any(
                repo_path == file_path or repo_path in file_path.parents
                for repo_path in active_repo_paths
            ):
                continue

            item = EvidenceItem(
                source="semantic_search",
                repo=_path_to_repo(file_path, active_repo_paths),
                path=str(file_path.relative_to(self.config.workspace_root)),
                summary=result.content[:400],
                start_line=result.start_line,
                end_line=result.end_line,
                score=round(float(result.score), 4),
                query=query.strip(),
            )
            self.collector.add(item)
            payload.append(asdict(item))

        return payload

    def read_file_excerpt(
        self,
        path: str,
        start_line: int = 1,
        end_line: int | None = None,
    ) -> dict[str, Any]:
        resolved_path = _resolve_user_path(path, self.config)
        if not any(
            repo_path == resolved_path or repo_path in resolved_path.parents
            for repo_path in self.repo_paths
        ):
            raise ResearchError("Arquivo fora do repo_scope permitido")
        if not _is_allowed_file(resolved_path, self.config):
            raise ResearchError(f"Arquivo fora da allowlist: {path}")

        lines = _read_lines(resolved_path)
        safe_start = max(1, int(start_line))
        max_end = min(len(lines), safe_start + self.config.read_max_lines - 1)
        safe_end = (
            max_end
            if end_line is None
            else min(max_end, max(safe_start, int(end_line)))
        )
        snippet = _snippet_from_lines(
            lines, safe_start, safe_end, self.config.read_max_chars
        )
        item = EvidenceItem(
            source="read_file_excerpt",
            repo=_path_to_repo(resolved_path, self.repo_paths),
            path=_relative_path(resolved_path, self.config),
            summary=snippet,
            start_line=safe_start,
            end_line=safe_end,
        )
        self.collector.add(item)
        return asdict(item)

    def search_exact(
        self,
        pattern: str,
        repo_scope: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        if not isinstance(pattern, str) or not pattern.strip():
            raise ResearchError("pattern deve ser uma string não vazia")

        active_repo_paths = (
            _resolve_repo_paths(repo_scope, self.config)
            if repo_scope
            else self.repo_paths
        )
        compiled = re.compile(re.escape(pattern.strip()), re.IGNORECASE)
        matches: list[dict[str, Any]] = []
        safe_limit = max(
            1, min(limit or self.config.exact_limit, self.config.exact_limit)
        )

        for repo_path in active_repo_paths:
            for file_path in repo_path.rglob("*"):
                if len(matches) >= safe_limit:
                    return matches
                if not _is_allowed_file(file_path, self.config):
                    continue
                try:
                    lines = _read_lines(file_path)
                except ResearchError:
                    continue
                for line_number, line in enumerate(lines, start=1):
                    if compiled.search(line) is None:
                        continue
                    snippet = line.strip()[: self.config.read_max_chars]
                    item = EvidenceItem(
                        source="search_exact",
                        repo=repo_path.name,
                        path=_relative_path(file_path, self.config),
                        summary=snippet,
                        start_line=line_number,
                        end_line=line_number,
                        query=pattern.strip(),
                    )
                    self.collector.add(item)
                    matches.append(asdict(item))
                    if len(matches) >= safe_limit:
                        return matches

        return matches

    def list_paths(
        self,
        repo_scope: str | None = None,
        glob_pattern: str = "**/*",
        limit: int | None = None,
    ) -> list[str]:
        active_repo_paths = (
            _resolve_repo_paths(repo_scope, self.config)
            if repo_scope
            else self.repo_paths
        )
        safe_limit = max(
            1, min(limit or self.config.list_limit, self.config.list_limit)
        )
        payload: list[str] = []
        for repo_path in active_repo_paths:
            for file_path in repo_path.glob(glob_pattern):
                if len(payload) >= safe_limit:
                    return payload
                if file_path.is_dir() or _is_ignored(file_path, self.config):
                    continue
                payload.append(_relative_path(file_path, self.config))
        return payload


def _build_custom_tools(toolkit: ResearchToolkit) -> dict[str, dict[str, Any]]:
    return {
        "semantic_search": {
            "tool": toolkit.semantic_search,
            "description": "Busca semântica principal no workspace usando CocoIndex. Use primeiro para descobrir contexto relevante.",
        },
        "read_file_excerpt": {
            "tool": toolkit.read_file_excerpt,
            "description": "Lê um trecho real de arquivo para confirmar afirmações importantes com evidência local.",
        },
        "search_exact": {
            "tool": toolkit.search_exact,
            "description": "Busca textual exata/case-insensitive em arquivos permitidos do workspace. Útil para nomes literais, símbolos e strings.",
        },
        "list_paths": {
            "tool": toolkit.list_paths,
            "description": "Lista paths do escopo local quando precisar descobrir estrutura, testes ou diretórios relevantes.",
        },
    }


def _build_fallback_answer(question: str, collector: EvidenceCollector) -> str:
    evidence = collector.to_payload(limit=8)
    if not evidence:
        return (
            "Não consegui concluir a análise com evidência suficiente. "
            f"Pergunta original: {question}"
        )

    bullet_lines = []
    for item in evidence[:5]:
        location = item["path"]
        if item.get("start_line"):
            location += f":{item['start_line']}"
        bullet_lines.append(f"- {location}")

    bullets = "\n".join(bullet_lines)
    return (
        "O RLM falhou e devolvi um resumo mínimo baseado em evidência coletada.\n"
        f"Pergunta: {question}\n"
        f"Arquivos mais relevantes:\n{bullets}"
    )


def _collect_top_evidence_excerpts(toolkit: ResearchToolkit, limit: int = 2) -> None:
    semantic_items = [
        item for item in toolkit.collector.items if item.source == "semantic_search"
    ]
    ranked_items = sorted(
        semantic_items,
        key=lambda item: item.score or 0.0,
        reverse=True,
    )

    for item in ranked_items[:limit]:
        if item.start_line is None:
            continue
        end_line = item.end_line or item.start_line
        excerpt_start = max(1, item.start_line - 6)
        excerpt_end = max(excerpt_start, min(end_line + 6, excerpt_start + 30))
        try:
            toolkit.read_file_excerpt(
                item.path, start_line=excerpt_start, end_line=excerpt_end
            )
        except ResearchError:
            continue


def _answer_needs_repair(answer: str, collector: EvidenceCollector) -> bool:
    if not collector.items:
        return False

    normalized = answer.lower()
    if (
        "não consegui" in normalized
        or "não foi possível" in normalized
        or "não há evid" in normalized
        or "falta de dados" in normalized
    ):
        return True

    bad_signals = (
        "não consegui realizar buscas",
        "não tenho evidências concretas",
        "não há arquivos ou trechos disponíveis",
        "não foi possível obter informações específicas",
        "não consegui acessar",
        "não foi possível realizar a pesquisa",
        "nenhum arquivo ou trecho relevante foi identificado",
        "nenhuma evidência",
        "buscas semânticas com sucesso",
        "tentativas de pesquisa na base de código retornaram vazias",
    )
    return any(signal in normalized for signal in bad_signals)


def _build_evidence_summary(question: str, collector: EvidenceCollector) -> str:
    preferred_sources = {
        "read_file_excerpt": 0,
        "semantic_search": 1,
        "search_exact": 2,
    }
    items = sorted(
        collector.items,
        key=lambda item: (
            preferred_sources.get(item.source, 9),
            -(item.score or 0.0),
            item.path,
        ),
    )[:5]
    if not items:
        return _build_fallback_answer(question, collector)

    findings = []
    for item in items:
        location = item.path
        if item.start_line is not None:
            location += f":{item.start_line}"
        source_label = {
            "read_file_excerpt": "trecho",
            "semantic_search": "busca semântica",
            "search_exact": "busca exata",
        }.get(item.source, item.source)
        snippet = item.summary[:220].replace(chr(10), " ")
        findings.append(f"- [{source_label}] {location} — {snippet}")

    joined = "\n".join(findings)
    return (
        f"1. Resumo curto: encontrei evidências concretas relacionadas à pergunta '{question}'.\n\n"
        "2. Principais achados:\n"
        f"{joined}\n\n"
        "3. Interpretação: priorize os trechos marcados como [trecho]; eles já representam leitura direta dos pontos mais promissores.\n"
        "4. Confiança: média.\n"
        "5. Lacunas de validação: ainda vale expandir a leitura dos handlers e helpers citados para consolidar o fluxo completo."
    )


def run_research_tool(
    *,
    tool_name: str,
    user_input: str,
    repo_scope: str | None,
    mode: str,
    limit: int,
) -> dict[str, Any]:
    config = get_config()
    collector = EvidenceCollector()
    toolkit = ResearchToolkit(collector=collector, config=config, repo_scope=repo_scope)

    warmup_query = user_input if len(user_input) <= 200 else user_input[:200]
    try:
        toolkit.semantic_search(
            warmup_query,
            limit=min(limit, config.semantic_limit),
            refresh_index=False,
        )
        _collect_top_evidence_excerpts(toolkit)
    except Exception:
        pass

    if config.openrouter_api_key is None:
        raise ResearchError("OPENROUTER_API_KEY não configurada no ambiente")

    prompt = build_task_prompt(
        tool_name=tool_name,
        user_input=user_input,
        repo_scope=repo_scope or config.default_repo_scope,
        mode=mode,
        limit=limit,
    )

    rlm = RLM(
        backend="openrouter",
        backend_kwargs={
            "api_key": config.openrouter_api_key,
            "model_name": config.rlm_model,
        },
        environment="local",
        max_depth=config.rlm_max_depth if mode == "deep" else 1,
        max_iterations=config.rlm_max_iterations,
        max_timeout=float(config.rlm_max_timeout_seconds),
        compaction=True,
        custom_system_prompt=BASE_SYSTEM_PROMPT,
        custom_tools=_build_custom_tools(toolkit),
        verbose=False,
    )

    warnings: list[str] = []
    answer: str
    try:
        completion = rlm.completion(prompt)
        answer = completion.response.strip()
    except Exception as exc:
        warnings.append(f"RLM fallback ativado: {exc}")
        answer = _build_fallback_answer(user_input, collector)

    if _answer_needs_repair(answer, collector):
        warnings.append("Resposta do RLM foi reparada com base na evidência coletada.")
        answer = _build_evidence_summary(user_input, collector)

    if not collector.items:
        warnings.append("Nenhuma evidência concreta foi registrada durante a execução.")

    return {
        "tool": tool_name,
        "mode": mode,
        "repoScope": repo_scope or config.default_repo_scope,
        "model": config.rlm_model,
        "answer": answer,
        "evidence": collector.to_payload(),
        "warnings": warnings,
    }
