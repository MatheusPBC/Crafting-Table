---
name: aula-md
description: Gera aulas e mini-cursos técnicos em Markdown (pt-BR) com foco em didática, aplicação prática e recursos visuais. Inclui trilhas de aprendizado (entender existente + construir do zero), checklists de verificação e comandos concretos.
version: 2.0.0
---

# Skill: Aula/Curso (aula-md)

**Propósito**: Transformar tópicos técnicos em material didático "mastigado", organizado e visual, pronto para consulta e aplicação prática. A skill gera aulas acionáveis que ensinam a construir do zero até o fim, não apenas explicar conceitos.

## 1. Gatilho e Ativação

Esta skill deve ser usada quando o usuário solicitar explicitamente:

- `use a skill aula: <TOPICO>`
- `aula: <TOPICO>`

### Opções Inline

- `path=<caminho.md>`: Sobrescreve o destino padrão (`docs/aulas/<slug>.md`).
- `escopo=<pasta|arquivos>`: Limita a análise do repositório a estes locais.
- `nivel=basico|normal|avancado`: Define a profundidade técnica (padrão: `normal`).
- `trilha=A|B|ambas`: `A` = entender existente, `B` = construir do zero, `ambas` = ambas (padrão).

## 2. Protocolo de Operação

### 2.1 Coleta de Contexto

1. **Analise o pedido**: Identifique o tópico central e o objetivo prático.
2. **Perguntas de Alinhamento (Obrigatório para infra/integrações)**:
   - Se o tópico envolver **AppSync, Terraform, DB ou integrações complexas**, faça **1-3 perguntas focadas** antes de gerar conteúdo:
     - "Qual o ambiente alvo? (local/dev/prod)"
     - "Você quer entender o existente ou construir do zero?"
     - "Quais componentes já existem no projeto?"
   - Se o usuário disser "prossegue" sem responder, registre **Suposições** no topo do arquivo.
3. **Perguntas (Socrático - opcional)**: Para tópicos menos complexos, faça até 5 perguntas focadas para alinhar o conteúdo.
4. **Prosseguimento**: Se o usuário disser "prossegue", registre **Suposições** no topo do arquivo e use um caminho padrão razoável.

### 2.2 Análise do Repositório (Se aplicável)

Se o tópico envolver código do projeto:

- Selecione arquivos relevantes.
- Extraia trechos mínimos para ilustrar conceitos.
- Identifique decisões arquiteturais e padrões usados.

### 2.3 Geração do Conteúdo

Siga rigorosamente a estrutura definida na seção 4. **NUNCA execute comandos automaticamente** - apenas liste-os para o usuário executar.

## 3. Framework de Trilhas de Aprendizado

Toda aula gerada deve incluir **pelo menos uma das trilhas abaixo**. Se o usuário não especificar, use **ambas as trilhas**.

### 3.1 Trilha A: Entender o Existente

**Objetivo**: Compreender como o sistema atual funciona, sem modificar nada.

**Estrutura obrigatória**:

- **Visão geral**: O que o componente faz e onde ele se encaixa no sistema.
- **Arquitetura**: Diagrama de componentes e suas interações.
- **Fluxo de dados**: Como os dados fluem de entrada até saída.
- **Pontos-chave**: Decisões arquiteturais, padrões usados e trade-offs.
- **Arquivos relevantes**: Lista de arquivos com links clicáveis e breve descrição.
- **Como debugar**: Passos para investigar problemas no código existente.

**Quando usar**: Quando o usuário quer entender um sistema já implementado.

### 3.2 Trilha B: Construir do Zero ao Fim

**Objetivo**: Guia passo-a-passo executável para construir o componente do zero.

**Estrutura obrigatória**:

- **Pré-requisitos mínimos**: Ferramentas, dependências e conhecimentos necessários.
- **Setup do ambiente**: Comandos concretos para preparar o ambiente (ex.: `docker compose up`, `terraform init`).
- **Passo 1 - Fundação**: Criar estrutura base, arquivos iniciais.
- **Passo 2 - Implementação core**: Lógica principal do componente.
- **Passo 3 - Integração**: Conectar com outros componentes.
- **Passo 4 - Testes**: Smoke tests e validações.
- **Passo 5 - Deploy**: Como fazer deploy (se aplicável).
- **Checklist de verificação por etapa**: Inputs esperados, outputs esperados e como validar cada passo.

**Quando usar**: Quando o usuário quer construir algo novo ou recriar um componente.

### 3.3 Checklist de Verificação por Etapa

Para cada passo da Trilha B, inclua:

```markdown
### Passo X: <Nome do Passo>

**Objetivo**: <O que você vai fazer>

**Pré-requisitos**: <O que precisa estar pronto antes>

**Comandos**:
```bash
# Comando 1
<comando concreto>

