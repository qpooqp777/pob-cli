import shutil
import unittest
from pathlib import Path

from pob_cli.headless import run_pob_calcs

ROOT = Path(__file__).resolve().parents[1]
POB_ROOT = Path("/home/ubuntu/PathOfBuilding")
BUILD = ROOT / "slammerlappen_pob.xml"


@unittest.skipUnless(shutil.which("luajit") and (POB_ROOT / "src" / "HeadlessWrapper.lua").exists(), "PoB LuaJIT runtime not available")
class HeadlessIntegrationTests(unittest.TestCase):
    def test_earthshatter_matches_expected_build_scale(self):
        payload = run_pob_calcs(BUILD, POB_ROOT, timeout=180, skill="Earthshatter")
        output = payload["output"]
        self.assertEqual(payload["selected_skill"], "Earthshatter")
        self.assertEqual(output["Life"], 3620)
        self.assertEqual(output["Armour"], 17253)
        self.assertEqual(output["ChaosResist"], -1)
        self.assertAlmostEqual(output["TotalDPS"], 203075.4164, places=2)
        self.assertAlmostEqual(output["ChaosMaximumHitTaken"], 6615, places=0)


if __name__ == "__main__":
    unittest.main()
