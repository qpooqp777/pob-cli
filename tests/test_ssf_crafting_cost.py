import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
import ssf_crafting_cost as mod

class TestSSFCraftingCost(unittest.TestCase):
    def test_geometric_expectation(self):
        r = mod.Route('x', 0.01, {'Essence': 2}, {'Base': 1})
        self.assertAlmostEqual(r.expected_attempts(), 100.0)
        self.assertAlmostEqual(r.expected_materials()['Essence'], 200.0)
        self.assertEqual(r.attempts_for_confidence(0.9), 230)

    def test_config_load_and_unit_cost(self):
        data = {'unit_values': {'A': 2, 'B': 5}, 'routes': [
            {'name': 'route', 'success_probability': 0.5, 'materials_per_attempt': {'A': 1}, 'fixed_materials': {'B': 1}}
        ]}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.json'; p.write_text(json.dumps(data), encoding='utf-8')
            cfg, routes = mod.load_config(p)
        self.assertEqual(len(routes), 1)
        self.assertAlmostEqual(routes[0].expected_total_units(cfg['unit_values']), 9.0)

if __name__ == '__main__':
    unittest.main()
