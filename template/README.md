# example-mcp

TODO: Strataに何を提供するMCPかを書く。

```text
Strata: 入力 → HTTP MCP /mcp (Bearer認証) → example-mcp (NAS Docker)
                                             ↓ 入力検証・回数予約
                                         OpenAI Responses API
                                             ↓ 簡潔なテキスト
Strata: 結果を使って最終回答
```

## NASでの起動

```bash
cp .env.example .env   # 既存の.envは上書きしない
python -c 'import secrets; print(secrets.token_urlsafe(32))'   # EXAMPLE_MCP_TOKEN用
docker compose config --quiet
docker compose up -d --build
docker compose logs --tail=30 example-mcp
```

LANから使うときは`.env`の`MCP_BIND_IP`と`SERVER_IP`の両方をNASのLAN IPにします。

## Strataへの登録

```json
{
  "mcp_servers": {
    "example-mcp": {
      "url": "http://192.168.0.49:8199/mcp",
      "headers": {"Authorization": "Bearer .envのEXAMPLE_MCP_TOKENと同じ値"}
    }
  }
}
```

## コストと上限

| 環境変数 | 既定値 | 意味 |
|---|---|---|
| `OPENAI_MODEL` | `gpt-4.1-mini` | 使用モデル |
| `EXAMPLE_MAX_OUTPUT_TOKENS` | 800 | 出力上限 |
| `EXAMPLE_MAX_CALLS_PER_WINDOW` / `EXAMPLE_WINDOW_SECONDS` | 3回 / 600秒 | 短時間の回数制限 |
| `EXAMPLE_MAX_CALLS_PER_DAY` | 20 | 1日の回数制限（`EXAMPLE_BUDGET_TIMEZONE`で日付を区切る） |

失敗・タイムアウトも回数に含め、自動再試行しません。使用量DBにアクセスできないときはAPIを呼びません。

## 確認・開発

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
EXAMPLE_MCP_TOKEN=... .venv/bin/python check_mcp.py http://192.168.0.49:8199/mcp            # 課金なし
EXAMPLE_MCP_TOKEN=... .venv/bin/python check_mcp.py http://192.168.0.49:8199/mcp --text "…"  # 課金あり
```
