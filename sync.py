"""Keep the shared conventions block in every MCP repository's AGENTS.md up to date.

python sync.py            Rewrite the shared block in sibling repositories
python sync.py --check    Exit 1 if any repository is out of date (no writes)
python sync.py new NAME --port 8103
                          Create ../NAME-mcp from template/ (stdlib only, no git)
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEGIN = "<!-- BEGIN mcp-conventions: sync.py が管理。この範囲は直接編集しない -->"
END = "<!-- END mcp-conventions -->"
BLOCK = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
NAME = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
SKIP = {"__pycache__", ".venv", ".DS_Store"}


def block() -> str:
    return f"{BEGIN}\n\n{(HERE / 'CONVENTIONS.md').read_text(encoding='utf-8').strip()}\n\n{END}"


def targets(root: Path) -> list[Path]:
    found = []
    for path in sorted(root.glob("*/AGENTS.md")):
        text = path.read_text(encoding="utf-8")
        if BEGIN in text and END in text:
            found.append(path)
        elif "<!-- BEGIN mcp-conventions" in text:
            raise SystemExit(f"{path}: 共通ブロックの開始/終了マーカーが壊れています。")
    return found


def sync(root: Path, check: bool) -> int:
    expected, stale = block(), []
    for path in targets(root):
        text = path.read_text(encoding="utf-8")
        updated = BLOCK.sub(lambda _: expected, text, count=1)
        if updated != text:
            stale.append(path.parent.name)
            if not check:
                path.write_text(updated, encoding="utf-8")
    if check:
        if stale:
            print("共通規約が古いリポジトリ:", ", ".join(stale))
            print("python mcp-conventions/sync.py で更新してください。")
            return 1
        print("共通規約はすべて最新です。")
    else:
        print("更新:", ", ".join(stale) if stale else "なし（すべて最新）")
    return 0


def used_ports() -> set[int]:
    text = (HERE / "CONVENTIONS.md").read_text(encoding="utf-8")
    return {int(p) for p in re.findall(r"^\| (\d{4,5}) \| [a-z]", text, re.M)}


def new(root: Path, name: str, port: int) -> int:
    name = name.removesuffix("-mcp")
    if not NAME.match(name):
        raise SystemExit("NAME は英小文字・数字・ハイフンで指定してください（例: translate, pdf-reader）。")
    if not 1024 <= port <= 65535 or port in used_ports():
        raise SystemExit(f"ポート {port} は使用済みか範囲外です。CONVENTIONS.md の表を確認してください。")
    dest = root / f"{name}-mcp"
    if dest.exists():
        raise SystemExit(f"{dest} は既に存在します。上書きしません。")
    package = name.replace("-", "_")
    replace = {"example-mcp": f"{name}-mcp", "example_mcp": f"{package}_mcp",
               "EXAMPLE_": f"{package.upper()}_", "8199": str(port)}

    def render(text: str) -> str:
        for old, value in replace.items():
            text = text.replace(old, value)
        return text

    template = HERE / "template"
    for src in sorted(template.rglob("*")):
        rel = src.relative_to(template)
        if SKIP & set(rel.parts) or src.is_dir():
            continue
        out = dest / render(str(rel))
        out.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in (".py", ".md", ".txt", ".yaml", ".example", "") or src.name.startswith("."):
            out.write_text(render(src.read_text(encoding="utf-8")), encoding="utf-8")
        else:
            shutil.copyfile(src, out)
    sync(root, check=False)
    print(f"作成しました: {dest}")
    print(f"次の作業: CONVENTIONS.md のポート表に `| {port} | {name}-mcp |` を追記し、sync.py を再実行してください。")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=HERE.parent, help="MCPリポジトリが並ぶフォルダー")
    parser.add_argument("--check", action="store_true", help="書き換えずに差分だけ確認")
    sub = parser.add_subparsers(dest="command")
    create = sub.add_parser("new", help="ひな形から新しいMCPリポジトリを作る")
    create.add_argument("name")
    create.add_argument("--port", type=int, required=True)
    args = parser.parse_args(argv)
    if args.command == "new":
        return new(args.root, args.name, args.port)
    return sync(args.root, args.check)


if __name__ == "__main__":
    sys.exit(main())
