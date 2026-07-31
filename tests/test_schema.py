import unittest
import json
from jsonschema import validate
from pathlib import Path

class TestSchema(unittest.TestCase):
    def setUp(self):
        with open('schema.json', 'r') as f:
            self.schema = json.load(f)

    def test_valid_spatial_json(self):
        valid_instance = {
            "project_id": "proj_001",
            "metadata": {
                "scale_ratio": 0.01,
                "unit": "mm"
            },
            "levels": [
                {
                    "level_id": "L1",
                    "walls": [
                        {
                            "id": "w1",
                            "points": [[0, 0], [1000, 0]],
                            "thickness": 220
                        }
                    ]
                }
            ]
        }
        # Should not raise exception
        validate(instance=valid_instance, schema=self.schema)

    def test_invalid_spatial_json(self):
        invalid_instance = {
            "project_id": "proj_001",
            # Missing levels
        }
        with self.assertRaises(Exception):
            validate(instance=invalid_instance, schema=self.schema)

if __name__ == '__main__':
    unittest.main()
