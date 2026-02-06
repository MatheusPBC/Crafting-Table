---
name: aula-md
description: Gera aulas e mini-cursos técnicos em Markdown (pt-BR) com foco em didática, aplicação prática e recursos visuais.
version: 1.0.0
---

# Skill: Aula/Curso (aula-md)

**Propósito**: Transformar tópicos técnicos em material didático "mastigado", organizado e visual, pronto para consulta e aplicação prática.

## 1. Gatilho e Ativação

Esta skill deve ser usada quando o usuário solicitar explicitamente:

- `use a skill aula: <TOPICO>`
- `aula: <TOPICO>`

### Opções Inline

- `path=<caminho.md>`: Sobrescreve o destino padrão (`docs/aulas/<slug>.md`).
- `escopo=<pasta|arquivos>`: Limita a análise do repositório a estes locais.
- `nivel=basico|normal|avancado`: Define a profundidade técnica (padrão: `normal`).

## 2. Protocolo de Operação

### 2.1 Coleta de Contexto

1. **Analise o pedido**: Identifique o tópico central e o objetivo prático.
2. **Perguntas (Socrático)**: Faça até 5 perguntas focadas para alinhar o conteúdo.
3. **Prosseguimento**: Se o usuário disser "prossegue", registre **Suposições** no topo do arquivo e use um caminho padrão razoável.

### 2.2 Análise do Repositório (Se aplicável)

Se o tópico envolver código do projeto:

- Selecione arquivos relevantes.
- Extraia trechos mínimos para ilustrar conceitos.
- Identifique decisões arquiteturais e padrões usados.

### 2.3 Geração do Conteúdo

Siga rigorosamente a estrutura definida na seção 4.

## 3. Diretrizes de Didática e Design

### 3.1 Princípios

- **Progressivo**: Comece pelo "porquê" e "o quê", depois vá para o "como".
- **Aplicável**: Inclua passos executáveis e validações.
- **Visual**: Use recursos visuais sempre que houver fluxos ou muitos componentes.

### 3.2 Recursos Visuais Obrigatórios

- **Diagramas Mermaid**:
  - `flowchart` para processos.
  - `sequenceDiagram` para interações temporais.
  - `mindmap` para conceitos.
- **Tabelas**: Para comparações, glossários e listas de componentes.
- **Checklists**: Para pré-requisitos e validação final.

### 3.3 Código

- Use blocos cercados com linguagem específica.
- Explique pontos críticos linha a linha (comentários ou texto explicativo).

## 4. Estrutura Padrão do Markdown (Outline)

Todo arquivo gerado deve seguir esta ordem:

1. **Título (H1)**
2. **Introdução**: O que é e para que serve.
3. **Quando usar vs. Quando não usar**: Casos de uso e trade-offs.
4. **Pré-requisitos**: O que o usuário precisa ter instalado ou saber.
5. **Conceitos Fundamentais**: Glossário essencial e componentes.
6. **Arquitetura**: Como foi feito e por que (decisões).
7. **Fluxo de Funcionamento**: Diagrama Mermaid detalhando o processo.
8. **Como Usar (Passo a Passo)**: Guia prático com comandos e saídas esperadas.
9. **Exemplos de Código**: Casos reais ou didáticos comentados.
10. **Troubleshooting**: Erros comuns e como resolver.
11. **Boas Práticas**: Dicas de ouro (segurança, performance).
12. **Limites e Pegadinhas**: O que pode dar errado ou não é suportado.
13. **Checklist Final**: Critérios de sucesso.
14. **Exercícios/Revisão**: Perguntas para fixação.
15. **FAQ**: Perguntas frequentes curtas.
16. **Fontes Consultadas**: Lista de arquivos do repo e observações.

## 5. Regras Especiais para Terraform

Se o tópico envolver Terraform:

- Inclua exemplos em `hcl`.
- Explique brevemente o papel do `state`, `providers` e `resources` no contexto.
- Sugira organização de arquivos.

## 6. Definition of Done (Qualidade)

Um arquivo de aula só é entregue se:

- Tiver pelo menos 1 diagrama visual adequado.
- Contiver um passo a passo 100% executável.
- Tiver glossário e FAQ completo.
- Estiver em `docs/aulas/` com nome em slug.
