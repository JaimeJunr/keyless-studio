# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é

`keyless-studio` é um **marketplace de plugins para Claude Code** que adiciona geração visual **keyless** (sem `OPENAI_API_KEY`): imagens, decks `.pptx`, criativos sociais, infográficos e visuais de site. Não é um app — é um catálogo de plugins declarativos (skills em Markdown), com um único script Python executável (`build_pptx.py`). Há uma suíte pytest mínima em `tests/`, configurada em `pyproject.toml`, ainda sem CI. Não há build, lint, `package.json` na raiz nem agents/hooks.

## Arquitetura

A geração de imagem roteia por um MCP externo, não por API key:

```
Claude Code → skill (ex: keyless-deck:deck) → keyless-image:generate
   → MCP global polyagent / tool generate_image → polyagent-mcp
   → codex exec → image_gen (gpt-image-2, keyless) → PNG salvo no cwd do projeto
```

Três camadas de plugins (todas registradas em `.claude-plugin/marketplace.json`):

1. **Motor** — `keyless-image`: única fonte de geração. Usa o servidor MCP `polyagent`, configurado globalmente no Claude Code a partir do projeto `polyagent-mcp`. O plugin não declara MCP próprio; instalar o plugin não registra o servidor. Skills `generate` e `edit`.
2. **Genéricos** — `keyless-deck` (slides→`.pptx`), `keyless-social`, `keyless-infographic`: delegam toda geração ao motor.
3. **Especialistas** — `keyless-biz`, `keyless-study`, `keyless-web`: templates de domínio sobre deck/image.

Dependência entre plugins é real: instalar `keyless-image` **primeiro**; os demais assumem que ele existe.

### Família game dev (base pai + especialistas de estilo)

Padrão distinto da família deck: uma **base pai** genérica carrega o fluxo e o script; **especialistas de estilo** são finos e só herdam.

- **`keyless-sprite`** (base pai, genérico) — fluxo game dev 2D completo (personagens, sprite sheets, tilesets, itens, UI) + o script Python `scripts/spritekit.py`. Estilo-agnóstico.
- **`keyless-pixel` / `keyless-cartoon` / `keyless-realistic`** (especialistas de estilo) — herdam o fluxo `keyless-sprite:sprite`; cada um só troca o **bloco de estilo** (injetado no prompt) e os **parâmetros de pós**. Todos dependem de `keyless-sprite` instalado.

Ao adicionar um **novo estilo** ("e afins"), copie o molde de um especialista: só o bloco de estilo + o pós mudam; nunca reescreva o fluxo nem duplique o script. Pixel usa `pixelate` (grid+paleta); cartoon/realista só `keyout` (fundo→alpha), nunca `pixelate`.

`spritekit.py` (Pillow) subcomandos: `pixelate` (downscale nearest + quantize de paleta), `keyout` (chroma/floodfill → alpha), `sheet` (sprite sheet + JSON, `--engine aseprite|unity|godot|texturepacker`), `gif` (GIF animado), `palettes` (catálogo), `setup` (config do Aseprite). Vive só no `keyless-sprite` — os especialistas o referenciam por dependência, não duplicam.

**Backend Aseprite (opcional, híbrido)**: `pixelate` roteia quantize+dither pro Aseprite headless quando disponível; senão Pillow. `aseprite_bin()` resolve na ordem `ASEPRITE_PATH` → config → PATH → auto-detect Steam (`libraryfolders.vdf`). Nunca duplicar o `pixelate` no Pillow e no Aseprite: o downscale é sempre Pillow, só o quantize/dither troca de motor.

**Dependência em runtime `keyless-sprite` → `keyless-image` (envkit.py)**: `spritekit.py` carrega sob demanda `plugins/keyless-image/scripts/envkit.py` — módulo compartilhado que resolve o config dir e o `ASEPRITE_PATH`/config/Steam de forma portátil entre Linux/macOS/Windows. Só as etapas **config** e **Steam** da cadeia de resolução dependem dele; **env var** (`ASEPRITE_PATH`) e **PATH** usam só `os.environ`/`shutil.which` e continuam funcionando mesmo sem `keyless-image` instalado. Sem `keyless-image`: `setup` falha cedo com mensagem amigável (é o único subcomando que *exige* o envkit); `pixelate` degrada silenciosamente as etapas config/Steam e cai pro Pillow se nenhuma das outras duas resolver o binário; os demais subcomandos (`keyout`, `sheet`, `gif`, `walkgen`, `palettes`) nunca tocam config/envkit. Bibliotecas Steam em disco custom não são catalogadas no `.vdf` → exigem `setup --path` uma vez.

**Paletas** (dict `PALETTES` no script, fonte única): db16, db32, pico8, nes, snes, gameboy, gameboy-gray, c64, cga, sweetie16, gray4/8/16. Adicionar paleta = uma entrada no dict (hex sem `#`).

