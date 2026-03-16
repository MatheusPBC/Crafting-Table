# Crafting-Table

Base reutilizável de arquitetura de plataforma para projetos com agentes, skills, MCP servers e gates de validação automatizados.

## Objetivo do platform architecture pack

Este repositório existe para servir como **fundação técnica reaproveitável** em novos projetos.

O foco é padronizar:

- governança de agentes e skills;
- execução segura de servidores MCP;
- validações de integridade (anti-drift) e hardening;
- enforcement contínuo via CI.

> Escopo intencional: este pacote não contém regras de domínio de produto; ele entrega somente a infraestrutura de plataforma.

## Arquitetura de referencia (reaplicavel)

Documento detalhado: `EXAMPLE_ARCHITETURE.md`.


## Componentes base adicionados

### `.agent/`

Camada principal de operação dos agentes.

Inclui:

- estrutura de skills e regras;
- scripts de validação centralizados em `.agent/scripts/`;
- gates de plataforma usados localmente e no CI.

Scripts principais:

- `check_agent_kilocode_drift.py`: compara espelhamento crítico entre `.agent` e `.kilocode`.
- `check_mysql_mcp_hardening.py`: valida invariantes estáticos de hardening do MCP MySQL.
- `check_aws_mcp_hardening.py`: valida invariantes estáticos de hardening do MCP AWS.
- `check_docker_mcp_hardening.py`: valida invariantes estáticos de hardening do MCP Docker.
- `checklist.py`: execução incremental de checks (inclui modo `--platform-only`).
- `verify_all.py`: suíte completa de verificação (inclui modo `--platform-only`).

### `.kilocode/`

Camada espelhada para compatibilidade operacional com runtimes que dependem dessa convenção.

Função prática:

- manter paridade de artefatos críticos com `.agent`;
- reduzir risco de inconsistência entre ambientes/ferramentas;
- permitir validação automatizada de drift.

### `.mcp_servers/`

Implementações dos servidores MCP customizados do template:

- `mysql_mcp_server.py`
- `aws_mcp_server.py`
- `docker_mcp_server.py`

Esses servidores já estão preparados para validação por gates estáticos (hardening) executados pelos scripts em `.agent/scripts/`.

### `.github/workflows/`

Automação CI de enforcement de plataforma.

Workflow presente:

- `platform-gates.yml`: executa validação agregada de plataforma em `pull_request`, `push` para `main`/`dev` e execução manual (`workflow_dispatch`).

### `MCP_CONFIG.md`

Guia operacional para configuração de MCPs no ambiente de desenvolvimento.

## Fluxo recomendado para uso em novos projetos

1. **Criar seu novo repositório** usando este conteúdo como base.
2. **Personalizar regras e skills** para o contexto do novo projeto.
3. **Configurar MCPs locais** conforme o guia em `MCP_CONFIG.md`.
4. **Executar gates de plataforma localmente** antes de abrir PR.
5. **Abrir PR** e deixar o workflow de platform gates validar no CI.
6. **Expandir para validações completas** (`verify_all`) quando o projeto já tiver aplicação/URL de teste.

## Pré-requisitos

- Git instalado.
- Python 3.12 (alinhado ao runtime do workflow CI atual).
- Ambiente com permissão para executar GitHub Actions no repositório alvo.
- Dependências específicas dos MCPs conforme seu cenário de uso (ex.: credenciais/CLI e serviços locais).

## Comandos essenciais (setup e validação)

### 1) Validar apenas a fundação de plataforma (recomendado no início)

```bash
python .agent/scripts/checklist.py . --platform-only
```

ou

```bash
python .agent/scripts/verify_all.py . --platform-only
```

### 2) Executar suíte completa (quando existir app/URL para checks dependentes)

```bash
python .agent/scripts/verify_all.py . --url http://localhost:3000
```

## O que o CI valida hoje

No estado atual deste repositório, o pipeline de plataforma valida:

- anti-drift entre `.agent` e `.kilocode`;
- hardening estático do MCP MySQL;
- hardening estático do MCP AWS;
- hardening estático do MCP Docker.

## Diretrizes de manutenção

Para manter a base saudável ao longo do tempo:

- qualquer ajuste estrutural em regras/skills espelhados deve considerar `.agent` e `.kilocode`;
- mudanças em servidores MCP devem ser acompanhadas pelos respectivos gates de hardening;
- toda evolução de governança deve passar por validação local (`--platform-only`) antes do push;
- mantenha este README atualizado sempre que o escopo dos componentes base mudar.

## Estado atual do repositório

Este README descreve a branch com pacote de arquitetura contendo:

- `.agent/`
- `.kilocode/`
- `.mcp_servers/`
- `.github/workflows/platform-gates.yml`
- `MCP_CONFIG.md`

Pronto para reutilização como fundação técnica em novos projetos.

## Migração de Kilo CLI para OpenCode CLI

Para projetos que utilizam Kilo CLI e desejam migrar para OpenCode CLI, consulte:

- **`MIGRATION_GUIDE.md`** - Guia completo de migração incluindo:
  - Configuração global (`~/.config/opencode/`)
  - Skills, agentes e comandos customizados
  - MCPs locais e remotos
  - Custom tools (aifns)
  - Migração de sessões
  - Fixes e troubleshooting
