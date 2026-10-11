# example-mcp

TODO: このMCPが Strata に何を提供し、何を Strata に任せるかを2〜3行で書く。

## このリポジトリ固有の情報

- 公開ツール: `example_tool(text: str) -> str`（TODO: 実際のツールに置き換える）
- ホスト側ポート: `8199`
- 認証トークン: `EXAMPLE_MCP_TOKEN`
- 固有の環境変数: `EXAMPLE_MAX_OUTPUT_TOKENS` `EXAMPLE_WINDOW_SECONDS` `EXAMPLE_MAX_CALLS_PER_WINDOW` `EXAMPLE_MAX_CALLS_PER_DAY` `EXAMPLE_BUDGET_TIMEZONE`
- 主なファイル: `example_mcp/core.py`（OpenAI呼び出しと指示）、`example_mcp/budget.py`（回数制限）、`example_mcp/config.py`（設定）

### 固有の制約

- TODO: 入力の制限、送ってはいけないデータ、出力の形式など。

### 確認コマンド

```bash
.venv/bin/python -m unittest discover -s tests -v
EXAMPLE_MCP_TOKEN=... .venv/bin/python check_mcp.py http://192.168.0.100:8199/mcp
```

<!-- BEGIN mcp-conventions: sync.py が管理。この範囲は直接編集しない -->
<!-- END mcp-conventions -->
