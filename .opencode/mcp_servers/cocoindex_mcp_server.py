from __future__ import annotations

import os

EXTRA_EXCLUDED_PATTERNS = [
    "**/cities1000.txt",
    "**/src/layers/rds-proxy-layer/python/**",
    "**/function/deepdiff/**",
]


def _apply_runtime_overrides() -> None:
    if not os.getenv("COCOINDEX_CODE_ROOT_PATH"):
        os.environ["COCOINDEX_CODE_ROOT_PATH"] = (
            "/home/matheus/Documentos/vscode/baseDev/smartly.backend_smartly-dev"
        )
    if not os.getenv("COCOINDEX_CODE_EMBEDDING_MODEL"):
        os.environ["COCOINDEX_CODE_EMBEDDING_MODEL"] = (
            "openai/text-embedding-3-small"
        )
    if not os.getenv("COCOINDEX_CODE_EXCLUDED_PATTERNS"):
        import json

        os.environ["COCOINDEX_CODE_EXCLUDED_PATTERNS"] = json.dumps(
            EXTRA_EXCLUDED_PATTERNS
        )


def main() -> None:
    _apply_runtime_overrides()

    from cocoindex_code.server import main as server_main

    server_main()


if __name__ == "__main__":
    main()
