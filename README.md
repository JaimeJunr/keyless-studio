# keyless-studio

keyless-studio is a Claude Code plugin marketplace for visual generation with no API key — images, pixel art, sprite sheets for game dev, `.pptx` decks, social creatives, infographics, and site visuals. It routes through the Codex or Grok subscription you already have (via [polyagent-mcp](https://github.com/JaimeJunr/polyagent-mcp)), so there is nothing new to bill. Built for anyone who needs the visual inside the agent, not another dashboard with a billed key.

**Superpoder visual keyless para o Claude Code, via Codex ou Grok.**

O Claude Code não gera pixel. O `keyless-studio` resolve isso ligando o Claude Code ao **Codex** (`image_gen` / gpt-image-2) ou ao **Grok** (grok-4.5-build) pelo **[polyagent-mcp](https://github.com/JaimeJunr/polyagent-mcp)** — gera e edita imagem usando a **sua assinatura ChatGPT/Codex ou Grok, sem API key**. Em cima disso, entrega skills para **pixel art, sprite sheets e assets de game dev 2D**, além de **decks/PowerPoint, criativos sociais, infográficos e visuais de site** — genéricos o suficiente pra qualquer coisa (jogo, trabalho, documento, aula, site) e com pacotes especialistas quando você quer resultado pronto de um domínio.

## Por que

- **Sem API key.** Imagem via Codex ou Grok usa a auth que você já tem (ChatGPT free incluído). Sem `OPENAI_API_KEY`, sem chave de terceiro pra gerenciar.
- **Local e seu.** Decks viram `.pptx` de verdade montado localmente (python-pptx). Imagens e sprites ficam no seu projeto.
- **Genérico + especialista.** Os plugins-base servem pra tudo; os especialistas (negócio, estudo, web, e os estilos de game — pixel, cartoon, realista) dão templates curados por cima.
- **Degrada com elegância.** Sem bridge/Codex/Grok, cai pro fluxo copia-e-cola (prompt pronto pro chatgpt.com/images) ou outro provedor — nunca trava.

## Pré-requisitos

- **Claude Code** (com suporte a plugins/marketplace).
- Servidor MCP **`polyagent`** configurado globalmente no Claude Code (veja abaixo), usando o projeto **[polyagent-mcp](https://github.com/JaimeJunr/polyagent-mcp)**.
- **Codex CLI** instalado e logado (`codex` no PATH) — o bridge chama `codex exec` + `image_gen` (gpt-image-2, keyless).
- **Python 3** + `python-pptx` (só pro `keyless-deck` montar `.pptx`): `pip install python-pptx`.

## Instalação

Instalar o plugin **não instala nem registra o MCP**. Configure o servidor MCP `polyagent` globalmente uma vez, fora deste repo. No terminal, escolha uma pasta permanente para o clone e execute:

```sh
git clone https://github.com/JaimeJunr/polyagent-mcp.git
cd polyagent-mcp
npm install
npm run build
claude mcp add --scope user --transport stdio polyagent -- node "$(pwd)/dist/index.js"
```

O comando registra o servidor na configuração MCP do Claude Code no escopo `user`, disponível em todos os projetos. Mantenha o clone nesse caminho. Reinicie o Claude Code e confira o servidor `polyagent` em `/mcp`; a tool de imagem resolve como `mcp__polyagent__generate_image`. O Codex CLI deve estar instalado e logado para a geração keyless.

Depois, no Claude Code:

```
/plugin marketplace add JaimeJunr/keyless-studio
/plugin install keyless-image@keyless-studio      # motor (instale primeiro)
/plugin install keyless-deck@keyless-studio        # decks/PPT
/plugin install keyless-social@keyless-studio      # criativos sociais
/plugin install keyless-infographic@keyless-studio
/plugin install keyless-biz@keyless-studio         # especialista: negócio
/plugin install keyless-study@keyless-studio       # especialista: estudo
/plugin install keyless-web@keyless-studio         # especialista: site
/plugin install keyless-sprite@keyless-studio      # game dev 2D (base pai)
/plugin install keyless-pixel@keyless-studio       # estilo: pixel art
/plugin install keyless-cartoon@keyless-studio     # estilo: cartoon
/plugin install keyless-realistic@keyless-studio   # estilo: realista
```

Um comando por linha (o Claude Code interpreta slash line-by-line).

## Plugins

| Plugin | Camada | O que faz |
|---|---|---|
| **keyless-image** | motor | Gera/edita imagem via polyagent-mcp → Codex (gpt-image-2, keyless). `out_path` no projeto, texto PT-BR na imagem. Base dos demais. |
| **keyless-deck** | genérico | Deck genérico → slides-imagem → `.pptx`. Trabalho, documento, relatório, aula. |
| **keyless-social** | genérico | Capa de carrossel, story/reel, quote card, criativo de anúncio. |
| **keyless-infographic** | genérico | Número/dado → slide infográfico. |
| **keyless-biz** | especialista | Pitch, deck de vendas, proposta, QBR (templates sobre o `keyless-deck`). |
| **keyless-study** | especialista | Aula, resumo, flashcard, defesa acadêmica. |
| **keyless-web** | especialista | Hero, OG card, ilustração de seção, favicon pra sites. |
| **keyless-sprite** | genérico (base pai) | Game dev 2D: personagens, sprite sheets, tilesets, itens, UI. Pós-processa (fundo→alpha, sheet+JSON) via `spritekit.py`. Estilo-agnóstico. |
| **keyless-pixel** | especialista (estilo) | Pixel art autêntico: grid real, paleta (DB16/PICO-8/NES), pixelate+quantize sobre o `keyless-sprite`. |
| **keyless-cartoon** | especialista (estilo) | Cartoon/toon: cores chapadas, bold outline sobre o `keyless-sprite`. |
| **keyless-realistic** | especialista (estilo) | Realista/painterly: volume, luz, textura sobre o `keyless-sprite`. |

## Como funciona (arquitetura)

```
Claude Code
   │  usa skill (ex: keyless-deck:deck → keyless-image:generate)
   ▼
keyless-image  ──(MCP global polyagent / generate_image)──►  polyagent-mcp
                                                           │
                                                           ▼
                                                     codex exec  ──►  image_gen (gpt-image-2, keyless)
                                                           │
                                                           ▼
                                                     seu projeto (out_path no cwd)
```

Princípios herdados do `image_gen` oficial do Codex e da comunidade: **built-in tool primeiro** (sem chave), **generate-then-move** (a tool salva direto no `out_path` do projeto), **fluxo estágio-a-estágio** (confirma outline/estilo/amostra antes de gerar tudo), e **biblioteca de estilos** versionada em cada plugin (`references/`).

## Créditos e inspiração

- Codex `image_gen` / [imagegen SKILL oficial](https://github.com/openai/codex/blob/main/codex-rs/skills/src/assets/samples/imagegen/SKILL.md)
- [polyagent-mcp](https://github.com/JaimeJunr/polyagent-mcp) (transporte MCP → `codex exec` + `image_gen`)
- [codex-ppt-skill](https://github.com/ningzimu/codex-ppt-skill) (fluxo de PPT como imagens-slide)
- [Claude Code Plugins reference](https://code.claude.com/docs/en/plugins-reference)

## Licença

MIT — veja [LICENSE](LICENSE).
