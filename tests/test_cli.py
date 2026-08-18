import contextlib
import io
import unittest
from pathlib import Path

from pob_cli.cli import cmd_items, cmd_skills, cmd_tree, build_parser, make_pob_code

ROOT = Path(__file__).resolve().parents[1]
BUILD = str(ROOT / "slammerlappen_pob.xml")


class PobCliTests(unittest.TestCase):
    def test_parser_commands(self):
        parser = build_parser()
        self.assertEqual(parser.parse_args(["tree", BUILD]).command, "tree")
        self.assertEqual(parser.parse_args(["skills", BUILD]).command, "skills")
        self.assertEqual(parser.parse_args(["items", BUILD]).command, "items")

    def test_tree_has_core_nodes(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cmd_tree(type("Args", (), {"build": BUILD, "all": False})())
        text = out.getvalue()
        self.assertIn("Resolute Technique", text)
        self.assertIn("War Bringer", text)
        self.assertIn("Rite of Ruin", text)

    def test_share_code_roundtrip(self):
        import base64
        import zlib
        code = make_pob_code(BUILD)
        xml = zlib.decompress(base64.urlsafe_b64decode(code + '=' * ((4 - len(code) % 4) % 4)))
        self.assertTrue(xml.startswith(b'<?xml'))
        self.assertIn(b'PathOfBuilding', xml)

    def test_docs_exist(self):
        self.assertTrue((ROOT / 'README.md').exists())
        self.assertTrue((ROOT / 'TODO.md').exists())

    def test_skills_and_items(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cmd_skills(type("Args", (), {"build": BUILD})())
            cmd_items(type("Args", (), {"build": BUILD})())
        text = out.getvalue()
        self.assertIn("技能配置", text)
        self.assertIn("Cataclysm Roar", text)


if __name__ == "__main__":
    unittest.main()
