# keyless-sprite

**Base pai de game dev 2D** do keyless-studio. Gera assets de jogo game-ready — personagens, sprite sheets animados (idle/walk/run/attack), tilesets, itens/ícones e UI — via Codex (keyless) e pós-processa localmente com Pillow.

É **estilo-agnóstico**: o bloco de estilo entra como parâmetro. As especializações de estilo reutilizam este fluxo:

- **`keyless-pixel`** — pixel art autêntico (grid + paleta + pixelate)
- **`keyless-cartoon`** — cartoon/toon (cores chapadas, bold outline)
- **`keyless-realistic`** — realista/painterly

## Skill & comandos

- **`keyless-sprite:sprite`** — fluxo estágio-a-estágio: briefing → estilo → âncora (1 asset) → derivar → sheet + JSON.
- **`keyless-sprite:handoff`** — edição/animação **avançada** (walk cycle real, retoque): faz o handoff pro [pixel-plugin](https://github.com/willibrandon/pixel-plugin) (Aseprite via MCP). Degrada pro `walkgen` procedural sem ele.
- **`/keyless-sprite:new`** · **`/keyless-sprite:export`** · **`/keyless-sprite:setup`** · **`/keyless-sprite:palette`** — atalhos.

## Arquitetura (3 camadas)

1. **GENERATE** (keyless) — `keyless-image` (motor conforme `plugins/keyless-image/references/engine-routing.md`). O estático.
2. **POST leve** (keyless) — `spritekit.py`: keyout, pixelate, paleta, sheet, gif, walkgen.
3. **EDIT/ANIMATE** (geral) — [pixel-plugin](https://github.com/willibrandon/pixel-plugin) (pixel-mcp + Aseprite): layers/frames/cels, walk cycle real, export sheet. Instalado **ao lado**; `keyless-sprite:handoff` orquestra.

## Requisitos

- `keyless-image` instalado (motor keyless via Codex).
- `pip install Pillow` (pós-processamento).
- **Aseprite** (opcional) — caminho de qualidade pra pixel art. Configure com `/keyless-sprite:setup`.

## Pós-processamento (`spritekit.py`)

```
# remover fundo chroma → alpha
python "${CLAUDE_PLUGIN_ROOT}/scripts/spritekit.py" keyout in.png out.png --key 00ff00
# pixel art (grid nearest + quantize; usa Aseprite se configurado, senão Pillow)
python "${CLAUDE_PLUGIN_ROOT}/scripts/spritekit.py" pixelate in.png out.png --grid 32 --palette db16 --dither ordered --scale 8
# sprite sheet + JSON (preset de engine)
python "${CLAUDE_PLUGIN_ROOT}/scripts/spritekit.py" sheet <dir_frames> sheet.png --cols 6 --padding 1 --json --engine unity
# GIF animado do ciclo
python "${CLAUDE_PLUGIN_ROOT}/scripts/spritekit.py" gif <dir_frames> preview.gif --fps 8
# listar paletas / configurar aseprite
python "${CLAUDE_PLUGIN_ROOT}/scripts/spritekit.py" palettes
python "${CLAUDE_PLUGIN_ROOT}/scripts/spritekit.py" setup --detect
```

**Paletas** (`--palette`): `db16`, `db32`, `pico8`, `nes`, `snes`, `gameboy`, `gameboy-gray`, `c64`, `cga`, `sweetie16`, `gray4/8/16`. **Engines** (`--engine`): `aseprite`, `unity`, `godot`, `texturepacker`.

### Aseprite (opcional, caminho de qualidade)

`/keyless-sprite:setup` detecta o Aseprite (PATH ou instalação Steam via `libraryfolders.vdf`) e grava em `~/.config/keyless-sprite/config.json`. Se a biblioteca Steam estiver em disco custom (não catalogada no `.vdf`), rode `/keyless-sprite:setup /caminho/para/aseprite` uma vez. Com Aseprite, o `pixelate` faz quantize indexed + dithering real; sem ele, cai pro Pillow.

## Referências

- [`references/sprites.md`](references/sprites.md) — prompts por tipo de asset, frame counts, naming, sprite sheet/atlas, import Unity/Godot, tilesets.
