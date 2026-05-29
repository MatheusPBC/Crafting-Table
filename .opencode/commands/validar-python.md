---
description: Preparar validação local de Python com pytest, Bandit, Pylint e Radon
---

Prepare a validação Python para `$ARGUMENTS`.

Regras obrigatórias:

- Responda em português.
- Não execute comandos sem confirmação explícita do usuário.
- Antes de sugerir comandos, identifique se `$ARGUMENTS` é arquivo, pasta, handler ou teste específico.
- Use comandos locais do projeto quando aplicável.

Sugira a sequência mínima apropriada:

- Testes: `pytest` ou `pytest path/to/test_file.py::test_case`.
- Segurança: `.venv/bin/bandit -q -ll -ii path/to/file.py`.
- Estrutura: `PYTHONPATH=.:src .venv/bin/pylint --score=n --reports=n --disable=all --enable="unused-import,unused-variable,redefined-outer-name,dangerous-default-value,broad-exception-caught,broad-exception-raised,too-many-arguments,too-many-locals,too-many-branches,too-many-statements,too-many-return-statements,too-many-nested-blocks,too-many-boolean-expressions,consider-using-with" path/to/file.py`.
- Complexidade: `.venv/bin/radon cc -s -n C path/to/file.py && .venv/bin/radon mi -s -n B path/to/file.py`.

Entregue:

- Comandos exatos para aprovação.
- O que cada comando valida.
- Ordem recomendada.
