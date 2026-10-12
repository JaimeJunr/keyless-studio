---
name: generate
description: Gera imagem (bitmap) dentro do Claude Code via polyagent-mcp → Codex (gpt-image-2) ou Grok (grok-4.5-build), sem API key. Use quando o usuário quer CRIAR uma imagem nova — foto, ilustração, mockup, capa, textura, slide-imagem. Salva no projeto via out_path. Para EDITAR imagem existente, use a skill edit. Para vetor/HTML/CSS, não use esta skill.
---

# keyless-image:generate — gerar imagem keyless via polyagent-mcp → Codex ou Grok

Cria imagem bitmap via a tool **`generate_image`** do MCP `polyagent` (`image_gen` / gpt-image-2 no Codex, grok-4.5-build no Grok). **Sem API key** — usa a assinatura ChatGPT/Codex ou Grok do usuário. A tool já faz generate-then-move e devolve **só o caminho do PNG salvo** (nunca bytes inline).

## Quando usar / não usar

- **Use** pra criar imagem nova: foto, ilustração, mockup, capa, textura, sprite, slide-imagem, cutout.
- **Não use** pra: editar SVG/vetor/ícone existente, montar UI em HTML/CSS/canvas, ou estender um sistema de logo — isso é código-nativo, não bitmap.

## Pré-requisito

Servidor MCP `polyagent` configurado globalmente no Claude Code e disponível, com **pelo menos um** dos dois motores instalado: Codex CLI ou Grok.

⚠️ **A tool não faz fallback entre motores.** Omitir `engine` usa o default `codex`; se o Codex não estiver instalado, a chamada **falha** em vez de tentar o Grok. Com só um motor disponível, passe `engine` explicitamente (`engine: grok` quando o Codex faltar). Verifique antes de chamar — o bridge checa a presença do binário, não o login, então um CLI instalado e deslogado passa o guard e falha depois.

Se **nenhum** motor estiver disponível:

- Não trave. Gere o **prompt pronto** e diga: "cole no chatgpt.com/images". Informe que configurar o servidor MCP `polyagent` globalmente + logar o Codex CLI **ou** o Grok destrava a geração automática.

## Fluxo

### 1. Contexto de marca (se houver)
Se o projeto tem um guia de estilo (`identidade/design-guide.md`, `DESIGN.md`, ou `references/`), leia: paleta (HEX), estilo de imagem, "o que NÃO fazer". Sem guia, gere neutro e diga que ficou genérico.

### 2. Montar o prompt (estrutura de 5 partes)
Ordem: **sujeito+ação → cenário/ambiente → iluminação → paleta (cores reais, HEX→"warm terracotta") + estilo → composição/enquadramento**. Prosa natural, sem flags.

**Texto dentro da imagem:**
- Literal com marcador: `EXACT TEXT: "Movimento é liberdade"` (aspas duplas).
- Rótulo curto sai quase perfeito; **parágrafo longo tremula** — pra texto longo, gere sem o texto e sobreponha depois (HTML/CSS ou editor).
- Nome de marca difícil: soletre letra a letra.

Mostre o prompt ao usuário **antes** de gerar (pré-aprovação), salvo quando for só preview/brainstorm.

### 3. Gerar via `generate_image` ⚠️
Chame a tool **`generate_image`** com:
- **`description`**: o prompt montado (§2).
- **`out_path`**: destino do PNG **relativo ao cwd do projeto** (ex: `assets/hero.png`, `marketing/imagens/capa.png`). A tool salva **direto** nesse caminho — não há etapa manual de mover de `~/.codex/generated_images`.
- **`engine`**: `codex` (default) ou `grok`. Ambos keyless. Só esses dois valores — o enum da tool é `z.enum(["codex","grok"])`.
  - Regra por tipo de asset: `references/engine-routing.md`.

**Modo prompt** (modo da *skill*, não parâmetro da tool): curto-circuita *antes* da chamada a `generate_image` e entrega o prompt pronto — mesmo com motor instalado e funcionando. **Não é um terceiro valor de `engine`.** Sem MCP (Pré-requisito) também cai neste modo.

O `out_path` **deve** ficar dentro do cwd do projeto (o sandbox do bridge só monta o cwd). A tool retorna **apenas o caminho final salvo**.

**Não** troque de modelo silenciosamente (gpt-image-2 → gpt-image-1.5). Se algo forçar downgrade, pergunte antes.

### 4. Revisar e iterar (1 mudança por vez)
Inspecione: sujeito, estilo, composição, **precisão do texto**, itens a evitar. Ajuste com **uma** mudança alvo e re-cheque — não empilhe 5 mudanças num prompt.

### 5. Reportar
Sempre informe: **caminho final salvo no projeto**, o **prompt final**, e o **motor efetivamente usado** (`codex` ou `grok`, via polyagent-mcp, keyless). Lote = uma chamada por asset.

## Nunca

- Usar `out_path` fora do cwd do projeto.
- Afirmar que ficou perfeito — descreva o que foi pedido e ofereça 1 ajuste.
- Gerar imagem de pessoa real/depoimento sem material autorizado.
- Publicar/entregar como final sem quem decide aprovar (quando houver esse fluxo no projeto).
