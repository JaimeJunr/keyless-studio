# Referência: assets 2D de jogo

Base de convenções pra gerar sprites, sheets, tilesets, itens e UI game-ready via IA. Estilo-agnóstico — o **bloco de estilo** (pixel/cartoon/realista) vem dos plugins especialistas.

## Regra de ouro

O motor (gpt-image-2 via Codex) é ótimo pra **frames isolados e conceito**, fraco em **consistência frame-a-frame**. Trate a saída da IA como *color comp*, não sprite final: gere a **pose-âncora** primeiro, aprove, e só então derive animações **por edição referenciada** (`keyless-image:edit` com `input_images`), nunca N gerações independentes. Pós-processe sempre (script `spritekit.py`).

## Fórmula de prompt

```
[assunto] + [bloco de estilo] + [vista] + [pose/ação] + [tamanho] + [layout se sheet] + [fundo] + [palavras de jogo]
```

Palavras game-ready de alto impacto: `game sprite`, `game asset`, `clean edges`, `hard edges`, `flat lighting`, `isolated`, `transparent background`, `centered composition`. Tokens de layout: `sprite sheet`, `horizontal strip`, `N frames`, `aligned in a row`, `1px padding between frames`, `same character`, `same proportions`. **Nunca** misture tokens contraditórios (`realistic` + `pixel art`, `photographic` + `8-bit`).

## Receita de sprite pequeno (≤64px) — obrigatória

Gerar sprite pequeno via IA + downscale só funciona se o prompt força um **sprite**, não uma ilustração. Personagem pequeno no frame, com shading e detalhe, vira mancha ilegível em 48px. Todo prompt de sprite ≤64px DEVE ter:

1. **Personagem preenche o frame** — `fills most of the frame, large and bold, not tiny`. É o item nº1.
2. **Silhueta forte, elementos nomeados** — cite e peça que sejam claros: `prominent round shield, raised sword, rounded helmet`. Silhueta > detalhe.
3. **Cores CHAPADAS de alto contraste, shading mínimo** — `bold flat high-contrast colors, minimal shading`. Gradiente/shading vira lama no downscale.
4. **Formas chunky, outline grosso** — `simple clean chunky shapes, thick 1-pixel dark outline`.
5. **Chibi + overhead** pra top-down (~2 cabeças de altura, visto de cima).
6. **Negativos sempre** — `no blur, no anti-aliasing, no smooth gradients`.
7. **Fundo chroma que NÃO exista no personagem** (magenta p/ herói prata/azul; verde p/ personagem sem verde).

**Downscale**: `--downscale nearest` (default) pra sprite com cores chapadas — mais crisp e preserva a silhueta. `--downscale box` só pra arte-fonte muito detalhada/ruidosa (retrato hi-res); em sprite chunky o box **borra** e é o errado.

**Pós do sprite (borda limpa)**: `keyout ... --defringe 2 --shrink 1` (shrink 1, não 2 — 2 come o outline) e `pixelate ... --outline` pra **reconstruir a borda preta** — dá coesão de sprite e conserta o contorno que o keyout tirou. Entregue o `--no-upscale` (asset real) + um `--scale` (preview).

**Teto do generate+pós**: reduzir arte hi-res da IA pra ≤48px joga fora detalhe fino — sprite pequeno fica *usável* com a receita acima, mas o pixel-perfect AAA é desenhado/retocado à mão. Subir o grid (64px) recupera muita leitura; abaixo disso, o retoque no editor é o fecho.

## Vista (perspectiva) — escolha UMA e não misture

| Vista | Tokens | Uso |
|---|---|---|
| Side-view | `side view`, `profile`, `platformer sprite` | Plataforma, walk cycle |
| Top-down | `strict top-down view`, `overhead`, `orthographic`, `no perspective` | RPG, twin-stick |
| Isometric | `isometric`, `2:1 perspective`, `diamond grid` | Tático, city-builder |

## Tipos de asset

| Tipo | Estrutura / tokens | Notas |
|---|---|---|
| **Personagem** | pose neutra/turnaround primeiro (`front view, side profile, back view, flat studio lighting`) | Vira referência das animações |
| **Sprite sheet** | `sprite sheet`, `N frames`, `horizontal strip`/`4x2 grid`, `same character`, `aligned` | Ver frame counts abaixo |
| **Tileset** | `tileable`, `seamless edges`, `regular grid`, `no complete map`, `no characters`, `no UI` | Grid fixo (ex: `6 columns × 3 rows`, `32×32`/célula) |
| **Item/ícone** | `game item icon`, `centered`, `bold simple shapes`, `high contrast` | Gere vários numa linha p/ manter estilo |
| **UI** | `pixel/flat UI`, `health bar`, `menu frame`, `9-slice`, `HUD element` | Cantos/bordas separados se for escalar |

## Frame counts típicos (indie)

