# Roteamento de motor por tipo de asset

Esta é a fonte única da recomendação de motor para `generate_image`.

| tipo de asset | motor | motivo |
|---|---|---|
| sprite de personagem / pixel art | `grok` | Sai nítido, "sprite-like", ganha do Codex (testado). |
| retrato | `codex` | Melhor coerência e detalhe. |
| ilustração detalhada | `codex` | Melhor coerência e detalhe. |
| cena | `codex` | Melhor coerência e detalhe. |
| slide de deck | `codex` | Sem teste comparativo com Grok neste repo; fica no default até haver evidência. |
| criativo social | `codex` | Sem teste comparativo com Grok neste repo; fica no default até haver evidência. |
| infográfico | `codex` | Sem teste comparativo com Grok neste repo; fica no default até haver evidência. |

O motor padrão da tool quando `engine` é omitido é o default `codex`; a tool não faz fallback entre motores.

Esta tabela é a recomendação padrão; pedido explícito do usuário vence, sem pergunta.
