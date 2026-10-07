import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sync  # noqa: E402


class SyncTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.repo = self.root / "demo-mcp"
        self.repo.mkdir()
        self.agents = self.repo / "AGENTS.md"
        self.agents.write_text(f"# demo\n\n固有の説明\n\n{sync.BEGIN}\n古い内容\n{sync.END}\n\n末尾\n", encoding="utf-8")

    def run_sync(self, *args):
        with redirect_stdout(io.StringIO()):
            return sync.main(["--root", str(self.root), *args])

    def test_check_detects_and_sync_fixes_drift(self):
        self.assertEqual(self.run_sync("--check"), 1)
        self.assertEqual(self.run_sync(), 0)
        text = self.agents.read_text(encoding="utf-8")
        self.assertIn("固有の説明", text)
        self.assertTrue(text.endswith("末尾\n"))
        self.assertNotIn("古い内容", text)
        self.assertIn("## 共通規約", text)
        self.assertEqual(self.run_sync("--check"), 0)

    def test_repos_without_markers_are_untouched(self):
        other = self.root / "other" / "AGENTS.md"
        other.parent.mkdir()
        other.write_text("no markers\n", encoding="utf-8")
        self.run_sync()
        self.assertEqual(other.read_text(encoding="utf-8"), "no markers\n")

    def test_broken_markers_are_reported(self):
        self.agents.write_text(f"{sync.BEGIN}\nno end\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.run_sync()

    def test_new_rejects_used_port_bad_name_and_existing_dir(self):
        for args in (["new", "demo2", "--port", "8101"], ["new", "Bad_Name", "--port", "8150"],
                     ["new", "demo", "--port", "8150"]):
            with self.subTest(args=args), self.assertRaises(SystemExit):
                self.run_sync(*args)

    def test_new_project_is_renamed_synced_and_tests_pass(self):
        self.assertEqual(self.run_sync("new", "pdf-reader-mcp", "--port", "8150"), 0)
        made = self.root / "pdf-reader-mcp"
        self.assertTrue((made / "pdf_reader_mcp" / "core.py").exists())
        self.assertFalse((made / "example_mcp").exists())
        for path in made.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"example[-_]mcp|EXAMPLE_|8199", path.name)
        self.assertIn("PDF_READER_MCP_TOKEN", (made / "docker-compose.yaml").read_text(encoding="utf-8"))
        self.assertIn("8150", (made / ".env.example").read_text(encoding="utf-8"))
        self.assertIn("## 共通規約", (made / "AGENTS.md").read_text(encoding="utf-8"))
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                                cwd=made, capture_output=True, text=True, env={"PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])


if __name__ == "__main__":
    unittest.main()
