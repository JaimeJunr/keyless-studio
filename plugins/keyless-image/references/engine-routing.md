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

## Pedido explícito do usuário

Qualquer pedido claro de motor ou de modo prompt conta. Aceite pedidos em português ou inglês na chamada, por exemplo:

- Motor `codex`: "use codex", "motor codex", "use the codex engine".
- Motor `grok`: "use grok", "motor grok", "use the grok engine".
- Modo prompt: "só o prompt", "modo prompt", "prompt only".

O pedido explícito do usuário vence a tabela, sem pergunta. Não avise que a tabela recomendaria outro motor; apenas informe a origem no relato. Sem pedido explícito, use a tabela por tipo de asset; se o tipo estiver fora da tabela, use o default `codex` da tool. O parâmetro `engine` aceita exatamente `codex` e `grok`.

O modo prompt entrega o prompt pronto, não chama `generate_image` e não gera arquivo, mesmo com os dois motores disponíveis. É escolha, não falha. Vive na skill e não é um terceiro valor de `engine`. Para edição, entregue o prompt de edição pronto e indique a imagem original e as referências que o usuário deve anexar na ferramenta externa (chatgpt.com/images).

Não há preferência persistente: a escolha vale só para a chamada; nada é gravado em disco/config nesta versão.

### Origem da decisão e relato

Use este vocabulário mínimo:

- `pedido explícito`: o usuário pediu `codex`, `grok` ou modo prompt.
- `tabela`: o tipo de asset casou com uma linha da tabela.
- `padrão`: o tipo está fora da tabela; usa o default `codex` da tool.

A detecção e a confirmação antes de trocar de motor pertencem à US-004; quando a troca do Pré-requisito da skill ocorrer, relate a origem como `pré-requisito: Codex ausente`.

Toda geração informa o motor efetivamente usado (`codex` ou `grok`) e a origem da decisão. Exemplo: "Motor: grok; origem: pedido explícito". No modo prompt, informe que nenhum motor foi usado; origem: `pedido explícito` quando solicitado pelo usuário. Se nenhum motor estiver disponível e não houver pedido explícito, entregue o prompt pronto conforme o pré-requisito da skill e informe a indisponibilidade; não atribua a escolha ao usuário.
