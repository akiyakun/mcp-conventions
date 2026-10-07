"""List tools without API charges. --text explicitly performs one paid call."""
import argparse
import asyncio
import os

import httpx2 as httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

TOOL = "example_tool"


class ToolCallFailed(RuntimeError):
    pass


def diagnose(error: BaseException) -> str:
    """Describe known failures without printing headers, URLs or response bodies."""
    if isinstance(error, BaseExceptionGroup):
        return "\n".join(dict.fromkeys(diagnose(e) for e in error.exceptions))
    if isinstance(error, ToolCallFailed):
        return "MCP接続は成功しましたが、ツールがエラーを返しました。上のツールメッセージを確認してください。"
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        hints = {
            401: "EXAMPLE_MCP_TOKENがNASの設定と一致しているか確認してください。",
            403: "Origin検証またはアクセス制限で拒否されました。",
            404: "接続先のパスが/mcpか確認してください。",
            421: "SERVER_IPまたはMCP_ALLOWED_HOSTSに接続先のNAS IP・ホスト名を設定してください。",
        }
        return f"HTTP {status}: " + hints.get(status, "サーバーの状態を確認してください。")
    if isinstance(error, httpx.TimeoutException):
        return "接続または応答がタイムアウトしました。NASの状態・通信経路を確認してください。"
    if isinstance(error, httpx.ConnectError):
        return "NASへ接続できません。コンテナの起動・公開ポート・MCP_BIND_IP・ファイアウォールを確認してください。"
    return "MCP接続またはツール呼び出しに失敗しました。依存ライブラリのバージョンとサーバー状態を確認してください。"


async def check(args):
    token = os.environ.get("EXAMPLE_MCP_TOKEN", "")
    if not token:
        raise SystemExit("EXAMPLE_MCP_TOKENを環境変数に設定してください。")
    async with httpx.AsyncClient(headers={"Authorization": "Bearer " + token}, timeout=60, trust_env=False) as client:
        async with streamable_http_client(args.url, http_client=client) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
                if [tool.name for tool in listed.tools] != [TOOL]:
                    raise RuntimeError("Unexpected tool list")
                print("接続OK:", TOOL)
                if args.text:
                    result = await session.call_tool(TOOL, {"text": args.text})
                    for content in result.content:
                        if content.type == "text":
                            print(content.text)
                    if result.is_error:
                        raise ToolCallFailed()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="http://NAS-IP:8199/mcp")
    parser.add_argument("--text", help="API送信・課金あり: ツールへ渡す入力")
    try:
        asyncio.run(check(parser.parse_args()))
    except Exception as exc:
        raise SystemExit(diagnose(exc)) from None
