---
name: obsidian-documentation
description: Use when saving, searching, organizing, or updating personal notes, daily logs, project docs, handoffs, decisions, or Second Brain knowledge in the Obsidian Docs vault via MCP.
tags: [documentation, obsidian, mcp, knowledge-base]
---

# Obsidian Documentation & MCP Skill

Use esta skill sempre que o usuário pedir para salvar contexto, procurar anotações, registrar daily logs, criar handoffs, organizar projetos, promover aprendizados ou manter a vault Obsidian `Docs`.

## 1. Princípio

Não deixe contexto importante apenas no chat. Registre na vault quando tiver valor futuro.

- Se é captura rápida, salve em `01_Inbox/Quick_Capture.md` ou no daily.
- Se é andamento do dia, salve em `10_Daily/`.
- Se é execução com resultado, salve em `20_Projects/`.
- Se é responsabilidade contínua, salve em `30_Areas/`.
- Se é conhecimento durável, salve em `40_Second_Brain/`.
- Se é legado ou inativo, mantenha em `80_Archive/`.

## 2. Estrutura do Vault

Vault local: `/home/matheus/Documentos/Obsidian Vault/Docs`

Vault na VPS: `/root/obsidian-vault`

MCP no OpenCode: `obsidian-vault`

```text
Docs/
├── 00_System/           # Dashboard, convenções e reviews
├── 01_Inbox/            # Captura rápida e notas de IA não processadas
├── 10_Daily/            # Jornal operacional por data
├── 20_Projects/         # Projetos ativos com tarefas e decisões
├── 30_Areas/            # Responsabilidades contínuas
├── 40_Second_Brain/     # Conhecimento durável por tópicos
├── 50_Resources/        # Referências e materiais brutos
├── 80_Archive/          # Legado e inativos
└── 90_Templates/        # Templates de notas
```

## 3. Ferramentas MCP Disponíveis

O servidor `obsidian-vault` expõe ferramentas para:

- `vault_info`: verificar root, remote, branch e status.
- `git_pull`: atualizar a vault na VPS.
- `git_status`: ver mudanças pendentes.
- `git_commit_push`: commitar e enviar mudanças da VPS.
- `list_directory`: listar pastas e arquivos.
- `read_note`: ler uma nota por caminho.
- `write_note`: criar ou sobrescrever nota.
- `append_note`: adicionar conteúdo a uma nota.
- `daily_append`: adicionar conteúdo ao daily de hoje.
- `search_notes`: buscar texto nas notas.

Se as tools MCP não estiverem visíveis na sessão atual, use `opencode mcp list` para confirmar conexão e reinicie o OpenCode se a config acabou de mudar.

## 4. Rotas De Decisão

| Pedido do usuário | Onde registrar |
|---|---|
| "salva isso rápido" | `01_Inbox/Quick_Capture.md` |
| "registra no daily" | `10_Daily/YYYY/MM/YYYY-MM-DD.md` |
| "o que fizemos hoje" | Daily do dia |
| "handoff" | Daily ou `90_Templates/Handoff.md` aplicado ao projeto |
| "decisão" | Projeto atual ou `90_Templates/Decision.md` |
| "aprendizado" | `40_Second_Brain/<Topico>/` |
| "referência/link/material" | `50_Resources/` |
| "nota antiga" | buscar em `80_Archive/Legacy_*` |

## 5. Workflow Padrão

### Início de sessão

1. Use `git_pull` para atualizar a VPS.
2. Leia `00_System/Dashboard.md` quando precisar de visão geral.
3. Leia o daily atual quando o usuário pedir continuidade do dia.

### Durante a sessão

1. Registre capturas imediatas no daily ou inbox.
2. Para trabalho em projeto, registre tasks, decisões e log em `20_Projects/<Projeto>/`.
3. Não promova tudo para Second Brain; promova só conhecimento reutilizável.

### Fim ou pausa

1. Registre handoff no daily ou projeto.
2. Liste próximos passos como tarefas markdown.
3. Use `git_status` e, se houver mudança intencional, `git_commit_push`.

## 6. Padrões De Nota

### Daily operacional

Use `90_Templates/Daily.md` como base:

```markdown
## Foco Do Dia
## Tasks
## Log
## Decisoes
## Bloqueios
## Handoff
## Promover Para Segundo Cerebro
```

### Conhecimento durável

Use `90_Templates/Knowledge.md` e salve por tópico em `40_Second_Brain/`.

### Projetos

Use `90_Templates/Project.md` e crie uma pasta em `20_Projects/<Nome>/`.

## 7. Convenções

- Use frontmatter mínimo: `type`, `status`, `tags`.
- Use links Obsidian `[[...]]` quando a relação tiver valor futuro.
- Escreva decisões com contexto, decisão, motivo e consequências.
- Não apague legado sem pedido explícito; mova para `80_Archive/`.
- Antes de alterar muitas notas, use `git_status`.
- Depois de mudanças importantes na VPS, use `git_commit_push`.

## 8. Sincronização

Fluxo normal:

```text
OpenCode -> MCP na VPS -> /root/obsidian-vault -> GitHub -> vault local
```

Depois de mudanças na VPS, o usuário deve puxar localmente:

```bash
git -C "/home/matheus/Documentos/Obsidian Vault/Docs" pull --ff-only
```

Se houver alterações locais do Obsidian, peça cuidado antes de sobrescrever ou resolver conflitos.