# Comando 2
<comando concreto>
```

**Verificação**:

- [ ] <Critério 1>
- [ ] <Critério 2>
- [ ] <Critério 3>

**Output esperado**:

```
<exemplo do que você deve ver>
```

**Se falhar**:

- <Erro comum 1>: <como diagnosticar>
- <Erro comum 2>: <como diagnosticar>

```

## 4. Diretrizes de Didática e Design

### 4.1 Princípios

- **Progressivo**: Comece pelo "porquê" e "o quê", depois vá para o "como".
- **Aplicável**: Inclua passos executáveis e validações.
- **Visual**: Use recursos visuais sempre que houver fluxos ou muitos componentes.
- **Acionável**: Cada seção deve ter um "o que fazer agora" claro.

### 4.2 Recursos Visuais Obrigatórios

- **Diagramas Mermaid**:
  - `flowchart` para processos.
  - `sequenceDiagram` para interações temporais.
  - `mindmap` para conceitos.
- **Tabelas**: Para comparações, glossários e listas de componentes.
- **Checklists**: Para pré-requisitos e validação final.

### 4.3 Código

- Use blocos cercados com linguagem específica.
- Explique pontos críticos linha a linha (comentários ou texto explicativo).
- **Comandos concretos**: Sempre que possível, inclua comandos exatos (ex.: `terraform init`, `pytest tests/`, `docker compose up -d`).
- **NUNCA execute comandos automaticamente**: Apenas liste-os para o usuário executar.

### 4.4 Exercícios Guiados e Desafios de Extensão

**Exercícios guiados** (obrigatório para Trilha B):
- Pequenas tarefas práticas para fixar cada conceito.
- Exemplo: "Modifique X para fazer Y e verifique o resultado."

**Desafios de extensão** (opcional):
- Tarefas mais complexas para quem quer ir além.
- Exemplo: "Adicione suporte para Z no componente que você construiu."

### 4.5 Seção de Troubleshooting

**Obrigatório para toda aula**:

```markdown
## Troubleshooting

### Erro Comum 1: <Nome do erro>

**Sintoma**: <O que aparece>
```

<exemplo do erro>
```

**Causa provável**: <Por que acontece>

**Como diagnosticar**:

1. <Passo 1>
2. <Passo 2>

**Como resolver**:

```bash
<comando ou solução>
```

### Erro Comum 2: <Nome do erro>

...

```

### 4.6 Critérios de Sucesso

**Obrigatório para toda aula**:

```markdown
## Critérios de Sucesso

Você concluiu esta aula quando:

- [ ] <Critério 1 - verificável>
- [ ] <Critério 2 - verificável>
- [ ] <Critério 3 - verificável>

**Como validar**:
- <Método de validação 1>
- <Método de validação 2>
```

## 5. Estrutura Padrão do Markdown (Outline)

Todo arquivo gerado deve seguir esta ordem. **Seções marcadas com (Obrigatório)** devem estar sempre presentes.

### 5.1 Cabeçalho (Obrigatório)

```markdown
---
title: <Título da Aula>
slug: <slug-para-arquivo>
nivel: basico|normal|avancado
trilhas: A|B|ambas
data: <YYYY-MM-DD>
---

# <Título da Aula>

**Suposições** (se aplicável):
- <Suposição 1>
- <Suposição 2>
```

### 5.2 Corpo da Aula

1. **Introdução** (Obrigatório): O que é, para que serve e objetivos da aula.
2. **Quando usar vs. Quando não usar** (Obrigatório): Casos de uso e trade-offs.
3. **Pré-requisitos Mínimos** (Obrigatório):
   - Ferramentas instaladas
   - Conhecimentos necessários
   - Acesso/credenciais necessários
4. **Setup do Ambiente** (Obrigatório para Trilha B):
   - Comandos concretos para preparar o ambiente
   - Verificação de que tudo está pronto
5. **Trilha A: Entender o Existente** (Obrigatório se trilha=A ou ambas):
   - Visão geral do sistema
   - Arquitetura e componentes
   - Fluxo de dados
   - Pontos-chave e decisões
   - Arquivos relevantes (com links clicáveis)
   - Como debugar
6. **Trilha B: Construir do Zero ao Fim** (Obrigatório se trilha=B ou ambas):
   - Passo 1: Fundação (com checklist de verificação)
   - Passo 2: Implementação core (com checklist de verificação)
   - Passo 3: Integração (com checklist de verificação)
   - Passo 4: Testes (com checklist de verificação)
   - Passo 5: Deploy (se aplicável, com checklist de verificação)
