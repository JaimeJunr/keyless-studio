---
name: sprite
description: Gera assets 2D de jogo game-ready — personagens, sprite sheets animados (idle/walk/run/attack), tilesets, itens/ícones e UI — via Codex (keyless), com pós-processamento (remoção de fundo → alpha, montagem de sheet+JSON). Base pai estilo-agnóstico; o estilo (pixel art, cartoon, realista) vem dos plugins especialistas keyless-pixel/keyless-cartoon/keyless-realistic. Depende do keyless-image e de Pillow.
---

# keyless-sprite:sprite — assets 2D de jogo

Base pai de **game dev** do keyless-studio. Gera qualquer asset 2D — personagem, sheet animado, tileset, item, UI — via Codex (keyless) e pós-processa com o script empacotado. É **estilo-agnóstico**: o bloco de estilo entra como parâmetro; as especializações (`keyless-pixel`, `keyless-cartoon`, `keyless-realistic`) só trocam esse bloco e os parâmetros de pós.

## Regras de fluxo (invioláveis)

1. **Entreviste ANTES de gerar.** Nunca gere sem briefing: uso · estilo · resolução/detalhe · paleta · enquadramento. Gerar sem alinhar dá resultado vago. Conduza via `/keyless-sprite:new` ou pergunte direto — e só então gere.
2. **Você dita a ordem de produção — não pergunte ao usuário "em que ordem fazer".** Sprite sheet multi-direcional animado segue SEMPRE: **design lock** (âncora idle de 1 direção → aprovar já no tamanho real) → **direção-piloto** (1 direção inteira: walk+attack, medir consistência) → **escalar** as demais direções por edit referenciado → **pós** → **retoque**. Nunca gere dezenas de frames antes de travar o design.
3. **Moderação/IP: contorne ANTES, não depois.** O gpt-image-2 recusa personagens protegidos (Zelda/Link, Mario, Pokémon, etc.). Não faça gere→falhe→ajuste: avise o usuário e já proponha um design original no mesmo gênero desde o primeiro prompt.
4. **Sprite pequeno = prompt de sprite, não ilustração.** Para ≤64px siga a **Receita de sprite pequeno** (`references/sprites.md`): personagem preenche o frame · silhueta forte com elementos nomeados · cores chapadas de alto contraste · formas chunky · chibi/overhead · negativos (no blur/AA/gradient). Downscale `nearest` (default, crisp) pra sprite; `box` só pra arte hi-res detalhada (retrato) — em sprite chunky o box borra.

## Pré-requisitos

- Skill `keyless-image` (motor keyless via Codex). Sem Codex → entregue os **prompts** dos assets pro usuário rodar no chatgpt.com/images; não trave.
- `pip install Pillow` (pro pós-processamento: `scripts/spritekit.py`).

## Fluxo estágio-a-estágio (não gere tudo de cara)

Gerar 12 frames antes de alinhar estilo = retrabalho caro. Confirme em etapas.

### 1. Briefing
Descubra: **tipo** (personagem/sheet/tileset/item/ui), **vista** (side/top-down/isometric — escolha UMA), **estilo** (delegue ao especialista se for pixel/cartoon/realista), **tamanho** alvo, **destino** de engine (Unity/Godot). Consulte `references/sprites.md`.

### 2. Bloco de estilo
Monte o bloco de estilo (do plugin especialista ou do guia de marca) + a vista. Repita esse bloco **idêntico** em todo prompt — é o que dá coesão.

### 3. Âncora (1 asset) — trava de qualidade
Gere **só a pose-âncora** (personagem neutro / 1 tile / 1 ícone) via `keyless-image:generate`, fundo chroma sólido (`solid bright green background`). Mostre. Só avance quando o usuário aprovar estilo + silhueta + leitura.

### 4. Derivar
- **Animações**: cada frame por **edição referenciada** — `keyless-image:edit` a partir da âncora (`input_images`), NÃO geração nova. Trave frame size, baseline dos pés, altura de cabeça/ombros. Frame counts em `references/sprites.md`.
- **Tileset/itens**: gere em grid único (ex: vários ícones numa linha) pra manter estilo.
- Salve os frames em `<projeto>/frames/` com naming `{entity}_{action}_{NN}.png`.

