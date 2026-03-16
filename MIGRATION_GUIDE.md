# Guia de Migração: Kilo CLI para OpenCode CLI

Este documento descreve o processo completo de migração de configurações, skills, MCPs, agentes e sessões do Kilo CLI para o OpenCode CLI.

## Visão Geral

A migração envolve:
1. **Configuração global** (`~/.config/opencode/`)
2. **Skills globais** (`.opencode/skills/`)
3. **MCPs globais** (opencode.json)
4. **Agentes e comandos customizados** (`.opencode/agents/` e `.opencode/commands/`)
5. **Sessões** (`~/.local/share/opencode/storage/`)
6. **Custom tools/aifns** (`.opencode/tools/`)

---

## 1. Pré-requisitos

- OpenCode CLI instalado (`~/.opencode/bin/opencode`)
- Kilo CLI instalado (opcional, apenas para migração de sessões)
- Python 3.10+ para scripts auxiliares

---

## 2. Estrutura de Diretórios

### Kilo CLI (origem)
```
~/.kilocode/                    # Regras globais do usuário
~/.local/share/kilo/            # Dados locais (sessões, etc)
<projeto>/.kilocode/            # Config local do projeto
<projeto>/.agent/               # Agentes e automações do projeto
<projeto>/.gemini/              # Config de MCP de referência
<projeto>/.mcp_servers/         # MCPs customizados do projeto
```

### OpenCode CLI (destino)
```
~/.config/opencode/             # Config global do usuário
  ├── opencode.json             # MCPs, instruções globais
  ├── agents/                   # Agentes customizados globais
  ├── commands/                 # Comandos customizados globais
  ├── skills/                   # Skills globais
  ├── tools/                    # Custom tools (aifns)
  └── superpowers/              # Skills extras (opcional)

~/.local/share/opencode/        # Dados locais (sessões, etc)
  ├── storage/                  # Sessões migradas
  └── opencode.db               # Banco de dados local

<projeto>/.opencode/            # Config local do projeto
  ├── opencode.json             # MCPs e instruções do projeto
  ├── agents/                   # Agentes do projeto
  ├── commands/                 # Comandos do projeto
  ├── skills/                   # Skills do projeto
  └── mcp_servers/              # MCPs do projeto
```

---

## 3. Migração de Configuração Global

### 3.1 Criar diretório base

```bash
mkdir -p ~/.config/opencode/{agents,commands,skills,tools,plugins}
```

### 3.2 Criar opencode.json global

