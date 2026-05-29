# SKILL: OpenCode Proxy (opencode-proxy)

Manual para uso do proxy de LLM do OpenCode para acesso a modelos globais.

## 🎯 Objetivo
Padronizar o acesso a LLMs (OpenAI, Anthropic, Gemini) através do proxy interno do OpenCode usando chaves JWT.

## 🔑 Autenticação
- **Protocolo:** Compatível com OpenAI.
- **Base URL:** `https://openrouter.ai/api/v1` (Ponte principal).
- **API Key:** Sua chave JWT (ex: `eyJhbGci...`).

## 🤖 Modelos Recomendados
- **Raciocínio Complexo:** `openai/gpt-4o`, `anthropic/claude-3.5-sonnet`.
- **Análises Rápidas:** `openai/gpt-4o-mini`, `google/gemini-2.0-flash-lite:free`.

## 🛠️ Configuração de Ambiente
Sempre que configurar um novo agente ou ferramenta, use o padrão:
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=SUA_CHAVE_JWT
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

## 📝 Regras de Segurança
1. **Nunca Logue o JWT:** Ao rodar comandos `env` ou listar configurações, use `grep -v` para ocultar o token.
2. **Rota de Backup:** Se o OpenRouter falhar, tente o endpoint direto do Kilo Code se disponível.
