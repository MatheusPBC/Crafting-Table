---
description: Guiar alteração segura em Lambda Python do backend Smartly
---

Prepare a alteração da Lambda indicada em `$ARGUMENTS`.

Regras obrigatórias:

- Responda em português.
- Trate como backend Python/AWS Lambda.
- Antes de editar, pesquise o fluxo com `smartly-research` e confirme arquivos relevantes.
- Respeite os padrões do projeto: `@db_handler`, `@exception_handler`, stage normalizado, SQL parametrizado com `%s`, respostas `{ "status": <int>, "message": ... }`, logs com `logging`.
- Não duplicar helpers já existentes na layer.
- Não executar comandos sem confirmação explícita do usuário.
- Se a mudança for complexa ou ambígua, faça perguntas de escopo antes de implementar.

Checklist de saída:

- Lambda e handler alvo.
- Contrato de entrada/saída atual.
- Mudança desejada.
- Arquivos que provavelmente precisam mudar.
- Testes existentes ou lacunas.
- Comandos de validação recomendados para o arquivo alterado: `pytest`, `bandit`, `pylint`, `radon`.
