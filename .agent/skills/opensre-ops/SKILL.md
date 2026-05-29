# SKILL: OpenSRE Operations (opensre-ops)

Manual de operação para o agente de investigação de incidentes OpenSRE.

## 🎯 Objetivo
Automatizar a investigação de incidentes, coleta de evidências em infraestrutura (AWS, K8s) e diagnóstico de causa raiz (RCA).

## 🛠️ Ferramentas Disponíveis (via MCP)
- `run_rca`: Executa o workflow completo de investigação do OpenSRE.
  - **Inputs:** Alerta JSON, nome do alerta, pipeline e severidade.
  - **Output:** Relatório formatado, evidências citadas e causa raiz provável.

## 🚀 Como Usar
Para iniciar uma investigação, envie um alerta JSON para a ferramenta `run_rca`.

### Exemplo de Alerta
```json
{
  "status": "firing",
  "labels": { "alertname": "DatabaseTimeout", "severity": "critical" },
  "annotations": { "summary": "Tempo de resposta do RDS Smartly > 5s" }
}
```

## ⚙️ Configuração (Infra Smartly)
O OpenSRE está configurado para acessar:
- **AWS:** Conta Smartly (589464758178) via IAM.
- **Banco de Dados:** RDS Smartly (MariaDB) host: `smartly.cpha2xe1xu6q.us-east-1.rds.amazonaws.com`.
- **Código:** Repositório local `smartly.backend_smartly-dev` via GitHub MCP.

## 📝 Princípios
1. **Evidência sobre Suposição:** Nunca aceite um diagnóstico sem que uma ferramenta (CloudWatch, SQL) tenha retornado dados.
2. **Contexto de Negócio:** Sempre cruze falhas técnicas com os Runbooks localizados em `/docs`.
3. **Loop de Feedback:** Se o OpenSRE falhar por falta de permissão, reporte imediatamente para ajuste de IAM.
