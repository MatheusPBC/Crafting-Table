# Prefer opencode-nvim MCP for terminal Neovim navigation

Quando a sessao estiver acontecendo no terminal do OpenCode e o usuario pedir explicitamente para abrir, navegar ou escolher arquivos no Neovim atual, o agente deve priorizar o MCP `opencode-nvim`.

## Diretrizes

- Antes de concluir que a abertura falhou, verifique `opencode mcp list`.
- Se `opencode-nvim` estiver `connected`, trate isso como fonte da verdade para navegacao no Neovim.
- Nomes como `opencode-nvim_open_file` e `opencode-nvim_open_candidates` podem ser os tools MCP namespaced do proprio `opencode-nvim`.
- Se um desses tools retornar `Not connected`, nao trate isso como falha de descoberta; trate como falha de ponte para diagnosticar.
- Para alvo unico, prefira `open_file`.
- Para ambiguidade ou multiplos candidatos razoaveis, prefira `open_candidates`.
- Se o servidor estiver `connected` mas o tool falhar com `Not connected`, verifique `OPENCODE_NVIM_RPC`, tente uma vez de novo e, se o usuario ainda quiser a abertura, use fallback confiavel com `nvim --server "$OPENCODE_NVIM_RPC" --remote-expr ...`.
- Nao use `--remote-send` como fallback padrao para automacao.