**Slash commands**: `keyless-sprite/commands/` → `/keyless-sprite:{new,export,setup,palette}`; `keyless-pixel/commands/new.md` → `/keyless-pixel:new`. Comandos que executam o script vivem no `keyless-sprite` (o `${CLAUDE_PLUGIN_ROOT}` resolve o path); comandos de fluxo só disparam a skill.

**Engine de imagem** (`generate_image` param `engine`, no polyagent-mcp): `grok` é keyless via assinatura Grok (modelo grok-4.5-build) e `codex` é o default (gpt-image-2); a regra de roteamento vive em `plugins/keyless-image/references/engine-routing.md`. **Animação**: testado — o generate NÃO anima coordenado ("samba"); walk cycle keyless via `spritekit.py walkgen` (deslocamento procedural, mecânico); `image_to_video` do Grok é bloqueado por Zero Data Retention. O forte do generate é o **sprite estático**. Detalhes em `keyless-sprite/references/sprites.md`.

**Edição/animação avançada (camada 3, geral)**: a skill `keyless-sprite:handoff` faz o handoff do sprite gerado pro **[pixel-plugin](https://github.com/willibrandon/pixel-plugin)** (motor `pixel-mcp` + Aseprite, ~50 tools de layers/frames/cels/draw/quantize/export) — o motor geral e reutilizável pra walk cycle real e retoque pixel-a-pixel (opera no documento, não na silhueta; não quebra no próximo sprite). Keyless com o Aseprite do usuário; config em `~/.config/pixel-mcp/config.json`. **Arquitetura de 3 camadas**: (1) GENERATE keyless (Grok/Codex) → (2) spritekit.py glue (keyout/pixelate/paleta/sheet) → (3) pixel-plugin edição/animação. O `pixel-plugin` é instalado **ao lado** do keyless-studio (não reimplementar suas 50 tools no spritekit). `walkgen` é atalho procedural, não o motor de animação.

## Estrutura de um plugin

```
plugins/<nome>/
├── .claude-plugin/plugin.json    # name, version, description, keywords, author...
├── README.md
└── skills/<skill>/SKILL.md        # frontmatter YAML: name + description
```

Extras: `keyless-image` usa o MCP global `polyagent`, sem `.mcp.json` próprio; `keyless-deck` tem `scripts/build_pptx.py` e `references/estilos.md` (biblioteca de estilos versionada). Skills são invocadas como `<plugin>:<skill>` (ex: `keyless-image:generate`).

Ao **adicionar um plugin**, registre-o também em `.claude-plugin/marketplace.json` — os dois arquivos (o `plugin.json` local e a entrada no marketplace) precisam existir.

## Convenções invioláveis

Estas regras estão codificadas nas skills e o script depende delas:

- **Keyless via bridge**: a geração usa a assinatura ChatGPT/Codex do usuário através do `polyagent-mcp`, nunca `OPENAI_API_KEY` direto.
- **Degradação graciosa**: se o bridge/Codex não estiver disponível, a skill **não trava** — entrega o prompt pronto e instrui "cole no chatgpt.com/images". Preserve esse comportamento em qualquer skill nova.
- **`out_path` sempre dentro do cwd do projeto**: o sandbox do bridge só monta o cwd. A tool `generate_image` salva direto no `out_path` e retorna **apenas o caminho** (nunca bytes inline). Uma chamada por asset.
- **Edição não-destrutiva** (`keyless-image:edit`): passe origens em `input_images`, salve em arquivo novo versionado (`-v2`, `-v3`); nunca sobrescreva o original.
- **Decks** (`keyless-deck`): slides vão para `<projeto>/origin_image/slide_01.png`, `slide_02.png`, … (nomeação numérica obrigatória — `build_pptx.py` ordena por `natural_key`). Nunca deixar PNG só no cache do Codex; nunca gerar todos os slides antes de aprovar a amostra.

## Comando útil

Montar o `.pptx` a partir dos slides gerados (requer `pip install python-pptx`):

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/build_pptx.py" <projeto> --size 16:9|4:3|9:16
```

Lê `<projeto>/origin_image/*.png` (ordenados naturalmente) + `speech.md` opcional (vira notas) e gera `<projeto>/<nome>.pptx`.

Rodar a suíte de testes (requer pytest e Pillow — `spritekit.py` sai com
`sys.exit` no import se Pillow faltar, o que quebra a *coleta*, não só os
testes dele):

```
pip install pytest Pillow
python -m pytest
```

`[dependency-groups]` em `pyproject.toml` documenta a intenção (PEP 735) mas
é decorativo neste ambiente: pip 24.0 não tem `--group` (só a partir do
25.1) e pytest não lê `[dependency-groups]` sozinho — instale manualmente
como acima.

A suíte verifica que nenhuma referência ao nome antigo do bridge permanece no repositório, respeitando as exclusões definidas no teste.

## Pré-requisitos externos (não vivem neste repo)

- Servidor MCP `polyagent` configurado globalmente no Claude Code: clonar `polyagent-mcp`, executar `npm install` e `npm run build`, e registrar `node /caminho/absoluto/para/polyagent-mcp/dist/index.js` no escopo `user` (comando completo no README).
- Codex CLI no PATH e logado.