Arquivo: `~/.config/opencode/opencode.json`

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [
    "~/.kilocode/rules/*.md"
  ],
  "mcp": {
    "context7": {
      "type": "remote",
      "url": "https://mcp.context7.com/mcp",
      "enabled": true,
      "headers": {
        "CONTEXT7_API_KEY": "{env:CONTEXT7_API_KEY}"
      }
    },
    "github": {
      "type": "local",
      "command": [
        "bash",
        "-lc",
        "GITHUB_PERSONAL_ACCESS_TOKEN=\"$(gh auth token)\" exec docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server"
      ],
      "enabled": true,
      "timeout": 120000
    },
    "cocoindex-code": {
      "type": "local",
      "command": ["cocoindex-code"],
      "enabled": true,
      "timeout": 120000
    }
  }
}
```

**Notas:**
- `instructions`: aponta para regras globais do Kilo
- MCPs `github` e `context7` são recomendados globalmente
- `cocoindex-code` é opcional, mas útil para busca semântica

---

## 4. Migração de Skills

### 4.1 Copiar skills do projeto para global

```bash
# Copiar skills do projeto (Kilo) para global (OpenCode)
cp -r <projeto>/.kilocode/skills/* ~/.config/opencode/skills/

# OU copiar do .agent/skills se for o caso
cp -r <projeto>/.agent/skills/* ~/.config/opencode/skills/
```

### 4.2 Remover skills específicas de projeto (opcional)

Skills muito específicas de um projeto não devem ficar no global:

```bash
# Mover skills específicas para um diretório de backup
mkdir -p ~/.config/opencode/skills-disabled
mv ~/.config/opencode/skills/projeto-especifico ~/.config/opencode/skills-disabled/
```

### 4.3 Verificar formato das skills

Cada skill deve ter um arquivo `SKILL.md` com frontmatter:

```markdown
---
name: skill-name
description: Descrição da skill
compatibility: opencode
---

# Conteúdo da skill...
```

---

## 5. Migração de Agentes

### 5.1 Converter formato dos agentes

Agentes do Kilo precisam de adaptação de frontmatter:

**Kilo (origem):**
```markdown
---
description: Descrição do agente
tools: Bash, Read, Write, Edit
skills: clean-code, brainstorming
---

# Conteúdo...
```

**OpenCode (destino):**
```markdown
---
description: "Descrição do agente"
mode: all
tools:
  bash: true
  read: true
  write: true
  edit: true
  task: false
---

OpenCode adaptation notes:
- Use the native `skill` tool to load relevant skills before acting.

# Conteúdo...
```

### 5.2 Script de conversão

```python
#!/usr/bin/env python3
import re
from pathlib import Path

def convert_agent(input_path: Path, output_path: Path):
    content = input_path.read_text(encoding="utf-8")
    
    # Extrair frontmatter
    match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    if not match:
        return
    
    fm_raw = match.group(1)
    body = match.group(2)
    
    # Parsear frontmatter
    fm = {}
    for line in fm_raw.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            fm[key.strip()] = value.strip()
    
    # Converter tools
    tools_raw = [t.strip() for t in fm.get('tools', '').split(',') if t.strip()]
    tools_lower = {t.lower() for t in tools_raw}
    
    tool_lines = []
    if 'bash' not in tools_lower:
        tool_lines.append('  bash: false')
    if 'edit' not in tools_lower:
        tool_lines.append('  edit: false')
    if 'write' not in tools_lower:
        tool_lines.append('  write: false')
    
    # Gerar output
    output = [
        '---',
        f'description: "{fm.get("description", "")}"',
        'mode: all',
    ]
    if tool_lines:
        output.append('tools:')
        output.extend(tool_lines)
    output.append('---')
    output.append('')
    output.append('OpenCode adaptation notes:')
    output.append('- Use the native `skill` tool to load relevant skills.')
    output.append('')
    output.append(body.lstrip())
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(output), encoding='utf-8')
```

---

## 6. Migração de Comandos

### 6.1 Estrutura de comandos

Diretório: `~/.config/opencode/commands/`

Cada comando é um arquivo `.md`:

```markdown
---
description: "Descrição do comando"
agent: project-planner
subtask: false
---

OpenCode command notes:
- Use this command when the user wants X.

# /comando

$ARGUMENTS

Comportamento detalhado aqui...
```

---

## 7. Migração de Custom Tools (aifns)

### 7.1 Estrutura

Diretório: `~/.config/opencode/tools/`

Cada tool é um arquivo `.js` ou `.ts` que exporta uma tool:

```javascript
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Descrição da tool",
  args: {
    param1: tool.schema.string().describe("Descrição do parâmetro"),
  },
  async execute(args, context) {
    return "Resultado"
  },
})
```

### 7.2 Exemplos úteis

- `find_skills.js` - Lista skills disponíveis
- `use_skill.js` - Carrega conteúdo de uma skill
- `find_agents.js` - Lista agentes customizados
- `find_commands.js` - Lista comandos customizados
- `global_context.js` - Resume setup global

---

## 8. Migração de MCPs Customizados

### 8.1 MCPs locais do projeto

Copiar para o projeto OpenCode:

```bash
# Copiar MCPs customizados
cp -r <projeto-kilo>/.mcp_servers/* <projeto-opencode>/.opencode/mcp_servers/
```

### 8.2 Registrar no opencode.json do projeto

```json
{
  "mcp": {
    "mysql-local": {
      "type": "local",
      "command": ["uv", "run", ".opencode/mcp_servers/mysql_mcp_server.py"],
      "enabled": false,
      "environment": {
        "MYSQL_HOST": "{env:MYSQL_HOST}",
        "MYSQL_USER": "{env:MYSQL_USER}"
      }
    }
  }
}
```

---

## 9. Migração de Sessões

### 9.1 Estrutura de sessões

**Kilo:**
```
~/.local/share/kilo/storage/
  ├── session/global/*.json     # Metadados da sessão
  ├── message/<session_id>/*.json  # Mensagens
  └── part/<message_id>/*.json     # Partes das mensagens
```

**OpenCode:**
```
~/.local/share/opencode/storage/
  ├── session/global/*.json
  ├── message/<session_id>/*.json
  ├── part/<message_id>/*.json
  └── project/global.json
```

### 9.2 Script de migração

Use o script em `~/.local/bin/kilo-to-opencode.py`:

```bash
# Listar sessões disponíveis
python3 ~/.local/bin/kilo-to-opencode.py --list

# Preview (sem gravar)
python3 ~/.local/bin/kilo-to-opencode.py --session ses_XXX --dry-run

# Migrar uma sessão
python3 ~/.local/bin/kilo-to-opencode.py --session ses_XXX

# Migrar todas com backup
python3 ~/.local/bin/kilo-to-opencode.py --all --backup
```

### 9.3 Código do script

O script completo está disponível em `~/.local/bin/kilo-to-opencode.py` e faz:
1. Lê sessões do Kilo (`~/.local/share/kilo/storage/`)
2. Converte formato JSON (quase idêntico)
3. Copia mensagens e partes
4. Cria backup opcional
5. Suporta `--dry-run` para preview

---

## 10. Configuração do Shell

### 10.1 Corrigir bug "Session not found"

Adicionar ao `~/.bashrc`:

```bash
# Prevenir bug do OpenCode CLI
unset OPENCODE_SERVER_USERNAME
unset OPENCODE_SERVER_PASSWORD
unset OPENCODE_PID
unset OPENCODE_CLIENT
```

### 10.2 Aliases úteis

```bash
# OpencOde aliases
alias oc='opencode'
alias ocr='opencode run'
alias oca='opencode agent list'
alias ocm='opencode mcp list'
```

---

## 11. Verificação Pós-Migração

### 11.1 Verificar MCPs

```bash
opencode mcp list
```

Deve mostrar `docker-local`, `context7`, `github`, `cocoindex-code` como conectados.

### 11.2 Verificar agentes

```bash
opencode agent list
```

Deve listar agentes customizados em `~/.config/opencode/agents/`.

### 11.3 Testar sessão importada

```bash
# Listar sessões
opencode session list -n 10

# Continuar uma sessão migrada
opencode session <session_id>
```

### 11.4 Testar skills e tools

```bash
opencode run "Use the global_context tool and summarize my setup."
```

---

## 12. Checklist de Migração

- [ ] Criar `~/.config/opencode/` e subdiretórios
- [ ] Criar `~/.config/opencode/opencode.json` com MCPs globais
- [ ] Copiar skills globais para `~/.config/opencode/skills/`
- [ ] Converter e copiar agentes para `~/.config/opencode/agents/`
- [ ] Converter e copiar comandos para `~/.config/opencode/commands/`
- [ ] Criar custom tools em `~/.config/opencode/tools/`
- [ ] Copiar MCPs locais do projeto para `.opencode/mcp_servers/`
- [ ] Atualizar `opencode.json` do projeto com MCPs locais
- [ ] Migrar sessões com `kilo-to-opencode.py`
- [ ] Configurar `~/.bashrc` com fixes e aliases
- [ ] Verificar com `opencode mcp list` e `opencode agent list`

---

## 13. Problemas Conhecidos

### 13.1 "Session not found" no `opencode run`

**Causa:** Variáveis de ambiente do desktop app interferindo.

**Solução:** Adicionar ao `~/.bashrc`:
```bash
unset OPENCODE_SERVER_USERNAME
unset OPENCODE_SERVER_PASSWORD
unset OPENCODE_PID
unset OPENCODE_CLIENT
```

### 13.2 Plugin global quebrando

**Solução:** Remover plugin global problemático e usar custom tools em vez de plugins.

```bash
rm ~/.config/opencode/plugins/*.js
```

### 13.3 Skills não carregando

**Verificar:**
1. Arquivo `SKILL.md` existe no diretório
2. Frontmatter está correto (`name`, `description`, `compatibility`)
3. Diretório está em `~/.config/opencode/skills/` ou `.opencode/skills/`

---

## 14. Referências

- OpenCode docs: https://opencode.ai/docs
- Context7 MCP: https://mcp.context7.com
- GitHub MCP: https://github.com/github/github-mcp-server
- CocoIndex: https://github.com/cocoindex-io/cocoindex-code

---

## 15. Arquivos de Referência deste Repositório

- `~/.config/opencode/opencode.json` - Config global
- `~/.config/opencode/agents/` - Agentes globais
- `~/.config/opencode/commands/` - Comandos globais
- `~/.config/opencode/skills/` - Skills globais
- `~/.config/opencode/tools/` - Custom tools
- `~/.local/bin/kilo-to-opencode.py` - Script de migração de sessões
- `_dest_Crafting-Table/` - Este documento

---

## 16. Próximos Passos após Migração

1. **Limpar skills desnecessárias**: Mover skills específicas de projeto para `skills-disabled/`
2. **Refinar agentes**: Ajustar prompts para ficarem mais nativos do OpenCode
3. **Adicionar mais tools**: Criar tools globais para git, github, etc.
4. **Organizar aliases**: Revisar aliases do shell para eficiência
5. **Documentar específicos do projeto**: Adicionar instruções no `AGENTS.md` ou `opencode.json` do projeto

---

*Documento criado durante migração de Kilo CLI para OpenCode CLI em Março 2026.*