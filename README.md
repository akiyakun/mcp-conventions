# mcp-conventions

Strata 向け自作MCP（`websearch-mcp`、`vision-mcp` など）の共通規約・ひな形・同期スクリプトです。
各MCPは別々のリポジトリのまま、AI向けの共通ルールをここで一元管理します。

```text
/Volumes/docker/
├─ mcp-conventions/        ← このリポジトリ（正本）
│  ├─ CONVENTIONS.md       ← 全MCP共通の規約
│  ├─ template/            ← 新規MCPのひな形（そのままテストが通る）
│  ├─ sync.py              ← 共通規約の反映・差分確認・新規作成
│  └─ tests/
├─ websearch-mcp/
│  ├─ AGENTS.md            ← 固有情報 + 共通規約の写し（マーカー内）
│  └─ CLAUDE.md            ← "@AGENTS.md" の1行
└─ vision-mcp/ (同じ)
```

## 仕組み

- 各リポジトリの `AGENTS.md` には、次のマーカーで囲まれた範囲があります。

  ```markdown
  <!-- BEGIN mcp-conventions: sync.py が管理。この範囲は直接編集しない -->
  …CONVENTIONS.md の写し…
  <!-- END mcp-conventions -->
  ```

- `sync.py` はこのフォルダーと同じ階層（`/Volumes/docker/*/AGENTS.md`）を探し、マーカー内だけを書き換えます。マーカーの外（固有情報）には触れません。マーカーの無いリポジトリは対象外です。
- `CLAUDE.md` は `@AGENTS.md` の1行で、Claude Code は AGENTS.md の内容を読み込みます。Codex などは AGENTS.md を直接読みます。
- 写しにしているのは、リポジトリ単体で clone しても規約が読めるようにするためです。

## 使い方

Python 3.10以上（標準ライブラリのみ）。

```bash
# 共通規約を直したら、全リポジトリへ反映
python3 /Volumes/docker/mcp-conventions/sync.py

# 反映漏れの確認（書き換えない。古いと終了コード1）
python3 /Volumes/docker/mcp-conventions/sync.py --check

# 新しいMCPをひな形から作る（../translate-mcp を作成）
python3 /Volumes/docker/mcp-conventions/sync.py new translate --port 8105
```

`new` は名前を置き換えてコピーします：`example-mcp` → `translate-mcp`、`example_mcp` → `translate_mcp`、`EXAMPLE_` → `TRANSLATE_`、`8199` → 指定ポート。既存フォルダーは上書きしません。CONVENTIONS.md のポート表で使用済みのポートは拒否します。作成後に次の作業をします。

1. `CONVENTIONS.md` のポート表に追記して `sync.py` を再実行
2. `example_tool`・指示文・`TODO` を実際の機能に置き換える
3. `git init`、GitHub に `akiyakun/<name>-mcp` を作成して push

## 規約を変えるとき

1. `CONVENTIONS.md` を編集（ひな形に関わる場合は `template/` も）
2. `.venv/bin/python -m unittest discover -s tests -v`（ひな形から作ったMCPのテストが通ることも確認します。`.venv` は `python3 -m venv .venv && .venv/bin/python -m pip install -r template/requirements.txt` で作成）
3. `python3 sync.py` で反映し、各リポジトリの AGENTS.md の変更をそれぞれコミット

リポジトリ固有の情報は各リポジトリの AGENTS.md のマーカーの外に書きます。
