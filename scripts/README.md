# Scripts

Scripts auxiliares para o setup Claude Code + Obsidian + Graphify.

## Arquivos

| Arquivo | Propósito |
|---------|-----------|
| `claude_to_obsidian.py` | Processa chats exportados do Claude e importa para seu vault Obsidian com frontmatter, auto-tags e wikilinks |
| `sync_claude_obsidian.sh` | Wrapper de automação: exporta os chats do Claude Code e roda o processador |

## Setup

1. **Copie os dois arquivos para `~/scripts/`:**

   ```bash
   mkdir -p ~/scripts
   cp claude_to_obsidian.py ~/scripts/
   cp sync_claude_obsidian.sh ~/scripts/
   chmod +x ~/scripts/sync_claude_obsidian.sh
   ```

2. **Instale o extrator do Claude Code:**

   ```bash
   pip install claude-conversation-extractor
   ```

3. **Edite o `sync_claude_obsidian.sh`:**

   Abra o arquivo e altere `VAULT_DIR` para apontar para o seu vault Obsidian:

   ```bash
   VAULT_DIR="$HOME/NomeDoSeuVault"
   ```

4. **Customize as tags (opcional):**

   Abra `claude_to_obsidian.py` e edite o dicionário `KEYWORD_TAG_MAP` no topo do arquivo. Adicione palavras-chave específicas da sua stack e dos seus projetos:

   ```python
   KEYWORD_TAG_MAP = {
       "meu-projeto": "meu-projeto",
       "nome-cliente": "trabalho-cliente",
       # ... suas palavras-chave
   }
   ```

5. **Teste manualmente:**

   ```bash
   ~/scripts/sync_claude_obsidian.sh
   ```

   Verifique o log:
   ```bash
   tail -f ~/scripts/claude_obsidian_sync.log
   ```

6. **Agende via cron (diariamente às 22h):**

   ```bash
   (crontab -l 2>/dev/null; echo "0 22 * * * $HOME/scripts/sync_claude_obsidian.sh") | crontab -
   ```

## Como funciona

1. `sync_claude_obsidian.sh` roda o `claude-extract` para exportar todas as conversas do Claude Code como arquivos `.md` em `~/claude-exports/code/`
2. Chats da Web podem ser exportados manualmente via extensão de navegador **"Export Claude Chat to Markdown"** para `~/claude-exports/web/`
3. `claude_to_obsidian.py` processa cada `.md`:
   - Detecta a origem (Code vs Web)
   - Gera auto-tags via keyword matching
   - Adiciona frontmatter YAML padronizado
   - Insere `[[wikilinks]]` para notas que já existem no seu vault
4. Os arquivos são movidos (com a flag `--move`) para `<vault>/chats/code/` ou `<vault>/chats/web/`

## Opções de CLI

```bash
python3 claude_to_obsidian.py \
    --export-dir ~/claude-exports \
    --vault-dir ~/ObsidianVault \
    --move
```

| Flag | Descrição |
|------|-----------|
| `--export-dir` | Diretório com os arquivos `.md` exportados (obrigatório) |
| `--vault-dir` | Caminho para o seu vault Obsidian (obrigatório) |
| `--dry-run` | Mostra o que aconteceria sem modificar nada |
| `--move` | Apaga os originais após copiar (padrão: só copia) |
| `--origin` | Força a origem: `code`, `web` ou `auto` (padrão: `auto`) |
| `--no-wikilinks` | Desativa a inserção de wikilinks |

## Filtros no Graph View do Obsidian

Após a importação, use esses filtros:

- `tag:chat-import` → apenas chats importados
- `path:chats` → todos os chats agrupados por pasta
- `-path:chats` → esconde todos os chats
- `tag:python tag:chat-import` → apenas chats relacionados a Python

## Troubleshooting

**`claude-extract` não encontrado:**
Instale com `pip install claude-conversation-extractor`. Se mesmo assim não for encontrado, verifique se o diretório `bin` do pip está no seu `$PATH`.

**Cron não roda no macOS:**
Conceda Full Disk Access ao `cron` em System Preferences → Privacy & Security → Full Disk Access.

**Nenhuma tag sendo gerada:**
Verifique se o `KEYWORD_TAG_MAP` em `claude_to_obsidian.py` contém palavras-chave que realmente aparecem nos seus chats. Rode com `--dry-run` para debugar.

**Wikilinks não inseridos:**
O script só insere wikilinks para notas que já existem no seu vault. Garanta que o `--vault-dir` aponta para um vault com notas (não para uma pasta vazia).