### 5. Pós-processamento (`spritekit.py`)
```
# 1) fundo chroma → alpha, SEM halo. shrink 1 (não 2: 2 come o outline); defringe descasca a borda contaminada
python "${CLAUDE_PLUGIN_ROOT}/scripts/spritekit.py" keyout frame.png frame.png --corners --tol 60 --defringe 2 --shrink 1
# (use --key RRGGBB pra cor exata; fundo chroma que NÃO exista no personagem — magenta p/ herói verde/prata)
# 1b) pixelizar: --outline RECONSTRÓI a borda preta (coesão de sprite + conserta o que o keyout comeu);
#     --downscale nearest (crisp, sprite); --no-upscale gera o asset REAL (48x48); --scale N só p/ preview
python "${CLAUDE_PLUGIN_ROOT}/scripts/spritekit.py" pixelate frame.png sprite_48.png --grid 48 --palette <nome|arquivo.gpl> --downscale nearest --remove-aa --outline --no-upscale
# ENTREGÁVEL = o asset real (--no-upscale, ex. sprite_48.png = 48x48). Gere TAMBÉM um preview ampliado
# (mesmo comando com --scale 6 → sprite_48_preview.png) e DEIXE CLARO ao usuário: o preview (288x288) é
# só pra visualizar na tela; quem vai pro jogo é o sprite_48.png (48x48). Nunca entregue só o preview.

# 2) montar sprite sheet + JSON (--engine ajusta o preset de import)
python "${CLAUDE_PLUGIN_ROOT}/scripts/spritekit.py" sheet <projeto>/frames <projeto>/sheet.png --cols 6 --padding 1 --json --engine unity

# 3) (opcional) GIF animado pra revisar o ciclo
python "${CLAUDE_PLUGIN_ROOT}/scripts/spritekit.py" gif <projeto>/frames <projeto>/preview.gif --fps 8
```
O subcomando `pixelate` (downscale nearest + quantize de paleta, com backend Aseprite opcional) é usado pelo especialista `keyless-pixel`. `--engine` aceita `aseprite`/`unity`/`godot`/`texturepacker`.

## Atalhos (slash commands)

`/keyless-sprite:new [tipo]` inicia o fluxo; `/keyless-sprite:export [sheet|gif|pixelate]` empacota; `/keyless-sprite:setup` configura o Aseprite; `/keyless-sprite:palette` lista as paletas.

## Animação (leia antes de tentar animar)

O generate **não anima de forma coordenada** (dá "samba") — detalhes e alternativas testadas em `references/sprites.md`. Regras:
- Escolha o engine pelo asset conforme `references/engine-routing.md` do keyless-image.
- Pra walk cycle **keyless**: `spritekit.py walkgen <sprite_48.png> <dir> --frames 4` (deslocamento procedural; ritmo por código, mecânico — refine no Aseprite). Não tente animar por N `generate`/`edit` independentes.
- O forte do generate é o **sprite estático** (âncora, pose única, item, tile). Direcione o esforço pra lá.

### 6. Reportar
Caminhos finais, o tipo/vista/estilo, e o preset de import da engine (Point/Nearest, PPU, sem compressão) — ver `references/sprites.md`.

## Estrutura de saída (por asset)

```
<base>/<nome>/
├── anchor.png          # pose-âncora aprovada
├── frames/             # {entity}_{action}_{NN}.png (fundo já removido)
├── sheet.png           # sprite sheet montado
└── sheet.json          # metadata estilo Aseprite (frames + meta)
```

## Nunca

- Gerar todos os frames antes de aprovar a âncora (estágio 3).
- Gerar animação por N imagens independentes — usa edição referenciada (senão dá wobble/flicker).
- Misturar vistas (top-down + isometric no mesmo asset).
- Entregar sprite com fundo branco/sólido colado — sempre `keyout` pra alpha.
- Afirmar que está pronto pra engine sem o usuário revisar leitura e consistência.
