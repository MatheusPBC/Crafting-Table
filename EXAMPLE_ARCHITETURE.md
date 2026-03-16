# EXAMPLE_ARCHITETURE.md

Guia de referencia para a arquitetura agentica usada neste repositório (`_dest_Crafting-Table`) e para reaplicacao em outros projetos.

## 1) Objetivo da arquitetura

Esta base separa **plataforma de agentes** do **dominio de produto**.

- A plataforma define como os agentes pensam, roteiam, validam e executam.
- O produto define regras de negocio, codigo da aplicacao e dados.
- O resultado e um pacote reutilizavel com baixo acoplamento ao dominio.

## 2) Mapa de pastas (visao macro)

```text
repo/
  .agent/                 # runtime principal dos agentes (fonte operacional)
  .kilocode/              # camada espelhada para compatibilidade de runtime
  .mcp_servers/           # MCP servers customizados (MySQL, AWS, Docker)
  .github/workflows/      # enforcement no CI
  MCP_CONFIG.md           # setup operacional de MCP
  README.md               # onboarding da plataforma
```

## 3) Camadas e responsabilidade

### 3.1 `.agent/` (fonte operacional principal)

- `ARCHITECTURE.md`: mapa de agentes, skills, workflows e protocolos.
- `rules/GEMINI.md`: regras globais de comportamento, roteamento e qualidade.
- `agents/`: personas especialistas (`backend-specialist`, `frontend-specialist`, etc.).
- `skills/`: conhecimento modular por tema (`clean-code`, `api-patterns`, etc.).
- `workflows/`: comandos slash (`/create`, `/plan`, `/debug`, etc.).
- `scripts/`: gates executaveis para validacao local e CI.

### 3.2 `.kilocode/` (espelho funcional)

- Replica artefatos criticos de `.agent` para ambientes/ferramentas que usam esse padrao.
- Contem `rules/`, `skills/`, `workflows/` e `ARCHITECTURE.md`.
- E validada por anti-drift para evitar divergencia silenciosa.

### 3.3 `.mcp_servers/` (integrações externas)

- `mysql_mcp_server.py`: consultas controladas ao MySQL.
- `aws_mcp_server.py`: leitura/listagem de recursos AWS permitidos.
- `docker_mcp_server.py`: observabilidade operacional de containers.

### 3.4 `.github/workflows/` (enforcement continuo)

- `platform-gates.yml`: bloqueia regressao estrutural em PR/push.

## 4) Arquivos-chave e para que servem

| Arquivo | Papel na arquitetura | Reutilizacao em outro repo |
| --- | --- | --- |
| `README.md` | onboarding, escopo e comandos essenciais | copiar e ajustar texto de contexto |
| `MCP_CONFIG.md` | instrucoes de setup de MCP no ambiente local | manter e adaptar credenciais/hosts |
| `.agent/ARCHITECTURE.md` | mapa tecnico da plataforma agentica | manter como referencia central |
| `.agent/rules/GEMINI.md` | policy global de execucao dos agentes | clonar e ajustar politicas internas |
| `.agent/scripts/checklist.py` | verificacao incremental | manter como gate local |
| `.agent/scripts/verify_all.py` | verificacao abrangente | manter como gate pre-release |
| `.agent/scripts/check_agent_kilocode_drift.py` | detecta drift entre `.agent` e `.kilocode` | obrigatorio se houver espelho |
| `.agent/scripts/check_*_mcp_hardening.py` | valida invariantes de seguranca dos MCPs | obrigatorio se MCP customizado |
| `.kilocode/rules/GEMINI.md` | espelho de regras criticas | manter sincronizado com `.agent` |

## 5) Conceitos estruturais (o que precisa existir)

### 5.1 Regra de precedencia

A plataforma funciona com camadas de autoridade:

1. Regra global (`GEMINI.md`)
2. Regras de agente (arquivo em `agents/`)
3. Regras de skill (`skills/*/SKILL.md`)

Isso evita conflito de instrucao e torna decisao rastreavel.

### 5.2 Skill loading modular

Fluxo esperado:

1. Classificar o pedido.
2. Selecionar agente especialista.
3. Ler `SKILL.md` da skill relevante.
4. Ler apenas secoes necessarias.
5. Executar com checklist/gates.

Esse fluxo reduz custo de contexto e melhora consistencia.

### 5.3 Espelhamento controlado

`.agent` e `.kilocode` nao sao duplicacao acidental; sao estrategia de compatibilidade.

- Quando muda um artefato critico, o espelho tambem precisa mudar.
- O script de anti-drift garante que a paridade seja verificavel.

### 5.4 Guardrails de plataforma

A fundacao usa gates estaticos para impedir erosao de seguranca/estrutura:

- anti-drift de regras/skills criticas
- hardening de MCP MySQL
- hardening de MCP AWS
- hardening de MCP Docker

## 6) Fluxo operacional padrao

### Desenvolvimento local

```bash
python .agent/scripts/checklist.py . --platform-only
```

### Verificacao abrangente local

```bash
python .agent/scripts/verify_all.py . --platform-only
```

### Pipeline CI

- PR/push aciona `.github/workflows/platform-gates.yml`.
- Se qualquer gate critico falhar, a mudanca nao deve ser promovida.

## 7) Como reaplicar em outro repositorio (playbook)

### Passo 1 - bootstrap da estrutura

Copiar para o novo repo:

- `.agent/`
- `.kilocode/`
- `.mcp_servers/`
- `.github/workflows/platform-gates.yml`
- `MCP_CONFIG.md`
- `README.md` (adaptado)

### Passo 2 - ajustar identidade do projeto

- Atualizar `README.md` com objetivo do novo produto.
- Ajustar skills/agents necessarios ao dominio.
- Manter regras globais e protocolo de precedencia.

### Passo 3 - ajustar MCPs e hardening

- Adaptar endpoints, escopo e credenciais dos MCP servers.
- Revisar scripts `check_*_mcp_hardening.py` para os novos invariantes.

### Passo 4 - validar integridade da base

Executar:

```bash
python .agent/scripts/check_agent_kilocode_drift.py
python .agent/scripts/checklist.py . --platform-only
```

### Passo 5 - ativar CI como gate obrigatorio

- Garantir execucao de `platform-gates.yml` em PR e push.
- Tratar falhas como bloqueio, nao como aviso.

## 8) Contratos e extensoes pessoais (recomendado)

Para manter regras pessoais sem poluir o repo de produto:

- Definir contratos em `~/.kilocode/rules/` (escopo pessoal/global).
- Referenciar esses contratos em `AGENTS.md`/`GEMINI.md` quando necessario.
- Evitar duplicar texto: usar ponteiros para a fonte oficial.

## 9) Checklist minimo de qualidade da arquitetura agentica

- Existe fonte principal de regras (`.agent/rules/GEMINI.md`).
- Existe espelho `.kilocode` com validacao de drift.
- MCP servers possuem hardening verificavel por script.
- Existe workflow CI de platform gates.
- README explica objetivo, escopo e comandos de validacao.
- Arquitetura pode ser portada sem depender de dominio especifico.

## 10) Limites deste template

Este template nao define:

- modelo de dominio da aplicacao
- schema de banco de negocio
- contratos de API do produto
- fluxo de deploy do produto final

Ele define somente a **plataforma agentica** para governanca, execucao e qualidade.
