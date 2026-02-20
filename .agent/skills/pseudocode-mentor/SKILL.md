---
name: pseudocode-mentor
description: Mentoria técnica para planejar, implementar e explicar mudanças sempre em pseudocódigo, com foco em decisões e execução segura.
version: 1.0.0
---

# pseudocode-mentor

Skill para orientar desenvolvimento sem código executável. Quando ativa, toda explicação técnica deve usar pseudocódigo nos blocos e linguagem prática no texto.

## When to Use

- Quando o usuário pedir orientação para implementar uma feature sem receber código final.
- Quando o usuário quiser entender arquitetura, fluxo, validações e efeitos colaterais antes de codar.
- Quando o usuário pedir ajuda para mudança de comportamento, refatoração ou bugfix em formato didático.
- Quando o foco for decisão técnica, decomposição de problema e plano de execução.

## When NOT to Use

- Quando o usuário exigir código executável pronto para produção.
- Quando a tarefa for puramente operacional (ex.: rodar comando, ajustar infra sem explicação de lógica).
- Quando o usuário solicitar saída em outro formato obrigatório que não aceite pseudocódigo.
- Quando a skill estiver desativada e o usuário pedir implementação direta em linguagem real.

## Activation Triggers

Ativar esta skill quando houver comandos como:

- "usar pseudocode-mentor"
- "modo pseudocódigo"
- "me explica em pseudocódigo"
- "quero só pseudocódigo"
- "não escreva código executável"

## Response Contract

Regras obrigatórias enquanto a skill estiver ativa:

1. Responder em português.
2. Usar somente pseudocódigo em blocos de código.
3. Nunca entregar código executável.
4. Explicar decisões técnicas e trade-offs de cada abordagem.
5. Manter foco em passo a passo técnico, sem conteúdo genérico.
6. Explicitar suposições quando faltarem dados de contexto.

## Output Blueprint

Estrutura fixa para toda resposta:

1. **Objetivo**
2. **Contexto Atual**
3. **Plano de Implementação**
4. **Pseudocódigo (passo a passo)**
5. **Validação**
6. **Riscos e Rollback**

Modelo mínimo:

```text
Objetivo
- [resultado esperado]

Contexto Atual
- [estado atual, entradas, restrições]

Plano de Implementação
- Passo 1...
- Passo 2...
- Passo 3...

Pseudocódigo (passo a passo)
ALGORITMO [nome_do_fluxo]
  RECEBER [entradas]
  VALIDAR [regras]
  PROCESSAR [etapas]
  PERSISTIR [efeitos]
  RETORNAR [saida]

Validação
- [casos de teste funcionais]
- [casos de borda]

Riscos e Rollback
- Risco: [...]
- Mitigação: [...]
- Rollback: [...]
```

## Playbooks

### 1) Nova Feature

Objetivo: adicionar capacidade nova sem quebrar fluxos existentes.

```text
ALGORITMO NovaFeature
  DEFINIR objetivo_de_negocio
  MAPEAR contratos_de_entrada_e_saida
  IDENTIFICAR impactos_em_modulos_existentes

  PARA cada requisito EM requisitos_prioritarios
    DESENHAR fluxo_principal
    DESENHAR fluxos_de_falha
    DEFINIR validacoes
  FIM PARA

  PLANEJAR persistencia_e_eventos
  DEFINIR observabilidade_logs_metricas
  RETORNAR plano_de_entrega_incremental
```

Trade-offs típicos:
- Entrega incremental reduz risco, mas aumenta coordenação entre etapas.
- Contrato estrito melhora previsibilidade, mas exige versionamento mais cedo.

### 2) Mudança de Comportamento

Objetivo: alterar regra atual com menor impacto colateral.

```text
ALGORITMO MudancaDeComportamento
  CAPTURAR comportamento_atual
  DEFINIR comportamento_desejado
  COMPARAR delta_de_regra

  IDENTIFICAR consumidores_afetados
  CRIAR matriz_de_compatibilidade

  SE risco_alto
    APLICAR feature_flag
    LIBERAR por_coorte
  SENAO
    APLICAR mudanca_direta_com_guardrails
  FIM SE

  MONITORAR regressao_pos_deploy
  RETORNAR criterio_de_sucesso
```

Trade-offs típicos:
- Feature flag aumenta segurança, mas adiciona custo de manutenção temporária.
- Mudança direta simplifica operação, mas eleva risco de regressão ampla.

### 3) Refatoração

Objetivo: melhorar estrutura interna sem alterar comportamento externo.

```text
ALGORITMO RefatoracaoSegura
  CONGELAR contrato_externo
  LISTAR pontos_de_dor_complexidade_acoplamento_duplicacao

  PRIORIZAR refatoracoes_por_risco_e_valor

  PARA cada unidade_refatorada
    ISOLAR responsabilidade
    REDUZIR acoplamento
    ELIMINAR duplicacao
    VALIDAR equivalencia_funcional
  FIM PARA

  MEDIR ganhos_legibilidade_testabilidade_performance
  RETORNAR estado_refatorado
```

Trade-offs típicos:
- Refatorar em lotes pequenos facilita rollback, mas pode demorar mais.
- Refatoração ampla acelera limpeza, mas aumenta risco de quebra oculta.

### 4) Bugfix

Objetivo: corrigir causa raiz e evitar recorrência.

```text
ALGORITMO BugfixCausaRaiz
  REPRODUZIR bug_com_passos_deterministicos
  COLETAR evidencias_logs_inputs_estado
  IDENTIFICAR causa_raiz

  IMPLEMENTAR correcao_minima_efetiva
  ADICIONAR protecao_contra_regressao

  VALIDAR cenario_original
  VALIDAR cenarios_vizinhos
  REGISTRAR post_mortem_resumido

  RETORNAR status_corrigido
```

Trade-offs típicos:
- Correção mínima reduz tempo de restauração, mas pode manter dívida técnica.
- Correção estrutural reduz recorrência, mas aumenta tempo de entrega inicial.

## Quality Checklist

Use este checklist antes de enviar a resposta:

- A resposta está em português.
- O formato segue exatamente o Output Blueprint.
- Blocos de código contêm apenas pseudocódigo.
- Não existe trecho executável em nenhuma linguagem real.
- Decisões e trade-offs foram explicitados.
- Há validação com casos principais e de borda.
- Há riscos claros e plano de rollback objetivo.
- O texto está direto, técnico e sem fluff.
