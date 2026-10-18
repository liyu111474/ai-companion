import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


class InstallationTests(unittest.TestCase):
    def test_complete_project_copy_starts_with_all_resources(self):
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder) / "project with spaces"
            project.mkdir()
            for name in ("app.py", "style.css"):
                shutil.copy2(ROOT / name, project / name)
            for name in ("static", ".streamlit"):
                shutil.copytree(ROOT / name, project / name)
            with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "",
                                         "AI_COMPANION_SESSION_DIR": str(project / "sessions")}):
                app = AppTest.from_file(str(project / "app.py"), default_timeout=15).run()
            self.assertFalse(app.exception)
            self.assertIn("把今天的心事", app.title[0].value)
            self.assertFalse((project / "sessions").exists())

    @unittest.skipUnless(os.name == "nt", "Windows launcher")
    def test_launcher_uses_project_venv_and_project_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder) / "project with spaces"
            project.mkdir()
            launcher = project / "launch.cmd"
            shutil.copy2(ROOT / "启动小叶子.cmd", launcher)
            subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(project / ".venv")],
                           check=True, capture_output=True, timeout=60)
            # Replace the external CLI boundary so this test never starts a server.
            module = project / "streamlit"
            module.mkdir()
            (module / "__init__.py").write_text("", encoding="utf-8")
            (module / "__main__.py").write_text(
                "import json, os, sys\n"
                "print(json.dumps(dict(executable=sys.executable, cwd=os.getcwd(), args=sys.argv[1:])))\n",
                encoding="utf-8")
            (project / "app.py").write_text("# Installation fixture\n", encoding="utf-8")
            result = subprocess.run(["cmd.exe", "/d", "/c", str(launcher), "--server.headless=true"],
                                    cwd=folder, capture_output=True, text=True, timeout=15,
                                    env={**os.environ, "PYTHONPATH": str(project)})
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(result.stdout.lstrip().startswith("{"), repr((result.stdout, result.stderr)))
            actual = json.loads(result.stdout.strip())
            self.assertEqual(project / ".venv" / "Scripts" / "python.exe", Path(actual["executable"]))
            self.assertEqual(project, Path(actual["cwd"]))
            self.assertEqual(["run", "app.py", "--server.headless=true"], actual["args"])


if __name__ == "__main__":
    unittest.main()
