---
name: handoff
description: Edição e animação AVANÇADA de sprite (walk cycle real, retoque pixel-a-pixel, separar partes em layers) fazendo o handoff do sprite gerado pro pixel-plugin (Aseprite via MCP). Use quando o walkgen procedural não basta e você precisa de animação/edição de verdade. Depende do pixel-plugin instalado + Aseprite; degrada pro keyless-sprite:sprite + walkgen quando ausente.
---

# keyless-sprite:handoff — edição/animação avançada via Aseprite

O generate (Grok/Codex) é **forte em sprite estático** e **fraco em animação coordenada** (ver `references/sprites.md`). Quando você precisa de **walk cycle de verdade**, retoque pixel-a-pixel, ou separar partes em layers, o caminho geral e reutilizável é o **[pixel-plugin](https://github.com/willibrandon/pixel-plugin)** (motor `pixel-mcp` dirigindo o **Aseprite** headless — ~50 tools de draw/layers/frames/cels/quantize/dither/animação/export). Ele opera no **documento** (layer→frame→cel), não na silhueta, então funciona em qualquer sprite — sem heurística que quebra no próximo.

## Arquitetura (3 camadas)

```
1. GENERATE (keyless)   keyless-image (motor conforme `references/engine-routing.md` do keyless-image)   [o estático]
2. POST leve (keyless)  spritekit.py → keyout, pixelate, paleta, sheet, gif  [cola barata]
3. EDIT/ANIMATE (geral) pixel-plugin (pixel-mcp + Aseprite) → import → layers → frames/offset → export
```

O `walkgen` (deslocamento procedural) fica como **atalho** pra walk rápido/mecânico; a camada 3 é o caminho de qualidade.

## Pré-requisitos

- **pixel-plugin instalado** no Claude Code (`/plugin`), expondo as tools `mcp__aseprite__*` (`import_image`, `add_layer`, `draw_pixels`, `duplicate_frame`, `link_cel`, `move_selection`, `apply_shading`, `export_spritesheet`, …).
- **Aseprite** configurado em `~/.config/pixel-mcp/config.json` → `{"aseprite_path": "…"}` (instalação Steam em disco custom vale o caminho absoluto, ex.: `.../SteamLibrary/steamapps/common/Aseprite/aseprite`).
- Sem o pixel-plugin/Aseprite → **degrade**: entregue o sprite estático (`keyless-sprite:sprite`) + `walkgen` procedural, e diga que a edição avançada precisa do pixel-plugin.

## Fluxo de handoff

1. **Gere o estático** (camada 1): `keyless-image:generate` com `engine: grok` (sprite) → PNG.
2. **Pós leve** (camada 2): `spritekit.py keyout --defringe --shrink 1` + `pixelate --grid N --outline --no-upscale` → o `sprite_N.png` limpo.
3. **Handoff pro pixel-plugin** (camada 3), via as tools `mcp__aseprite__*`:
   - `create_canvas` → `import_image` o sprite numa layer.
   - Para animar: separe as partes que se movem em **layers** (ex.: pernas), `duplicate_frame` por keyframe do walk (contact/passing/contact), mova o cel das pernas por offset em arco (`move_selection`/cel offset) + body bob — o modelo de walk está em `references/sprites.md`.
   - Retoque: `draw_pixels`, `apply_shading`, `apply_outline`, `suggest_antialiasing`.
   - `export_spritesheet` → PNG + JSON pronto pra engine.
4. **Volte pro spritekit** se precisar de paleta fixa / GIF de preview / naming de engine.

## Nunca

- Reimplementar as 50 tools do pixel-mcp no `spritekit` (é reinventar a roda — o `spritekit` é só a cola barata keyless).
- Prometer walk cycle "incrível" via generate puro (não coordena tempo) nem via `walkgen` (mecânico). Animação de qualidade = camada 3 (Aseprite) ou desenho humano.