| Ação | Frames | Timing |
|---|---|---|
| Idle | 2–4 | Loop lento 400–800 ms/frame |
| Walk | 4–6 (16px) / 6–8 (32px+) | Celeste 4, Shovel Knight 6 |
| Run | 6–8 | Mais rápido, não + frames |
| Jump | 3–5 | Anticipation → air → land |
| Attack | 3–6 | Wind-up longo, strike rápido |
| Hit | 2–3 | Curtíssimo |
| Death | 4–10 | One-shot |

Timing **variável por frame** importa mais que contagem alta.

## Consistência entre frames (o problema difícil)

1. **Âncora** — personagem neutro aprovado antes de qualquer animação.
2. **Trava** — mesmo `frame size`, baseline dos pés, altura de cabeça/ombros e props em TODOS os frames. Silhueta/baseline mudando = *wobble/flicker*.
3. **Edição referenciada** — cada pose via `keyless-image:edit` a partir da âncora (`input_images`), não geração nova.
4. **Repita o bloco de estilo** em todo prompt.
5. **Normalize no pós** — bbox, padding 1–2px, downscale nearest, snap ao grid.

## Animação (walk cycle): teto do generate + caminhos — TESTADO

Testado à exaustão (Codex e Grok): **o generate NÃO produz animação coordenada.** Mantém identidade (ótimo), mas não modela sequência temporal. Resultados reais:

- **Frames independentes** (cada frame um `edit` da âncora com pose vaga) → "samba": pernas descoordenadas, sem ritmo. NÃO use pra animação.
- **Sheet único com keyframes NOMEADOS por célula** (top-down: `contact-L / passing / contact-R / passing`; baseline compartilhado; "não espelhe left/right; mude SÓ as pernas") → melhor que frames soltos, mas metade das células tende a repetir. Serve só pra protótipo.
- **`image_to_video`** (o Grok tem a tool built-in) seria o caminho confiável — o movimento nasce no tempo — MAS falha sob **Zero Data Retention** (exige `output.upload_url`): indisponível keyless neste setup.
- **Caminho keyless que funciona**: `spritekit.py walkgen <sprite> <outdir>` — deslocamento procedural das pernas (ritmo por código, não IA). Coordenado, mas **mecânico**; refine no editor/Aseprite. Melhor em sprites simétricos com pernas na faixa inferior.

**O forte do generate é o SPRITE ESTÁTICO** (âncora, pose única, item, tile, turnaround) — aí ele brilha.

## Engine por tipo de asset (`generate_image` param `engine:`)

A regra de roteamento vive em `references/engine-routing.md` do keyless-image.

## Fundo → alpha

gpt-image-2 **não** tem alpha nativo. Gere com **fundo sólido chroma** (`solid bright green background`, `#00FF00`) e remova no pós: `spritekit.py keyout --key 00ff00` (cor exata) ou `--corners` (flood-fill dos cantos). Nunca entregue sprite com fundo branco "colado".

## Sprite sheet / atlas

- **Grid** (strip ou rows×cols) quando frames têm **mesmo tamanho** (animação/tileset): indexação trivial `col=i%cols`, `row=i/cols`.
- **Packed atlas** só pra tamanhos mistos (UI/props) — exige metadata JSON.
- **Padding** 1–2px transparente entre frames evita *texture bleeding*.
- **POT**: a textura/atlas final deve ser potência de 2 (512/1024/2048, ≤2048 mobile); frames individuais não precisam.
- Montagem: `spritekit.py sheet <dir> <out.png> --cols N --padding 1 --json` (gera PNG + JSON estilo Aseprite).

## Naming

`{entity}_{action}_{direction?}_{frame}` com zero-padding: `player_walk_down_004.png`. Lowercase, separador consistente (`_`), números com zeros à esquerda (sort correto). O `spritekit.py` ordena por `natural_key` (`frame_2` antes de `frame_10`).

## Import na engine (pixel art)

| Setting | Unity | Godot 4 |
|---|---|---|
| Filtro | **Point (no filter)** | **Nearest** |
| Compressão | **None** | Lossless / off |
| PPU | 1 PPU = 1 pixel do tile (16 p/ 16×16) | snap de pixel em Project Settings |
| Mipmaps | Off | Off |

Godot 4.2+ importa `.aseprite` nativo; ou dropar PNG+JSON.

## Tilesets

- **16×16** retro/mobile, **32×32** padrão moderno — escolha uma e mantenha.
- **Margin** = offset da borda; **Spacing** = gap entre tiles (extrusão anti-bleed).
- Autotiling: 16-tile (4 vizinhos, blocky) vs **47-tile blob** (8 vizinhos, orgânico). Godot 4 usa **Terrains**.

## Prompts copy-ready

Walk cycle: `pixel art sprite sheet, cyberpunk ninja, running, 6 frames, aligned in a single horizontal row, solid bright green background, 16-bit --ar 3:1`

Tileset top-down: `top-down pixel art tile atlas, 32×32 per tile, 6×3 regular grid, transparent background, tileable grass/dirt/water transitions, strict top-down, no isometric, no characters, no complete map`

Ícones: `row of five game item icons: sword, red potion, shield, gold key, scroll, clean outlines, same visual weight, transparent background`
