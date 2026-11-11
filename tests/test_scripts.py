"""Tests des scripts du dépôt et de lean.py — usage : python -m unittest discover -s tests"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
LEAN = os.path.join(ROOT, "plugins", "geo-powerbi", "skills", "powerbi-lean", "scripts", "lean.py")
FIXTURE = os.path.join(ROOT, "tests", "fixture", "Demo")


def run(script, *args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, script, *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", env=env)


class Depot(unittest.TestCase):
    def test_validate(self):
        r = run(os.path.join(SCRIPTS, "validate.py"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_marketplace_synchronise(self):
        r = run(os.path.join(SCRIPTS, "generate_marketplace.py"), "--check")
        self.assertEqual(r.returncode, 0, r.stderr)


class Installation(unittest.TestCase):
    def install(self, target, *args):
        return run(os.path.join(SCRIPTS, "install.py"), "--target", target, *args)

    def test_codex_puis_desinstallation(self):
        with tempfile.TemporaryDirectory() as t:
            with open(os.path.join(t, "AGENTS.md"), "w", encoding="utf-8") as f:
                f.write("# Mon projet\n\nRègle locale.\n")
            for _ in range(2):  # deux fois : l'installation est idempotente
                r = self.install(t, "--agent", "codex")
                self.assertEqual(r.returncode, 0, r.stderr)
            skills = os.path.join(t, ".agents", "skills")
            self.assertTrue(os.path.isfile(os.path.join(skills, "powerbi-lean", "scripts", "lean.py")))
            with open(os.path.join(t, "AGENTS.md"), encoding="utf-8") as f:
                text = f.read()
            self.assertIn("Règle locale.", text)
            self.assertEqual(text.count("geo-powerbi:début"), 1)
            self.assertIn(".agents/skills/powerbi-conventions/SKILL.md", text)

            r = self.install(t, "--agent", "codex", "--uninstall")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse(os.path.exists(os.path.join(skills, "powerbi-lean")))
            with open(os.path.join(t, "AGENTS.md"), encoding="utf-8") as f:
                self.assertEqual(f.read(), "# Mon projet\n\nRègle locale.\n")

    def test_dossier_par_agent(self):
        for agent, folder in (("grok", ".grok/skills"), ("copilot", ".github/skills"), ("claude", ".claude/skills")):
            with tempfile.TemporaryDirectory() as t:
                r = self.install(t, "--agent", agent, "--skills", "powerbi-tmdl")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue(os.path.isfile(os.path.join(t, *folder.split("/"), "powerbi-tmdl", "SKILL.md")))
                self.assertEqual(os.path.isfile(os.path.join(t, "AGENTS.md")), agent != "claude")
                self.assertEqual(os.path.isdir(os.path.join(t, ".claude", "agents")), agent == "claude")

    def test_refuse_d_ecraser_un_skill_etranger(self):
        with tempfile.TemporaryDirectory() as t:
            mine = os.path.join(t, ".agents", "skills", "powerbi-tmdl")
            os.makedirs(mine)
            with open(os.path.join(mine, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write("à moi")
            r = self.install(t, "--agent", "generic")
            self.assertEqual(r.returncode, 1)
            with open(os.path.join(mine, "SKILL.md"), encoding="utf-8") as f:
                self.assertEqual(f.read(), "à moi")
            self.assertFalse(os.path.exists(os.path.join(t, ".agents", "skills", "powerbi-lean")))

    def test_simulation_n_ecrit_rien(self):
        with tempfile.TemporaryDirectory() as t:
            r = self.install(t, "--agent", "gemini", "--dry-run")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(os.listdir(t), [])


class Distribution(unittest.TestCase):
    def test_archives(self):
        with tempfile.TemporaryDirectory() as t:
            r = run(os.path.join(SCRIPTS, "build_dist.py"), "--out", t)
            self.assertEqual(r.returncode, 0, r.stderr)
            names = os.listdir(t)
            self.assertIn("powerbi-lean.zip", names)
            with zipfile.ZipFile(os.path.join(t, "powerbi-lean.zip")) as zf:
                self.assertIn("powerbi-lean/SKILL.md", zf.namelist())
                self.assertIn("powerbi-lean/scripts/lean.py", zf.namelist())
            bundle = [n for n in names if n.startswith("geo-powerbi-") and n.endswith(".md")]
            self.assertEqual(len(bundle), 1)
            with open(os.path.join(t, bundle[0]), encoding="utf-8") as f:
                self.assertIn("<!-- skill: powerbi-conventions -->", f.read())


class Lean(unittest.TestCase):
    def lean(self, *args):
        r = run(LEAN, *args)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_audit(self):
        res = json.loads(self.lean("audit", FIXTURE, "--json"))
        inutilises = [f["obj"] for f in res["findings"] if f["cat"].startswith("Inutilis")]
        self.assertIn("[Nb clients] (_Mesures)", inutilises)
        self.assertNotIn("[CA HT] (_Mesures)", inutilises)  # utilisée par le rapport

    def test_usage(self):
        self.assertIn("CA HT", self.lean("usage", FIXTURE))

    def test_dette(self):
        rep = json.loads(self.lean("dette", FIXTURE, "--json"))
        self.assertEqual((rep["open"], rep["nextId"]["dette"]), (1, "D-002"))

    def test_catalogue(self):
        md = self.lean("catalogue", FIXTURE)
        self.assertIn("# Dictionnaire de données", md)
        self.assertIn("Fact_Ventes", md)
        self.assertNotIn("@example.com", md)  # un filtre RLS qui contient un e-mail n'est jamais recopié
        json.loads(self.lean("catalogue", FIXTURE, "--json"))

    def test_projet_introuvable(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertNotEqual(run(LEAN, "audit", t).returncode, 0)


if __name__ == "__main__":
    unittest.main()
