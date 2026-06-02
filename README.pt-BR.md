# Copilot Memory Setup — Memória Persistente para Qualquer Assistente de Código com IA

> **Um único vault, vários copilots.** Memória persistente de projeto e consciência total de codebase para Cursor, GitHub Copilot, Claude Code e qualquer outro assistente que leia `AGENTS.md` / `CLAUDE.md` / `.github/copilot-instructions.md`.

Setup configurável que transforma o assistente de IA que você usa em um agente com memória de longo prazo e consciência total do seu codebase — sem desperdiçar tokens relendo arquivos. Originalmente criado para o Claude Code; agora generalizado.

🇺🇸 [Read in English](./README.md)

---

## Índice

1. [O Problema](#o-problema)
2. [A Solução (Visão Geral)](#a-solução-visão-geral)
3. [Arquitetura](#arquitetura)
4. [Quick Start](#quick-start)
5. [Parte 1 — Obsidian como Memória Persistente](#parte-1--obsidian-como-memória-persistente)
6. [Parte 2 — Pipeline de Importação de Chats](#parte-2--pipeline-de-importação-de-chats)
7. [Parte 3 — Graphify (Knowledge Graph do Codebase)](#parte-3--graphify-knowledge-graph-do-codebase)
8. [Parte 4 — Adapters por Agente](#parte-4--adapters-por-agente)
9. [Parte 5 — Fluxo de Trabalho Completo](#parte-5--fluxo-de-trabalho-completo)
10. [Troubleshooting](#troubleshooting)

---

## O Problema

Trabalhando com qualquer assistente de IA, dois problemas consomem seus tokens silenciosamente:

**Problema 1 — Amnésia entre sessões.** Toda sessão nova, você precisa re-explicar o projeto: stack, decisões tomadas, bugs em andamento, o que falta fazer. O agente não lembra de nada.

**Problema 2 — Releitura do codebase.** O agente relê seus arquivos a cada sessão para entender a estrutura. Um projeto com ~40 arquivos consome ~20.000 tokens só para se orientar — antes de você fazer a primeira pergunta.

Esses problemas independem do agente. Cursor, Copilot, Claude Code — todos fazem isso.

---

## A Solução (Visão Geral)

Três sistemas complementares:

| Camada | Ferramenta | O que resolve | Custo |
|--------|-----------|---------------|-------|
| Memória persistente | **Vault Obsidian** (Zettelkasten) | Amnésia entre sessões | Gratuito |
| Mapa do código | **Graphify** | Releitura do codebase | Gratuito (modo AST) |
| Histórico de chats | **Pipeline de importação** | Chats perdidos | Gratuito |
| Continuidade | **`/memory-load`** + **`/memory-save`** | Retomar de onde parou | Gratuito |

Mais **adapters** por agente que instalam os arquivos corretos nos lugares corretos (`AGENTS.md`, `.cursor/commands/`, `.github/copilot-instructions.md`, etc.) de modo que todos os agentes leem da mesma fonte da verdade.

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│              VAULT OBSIDIAN (único, compartilhado)           │
│                                                             │
│  AGENTS.md   ← instruções universais (lido por todo agente) │
│  permanent/  ← conhecimento consolidado (Zettelkasten)      │
│  logs/       ← session logs (/memory-save)                  │
│  chats/      ← conversas importadas (por fonte)             │
│    claude-code/  claude-web/  cursor/  copilot/             │
│  graphify/   ← knowledge graphs de codebases                │
│  <projeto>/  ← MOCs, decisões, arquitetura                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
              symlinks / cópias geradas
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌──────────────────────┐        ┌──────────────────────┐
│   REPO DO PROJETO    │        │   ~/.copilot-memory/ │
│                      │        │                      │
│  AGENTS.md           │        │  bin/memory-load     │
│  .cursor/commands/   │        │  bin/memory-save     │
│  .github/prompts/    │        │                      │
│  graphify-out/       │        │  (scripts            │
│                      │        │   determinísticos)   │
└──────────────────────┘        └──────────────────────┘
```

O trabalho do agente é **ler a camada certa primeiro** em vez de reler os arquivos brutos.

---

## Quick Start

```bash
git clone https://github.com/<você>/copilot-memory-setup.git
cd copilot-memory-setup

# Cria o vault + instala adapters para Cursor e Copilot
./install.sh --vault ~/vault --agent cursor --agent copilot

# Depois, para cada repo de projeto:
./install.sh --project ~/repos/meuapp --vault ~/vault --agent cursor --agent copilot

# Adicione os scripts determinísticos ao PATH:
echo 'export PATH="$HOME/.copilot-memory/bin:$PATH"' >> ~/.bashrc
```

Aí no Cursor/Copilot:
- Digite `/memory-load` no início da sessão
- Digite `/memory-save` quando estiver encerrando
- Rode `memory-load` ou `memory-save --slug <slug>` direto do shell

---

## Parte 1 — Obsidian como Memória Persistente

### Conceito

Um vault Obsidian único e centralizado funciona como o "segundo cérebro" do seu assistente. Ele armazena decisões, contexto, progresso e conhecimento de todos os seus projetos. As notas seguem o método Zettelkasten: atômicas (uma ideia por nota), densamente interligadas, com metadados padronizados.

O agente acessa esse vault através do `AGENTS.md` (e, quando relevante, dos arquivos específicos como `CLAUDE.md` ou `.github/copilot-instructions.md` — mas todos eles são symlinks para o mesmo `AGENTS.md`).

### Estrutura Recomendada

```
~/vault/                           # vault único para todos os projetos
├── AGENTS.md                      # symlink → spec/AGENTS.md
├── permanent/                     # notas atômicas consolidadas
├── inbox/                         # captura bruta
├── fleeting/                      # notas temporárias
├── templates/                     # templates de nota
├── logs/                          # session logs globais
├── references/                    # material de referência
├── <projeto>/                     # MOCs e notas por projeto
│   ├── architecture/
│   ├── pipeline/
│   ├── data/
│   ├── features/
│   └── logs/
├── chats/                         # conversas importadas
│   ├── claude-code/
│   ├── claude-web/
│   ├── cursor/
│   └── copilot/
└── graphify/                      # knowledge graphs dos codebases
    └── <projeto>/
```

> **Por que vault único?** Um vault por projeto fragmenta o conhecimento. Com vault único, uma nota sobre "Supabase Auth" é linkada por A e B. O graph view revela conexões entre projetos que você não esperava.

### Setup

O instalador cuida disso de ponta a ponta:

```bash
./install.sh --vault ~/vault --agent cursor --agent copilot
```

Cria a estrutura de pastas, faz o symlink `~/vault/AGENTS.md` → `spec/AGENTS.md` e instala os configs por agente (slash commands, rules, prompt files).

Mais detalhes da estrutura: [`spec/vault-structure.md`](./spec/vault-structure.md).

---

## Parte 2 — Pipeline de Importação de Chats

### Conceito

Seus chats com IA contêm decisões, insights e contexto valiosos que se perdem no histórico. Esse pipeline exporta, processa e importa essas conversas como notas no vault — com frontmatter, tags automáticas e wikilinks para notas existentes.

O `claude_to_obsidian.py` original foi generalizado em `chat_to_obsidian.py` com extractors por fonte:

| `--source` | De onde vêm as conversas |
|---|---|
| `claude-code` | `claude-extract --all` (do `claude-conversation-extractor`) |
| `claude-web` | Extensão de navegador → `.md` em `~/claude-exports/web/` |
| `cursor` | `~/.cursor/projects/*/agent-transcripts/*/*.jsonl` (parser direto) |
| `copilot` | VS Code "Chat: Export" → `.json` em `~/copilot-exports/` |

### Uso

```bash
# Uma fonte
python3 scripts/chat_to_obsidian.py --source cursor --vault-dir ~/vault

# Todas as fontes (padrões cron-friendly)
scripts/sync.sh --vault ~/vault
```

### Cron (diariamente às 22h)

```bash
(crontab -l 2>/dev/null; echo "0 22 * * * $HOME/repos/copilot-memory-setup/scripts/sync.sh") | crontab -
```

### Opções de CLI

| Flag | Descrição |
|------|-----------|
| `--source` | Uma de: `cursor`, `copilot`, `claude-code`, `claude-web` (obrigatório) |
| `--vault-dir` | Caminho do seu vault Obsidian (obrigatório) |
| `--import-dir` | Sobrescreve o diretório de staging (padrões são por fonte) |
| `--dry-run` | Preview sem escrever |
| `--move` | Apaga os originais após importar (só funciona em fontes que possuem arquivos) |
| `--no-wikilinks` | Pula a inserção de wikilinks |

Customize a extração de tags editando o `KEYWORD_TAG_MAP` no topo de `scripts/chat_to_obsidian.py`.

---

## Parte 3 — Graphify (Knowledge Graph do Codebase)

### Conceito

O [Graphify](https://github.com/safishamsi/graphify) transforma seu codebase em um knowledge graph consultável. Em vez do agente reler cada arquivo, ele consulta o grafo — persistente entre sessões, uma fração dos tokens.

- **Código:** processado 100% localmente via AST tree-sitter. Nada sai da sua máquina.
- **Cache:** SHA256 — re-execuções só processam arquivos modificados.
- **Custo:** 0 tokens no modo padrão (AST puro). `--deep` usa LLM para edges semânticos.
- **Linguagens:** 20+ via tree-sitter (Python, JavaScript, TypeScript, Go, Rust, Java, C, C++, Ruby, C#, Kotlin, Scala, PHP, Swift, Lua, Zig, …).

### Setup

```bash
pip install graphifyy

# Instala a skill/integração do Graphify para seu agente:
graphify install --platform cursor    # ou claude, codex, opencode, copilot, ...
```

### Extração

```bash
cd ~/repos/meuapp
graphify extract . --out ./graphify-out
```

Saída:

```
graphify-out/
├── graph.json          # grafo consultável (sempre)
├── graph.html          # viz interativa
├── GRAPH_REPORT.md     # nós principais, métricas
└── cache/              # cache SHA256
```

### Atualize o `.gitignore`

```gitignore
graphify-out/cache/
```

Versione `graph.json` e `GRAPH_REPORT.md` — são úteis para o time.

### Opcional: auto-rebuild

```bash
graphify hook install        # reconstrói a cada commit
graphify watch .             # reconstrói ao salvar (terminal separado)
```

### Regra de Navegação de Contexto (3 camadas)

O `AGENTS.md` instalado pelo installer já inclui essa regra. O agente deve consultar nesta ordem:

1. **Primeiro:** `graphify-out/graph.json` — estrutura do código
2. **Segundo:** o vault — para decisões, progresso, contexto
3. **Terceiro:** só leia o código bruto ao editar, ou quando 1 + 2 não derem a resposta

---

## Parte 4 — Adapters por Agente

Cada agente tem seu próprio instalador que instala os arquivos que ele precisa. Todos leem do mesmo `spec/AGENTS.md`.

### Cursor

```bash
adapters/cursor/install.sh --target vault   --path ~/vault
adapters/cursor/install.sh --target project --path ~/repos/meuapp
```

Arquivos instalados:

| Onde | O quê |
|---|---|
| `<target>/AGENTS.md` | Symlink → `spec/AGENTS.md` (vault) ou pointer gerado (project) |
| `<target>/.cursor/rules/agents.mdc` | Rule `alwaysApply: true` com regras do Zettelkasten |
| `<target>/.cursor/commands/memory-load.md` | Slash command `/memory-load` |
| `<target>/.cursor/commands/memory-save.md` | Slash command `/memory-save` |
| `<target>/.cursor/skills/memory-load/SKILL.md` | Skill auto-trigger (vault only) |
| `<target>/.cursor/skills/memory-save/SKILL.md` | Skill auto-trigger (vault only) |

### GitHub Copilot

```bash
adapters/copilot/install.sh --target vault   --path ~/vault
adapters/copilot/install.sh --target project --path ~/repos/meuapp
```

Arquivos instalados:

| Onde | O quê |
|---|---|
| `<target>/.github/copilot-instructions.md` | Symlink → `spec/AGENTS.md` |
| `<target>/.github/prompts/memory-load.prompt.md` | Prompt file `/memory-load` (VS Code 1.95+) |
| `<target>/.github/prompts/memory-save.prompt.md` | Prompt file `/memory-save` |
| `<target>/AGENTS.md` | Pointer slim (target project apenas) |

> **Aviso sobre Copilot:** o GitHub Copilot é escopado por workspace — não existe localização global de instruções. Você precisa rodar o adapter de project para cada repo. Os scripts shell determinísticos em `~/.copilot-memory/bin/` são a superfície mais confiável para usuários de Copilot.

### Symlinks vs cópias

Por padrão o installer usa symlinks (uma fonte da verdade). Passe `--copy` para gerar arquivos reais com um cabeçalho `<!-- GENERATED -->` — útil no Windows ou quando symlinks não são rastreados pelo seu VCS.

### Adicionando mais agentes

Crie uma pasta `adapters/<nome>/` com um `install.sh` que aceite `--target {vault|project} --path PATH [--copy]`. O `install.sh --agent <nome>` do top-level já vai reconhecer.

---

## Parte 5 — Fluxo de Trabalho Completo

### Sessão típica

```
Abre o agente (Cursor / Copilot / etc.)
    │
    ├── /memory-load                  ← carrega contexto do vault
    │                                   (logs recentes, decisões, graph report)
    │
    ├── Agente consulta graph.json    ← entende a estrutura do código
    │                                   sem reler todo arquivo
    │
    ├── Trabalha no código            ← features, bugs, refactors
    │
    ├── /memory-save                  ← escreve session log + git commit
    │
    └── (grafo reconstruído via hook) ← se rodou `graphify hook install`
```

### Economia por camada

| Camada | Sem | Com |
|--------|-----|-----|
| `/memory-load` | Re-explicar o projeto toda sessão | Agente já tem o contexto |
| Graphify | Reler ~40 arquivos (~20k tokens) | Consultar 1 grafo (~280 tokens) |
| Pipeline de chats | Insights perdidos no histórico | Tudo indexado e buscável |
| `/memory-save` | Esquecer o que foi feito | Histórico completo com wikilinks |

### Filtros no Graph View (Obsidian)

| Filtro | Mostra |
|---|---|
| `path:permanent` | Só notas permanentes |
| `path:graphify` | Só nós de código |
| `tag:chat-import` | Só chats importados |
| `path:chats/cursor` | Só chats do Cursor |
| `-path:graphify -path:chats` | Só o conhecimento curado |

---

## Troubleshooting

**Graph view vazio com filtro aplicado:**
Desative "Orphans" e "Existing files only" no filtro do grafo. Cmd+Q e reabra o Obsidian para forçar reindex.

**Symlinks não seguem no Windows:**
Rode o instalador com `--copy`. Os arquivos são gerados como reais com cabeçalho `<!-- GENERATED -->`. Você precisa rodar `--copy` de novo após mudar o spec.

**`memory-save --check` falha:**
O log está faltando uma das seções (`## What was done`, `## Decisions`, `## Open questions`, `## Next session`) ou o frontmatter. Abra o arquivo em `$VAULT/logs/` e adicione o que falta.

**Comandos do Cursor não aparecem:**
Garanta que o workspace aberto é o vault ou o projeto onde rodou o installer. O Cursor lê `.cursor/commands/` relativo ao workspace aberto. Reinicie o Cursor após instalar.

**Copilot não pega `.github/copilot-instructions.md`:**
O arquivo é escopado por workspace. Confirme que você está numa pasta que tem o arquivo na raiz (ou um nível abaixo). Ative a configuração do Copilot Chat "Use Instructions Files" e recarregue a janela.

**Extractor do Cursor não encontra nada:**
Os transcripts do Cursor ficam em `~/.cursor/projects/*/agent-transcripts/*/*.jsonl`. Se o caminho for diferente na sua instalação, passe `--import-dir <root>` para sobrescrever.

**Extractor do Copilot não encontra nada:**
Você precisa exportar os chats manualmente: Command Palette → "Chat: Export" → salve o `.json` em `~/copilot-exports/`. Então rode `chat_to_obsidian.py --source copilot`.

**Cron não roda no macOS:**
Conceda Full Disk Access ao seu terminal (ou ao `cron`) em System Preferences → Privacy & Security.

**Graphify não gera wiki:**
A pasta `wiki/` só é produzida pela forma de skill com `--wiki`. O `graphify extract` headless não expõe isso. Use `graphify query "pergunta"` contra `graph.json`, ou rode a forma de skill.

**Arquivos com parênteses no nome:**
O Graphify gera notas tipo `myFunction().md`. O Obsidian sofre com `()`. Renomeie em batch:
```bash
cd ~/vault/graphify/<projeto>
for f in *"("*; do mv "$f" "$(echo "$f" | sed 's/[()]//g')"; done
```

---

## Layout do Repo

```
copilot-memory-setup/
├── spec/                          # fonte da verdade (tool-agnostic)
│   ├── AGENTS.md
│   ├── vault-structure.md
│   └── commands/{memory-load,memory-save}.md
├── adapters/                      # instaladores por ferramenta
│   ├── cursor/
│   └── copilot/
├── scripts/
│   ├── chat_to_obsidian.py        # importador generalizado
│   ├── extractors/                # extractors por fonte
│   ├── sync.sh                    # wrapper cron-friendly
│   ├── bin/{memory-load,memory-save}  # scripts determinísticos
│   ├── claude_to_obsidian.py      # mantido para compat
│   └── sync_claude_obsidian.sh    # mantido para compat
├── install.sh                     # dispatcher top-level
└── README.md
```

---

## Créditos & Links

- [Graphify](https://github.com/safishamsi/graphify) — knowledge graphs de codebase (MIT)
- [Obsidian](https://obsidian.md) — PKM e segundo cérebro (gratuito)
- [Cursor](https://cursor.sh), [GitHub Copilot](https://github.com/features/copilot), [Claude Code](https://docs.anthropic.com) — os agentes que esse setup mira
- Inspirado pelo sistema do Andrej Karpathy e pela comunidade r/ClaudeAI

---

**Se este setup te ajudou, dá uma ⭐ no repo e compartilha com outros devs.**