7. **Conceitos Fundamentais**: Glossário essencial e componentes.
8. **Arquitetura**: Como foi feito e por que (decisões).
9. **Fluxo de Funcionamento**: Diagrama Mermaid detalhando o processo.
10. **Exemplos de Código**: Casos reais ou didáticos comentados.
11. **Exercícios Guiados** (Obrigatório para Trilha B): Pequenas tarefas práticas.
12. **Desafios de Extensão** (Opcional): Tarefas mais complexas para ir além.
13. **Troubleshooting** (Obrigatório): Erros comuns, como diagnosticar e resolver.
14. **Boas Práticas**: Dicas de ouro (segurança, performance).
15. **Limites e Pegadinhas**: O que pode dar errado ou não é suportado.
16. **Critérios de Sucesso** (Obrigatório): Checklist de como saber que concluiu.
17. **Exercícios/Revisão**: Perguntas para fixação.
18. **FAQ**: Perguntas frequentes curtas.
19. **Fontes Consultadas**: Lista de arquivos do repo (com links clicáveis) e observações.

### 5.3 Template de Checklist de Verificação por Etapa

```markdown
### Passo X: <Nome do Passo>

**Objetivo**: <O que você vai fazer>

**Pré-requisitos**:
- [ ] <Pré-requisito 1>
- [ ] <Pré-requisito 2>

**Comandos**:
```bash
# Comando 1
<comando concreto>

# Comando 2
<comando concreto>
```

**Verificação**:

- [ ] <Critério 1>
- [ ] <Critério 2>
- [ ] <Critério 3>

**Output esperado**:

```
<exemplo do que você deve ver>
```

**Se falhar**:

- **Erro**: <Erro comum>
  - **Causa**: <Por que acontece>
  - **Como diagnosticar**: <Passos>
  - **Como resolver**: <Solução>

```

### 5.4 Template de Critérios de Sucesso

```markdown
## Critérios de Sucesso

Você concluiu esta aula quando:

- [ ] <Critério 1 - verificável>
- [ ] <Critério 2 - verificável>
- [ ] <Critério 3 - verificável>

**Como validar**:
1. <Método de validação 1>
2. <Método de validação 2>
```

### 5.5 Template de Troubleshooting

```markdown
## Troubleshooting

### Erro Comum 1: <Nome do erro>

**Sintoma**: <O que aparece>
```

<exemplo do erro>
```

**Causa provável**: <Por que acontece>

**Como diagnosticar**:

1. <Passo 1>
2. <Passo 2>

**Como resolver**:

```bash
<comando ou solução>
```

```

## 6. Regras Especiais para Terraform

Se o tópico envolver Terraform:

- Inclua exemplos em `hcl`.
- Explique brevemente o papel do `state`, `providers` e `resources` no contexto.
- Sugira organização de arquivos.
- **Comandos concretos obrigatórios**:
  - `terraform init` - inicializar o working directory
  - `terraform plan` - visualizar mudanças antes de aplicar
  - `terraform apply` - aplicar mudanças
  - `terraform destroy` - destruir recursos (se aplicável)
- **Verificação de estado**: Como verificar se o Terraform aplicou corretamente.
- **Troubleshooting específico**: Erros comuns de Terraform e como resolver.

## 7. Definition of Done (Qualidade)

Um arquivo de aula só é entregue se:

- Tiver pelo menos 1 diagrama visual adequado.
- Contiver um passo a passo 100% executável (com comandos concretos).
- Tiver glossário e FAQ completo.
- Incluir **Critérios de Sucesso** verificáveis.
- Incluir seção de **Troubleshooting** com erros comuns.
- Incluir **Checklist de Verificação** por etapa (para Trilha B).
- Estiver em `docs/aulas/` com nome em slug.
- **NÃO ter executado nenhum comando automaticamente**.

## 8. Exemplo de Uso

### 8.1 Solicitação Básica

```

aula: AppSync com Terraform

```

**Resposta esperada do agente**:
1. Perguntas de alinhamento (1-3 perguntas):
   - "Qual o ambiente alvo? (local/dev/prod)"
   - "Você quer entender o existente ou construir do zero?"
   - "Quais componentes já existem no projeto?"
2. Após respostas, gerar aula com ambas as trilhas.

### 8.2 Solicitação com Opções

```

aula: Orquestração de dispositivos trilha=B nivel=avancado

```

**Resposta esperada do agente**:
1. Gerar aula focada apenas na Trilha B (Construir do Zero).
2. Nível avançado de profundidade técnica.
3. Incluir comandos concretos para cada passo.

### 8.3 Solicitação com Escopo

```

aula: Lambda handlers escopo=src/handlers/device_orchestration

```

**Resposta esperada do agente**:
1. Analisar apenas arquivos em `src/handlers/device_orchestration`.
2. Gerar aula focada nesse escopo específico.
