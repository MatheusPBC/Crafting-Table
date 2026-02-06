# Guia de Configuração de Servidores MCP

Este guia ajuda a configurar os servidores MCP (Model Context Protocol) para turbinar o nosso trabalho no Antigravity/Cursor.

## 1. Onde Configurar

1. Abra as configurações do Cursor ( atalho `Ctrl + ,` ou clique na engrenagem ⚙️).
2. Vá em **Features** > **MCP Servers**.
3. Você verá uma opção para adicionar novos servidores (botão "Add New MCP Server" ou similar, ou editar o JSON direto se disponível).

## 2. Configuração dos Servidores

Adicione os seguintes servidores.

### A. GitHub (Para ver PRs, Issues e código remoto)

**Nome:** `github`
**Type:** `command`
**Command:** `npx`
**Args:**

```text
-y
@modelcontextprotocol/server-github
```

**Environment Variables (Env):**
Você precisa de um Token do GitHub.

1. Crie um token aqui: [GitHub Tokens](https://github.com/settings/tokens?type=beta) (Dê permissão de leitura em repositórios/issues).
2. Adicione a variável:
   - Key: `GITHUB_PERSONAL_ACCESS_TOKEN`
   - Value: `seu_token_que_começa_com_github_pat_xxxx`

---

### B. MySQL (Para acessar o banco local)

Como seu banco é MySQL, usaremos um servidor compatível.
**Nome:** `mysql-local`
**Type:** `command`
**Command:** `npx`
**Args:**

```text
-y
mcp-server-mysql
--host
localhost
--port
3307
--user
root
--password
root
--database
dev
```

*(Nota: Se o pacote `mcp-server-mysql` não funcionar direto, podemos usar um script Python customizado).*

---

### C. Docker (Para gerenciar containers)

**Nome:** `docker`
**Type:** `command`
**Command:** `npx`
**Args:**

```text
-y
@modelcontextprotocol/server-docker
```

---

### D. AWS (Para verificar recursos na nuvem)

*Requer AWS CLI configurado localmente (`aws configure`).*
**Nome:** `aws`
**Type:** `command`
**Command:** `npx`
**Args:**

```text
-y
@modelcontextprotocol/server-aws
```

---

### E. Obsidian (Para acessar suas notas)

**Nome:** `obsidian`
**Type:** `command`
**Command:** `npx`
**Args:**

```text
-y
@mauricio.wolff/mcp-obsidian@latest
"/home/matheus/Documentos/Obsidian Vault"
```

---

## 3. Após Adicionar

Depois de adicionar, verifique se a "luzinha" verde acende ao lado do servidor na lista do MCP. Se ficar vermelha, clique para ver o log de erro (geralmente falta de token ou comando não encontrado).

### Resumo para Copiar (JSON)

Se sua ferramenta aceitar editar o JSON direto (arquivo `config.json` ou similar):

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "INSIRA_SEU_TOKEN_AQUI"
      }
    },
    "mysql": {
      "command": "npx",
      "args": ["-y", "mcp-server-mysql", "--host", "localhost", "--port", "3307", "--user", "root", "--password", "root", "--database", "dev"]
    },
    "docker": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-docker"]
    },
    "aws": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-aws"]
    },
    "obsidian": {
      "command": "npx",
      "args": ["-y", "@mauricio.wolff/mcp-obsidian@latest", "/home/matheus/Documentos/Obsidian Vault"]
    }
  }
}
```
