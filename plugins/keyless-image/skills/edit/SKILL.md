---
name: edit
description: Edita uma imagem existente via polyagent-mcp → Codex (gpt-image-2) ou Grok (grok-4.5-build), sem API key — trocar fundo, remover/adicionar objeto, mudar cor/estilo, inserir logo/texto, gerar variação a partir de referência. Use quando já existe uma imagem e o usuário quer ALTERÁ-la. Para criar do zero, use a skill generate.
---

# keyless-image:edit — editar imagem keyless via polyagent-mcp → Codex ou Grok

Transforma uma imagem existente via a tool **`generate_image`** do MCP `polyagent`. **Sem API key.**

## Pré-requisito

Servidor MCP `polyagent` configurado globalmente no Claude Code e disponível, com **pelo menos um** dos dois motores instalado: Codex CLI ou Grok.

⚠️ **A tool não faz fallback entre motores.** Omitir `engine` usa o default `codex`; se o Codex não estiver instalado, a chamada **falha** em vez de tentar o Grok. Com só um motor disponível, passe `engine` explicitamente (`engine: grok` quando o Codex faltar). Verifique antes de chamar — o bridge checa a presença do binário, não o login, então um CLI instalado e deslogado passa o guard e falha depois.

Se **nenhum** motor estiver disponível: monte o **prompt de edição** e diga "cole no chatgpt.com/images **junto com a imagem original**". Não trave.

## Fluxo

### 1. Entender o ponto de partida
Peça o caminho da imagem original (e referências, se houver: logo, foto de produto). O modelo precisa do arquivo de origem.

### 2. Prompt de edição — Keep / Change / Do not
Ordem que preserva o que importa:
```
Edit this image. Keep: <o que preservar — sujeito, enquadramento, identidade do produto, texto>.
Change: <a alteração única e específica>.
Style: <paleta em cores reais, iluminação, mood on-brand>.
Do not: <itens do "o que NÃO fazer" do guia de estilo>.
```
- **Uma alteração por vez.** Trocar fundo + remover objeto + mudar cor num prompt só sai impreciso — encadeie: edita, salva, edita de novo.
- Preserve invariantes agressivamente (rosto/texto/marca não mudam salvo se pedido).

### 3. Editar via `generate_image` ⚠️
Chame a tool **`generate_image`** com:
- **`input_images`**: array com os caminhos das imagens de origem.
- **`description`**: o prompt Keep/Change (§2).
- **`out_path`**: um **arquivo novo** (não sobrescreva o original) relativo ao cwd do projeto — versione (`-v2`, `-v3`). A tool salva **direto** nesse caminho e retorna só o path final.
- **`engine`**: `codex` (default) ou `grok`. Ambos keyless. Só esses dois valores — o enum da tool é `z.enum(["codex","grok"])`.
  - Regra por tipo de asset: `references/engine-routing.md`.

**Modo prompt** (modo da *skill*, não parâmetro da tool): curto-circuita *antes* da chamada a `generate_image` e entrega o prompt pronto — mesmo com motor instalado e funcionando. **Não é um terceiro valor de `engine`.** Sem MCP (Pré-requisito) também cai neste modo.

### 4. Iterar
Se desviou do que devia ficar, **reforce o "Keep:"** e tente de novo, uma mudança por vez.

### 5. Reportar
Caminho final no projeto + prompt usado + o motor efetivamente usado (`codex` ou `grok`, via polyagent-mcp). Não afirme perfeição; ofereça 1 ajuste.

## Nunca

- Alteração destrutiva no original (sempre salve cópia nova).
- Usar `out_path` fora do cwd do projeto.
- Editar rosto/pessoa de forma enganosa; usar imagem de terceiro sem autorização (direito de imagem / LGPD).
