import argparse
import hmac
import logging
import os
from ipaddress import ip_address

import uvicorn
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import PlainTextResponse

from example_mcp.config import Settings, integer
from example_mcp.core import run


def create_server(settings: Settings) -> MCPServer:
    mcp = MCPServer("example-mcp", version="0.1.0")

    @mcp.tool()
    async def example_tool(text: str) -> str:
        """TODO: Strataのモデルが読む説明。用途・引数の選び方・やらないことを日本語で簡潔に書く。
        1回の呼び出しで完結させ、失敗や不足時に自動で繰り返し呼び出さない。最終判断はStrataが行う。
        """
        return await run(settings, text)

    return mcp


class BearerAuth:
    def __init__(self, app, token: str):
        self.app, self.expected = app, ("Bearer " + token).encode("ascii")

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            supplied = dict(scope["headers"]).get(b"authorization", b"")
            if not hmac.compare_digest(supplied, self.expected):
                await PlainTextResponse("Unauthorized", status_code=401)(scope, receive, send)
                return
        await self.app(scope, receive, send)


def create_http_app(mcp: MCPServer):
    token = os.environ.get("EXAMPLE_MCP_TOKEN", "")
    if len(token) < 32 or not token.isascii() or any(c.isspace() for c in token):
        raise ValueError("EXAMPLE_MCP_TOKENに空白を含まない32文字以上のASCII文字列を設定してください。")
    hosts = [x.strip() for x in os.environ.get(
        "MCP_ALLOWED_HOSTS", "localhost:*,127.0.0.1:*,[::1]:*"
    ).split(",") if x.strip()]
    if "*" in hosts:
        raise ValueError("MCP_ALLOWED_HOSTSで全ホスト許可は指定できません。")
    server_ip = os.environ.get("SERVER_IP", "").strip()
    if server_ip:
        addr = ip_address(server_ip)
        hosts.append(f"[{addr}]:*" if addr.version == 6 else f"{addr}:*")
    app = mcp.streamable_http_app(
        stateless_http=True, json_response=True, max_request_body_size=16 * 1024,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True, allowed_hosts=hosts),
    )
    return BearerAuth(app, token)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    # SDK diagnostics may contain request data. Only our aggregate usage log is needed.
    for name in ("openai", "httpx", "httpcore", "mcp"):
        logging.getLogger(name).setLevel(logging.CRITICAL)
    mcp = create_server(Settings.from_env())
    if args.http:
        uvicorn.run(create_http_app(mcp), host=os.environ.get("MCP_HOST", "0.0.0.0"),
                    port=integer("MCP_PORT", 8000, 1, 65535), access_log=False)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
