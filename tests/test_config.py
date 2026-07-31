import unittest
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.infrastructure.config_service import config_service

class TestConfigService(unittest.TestCase):
    def test_get_existing_config(self):
        # Test getting a nested config value
        iou = config_service.get('ai.segformer.iou_threshold')
        self.assertIsInstance(iou, float)
        self.assertGreater(iou, 0)

    def test_get_default_value(self):
        # Test getting a non-existent value with a default
        val = config_service.get('non.existent.key', default='fallback')
        self.assertEqual(val, 'fallback')

    def test_config_structure(self):
        # Test if spatial config is present
        wall_thick = config_service.get('spatial.wall_thickness.medium')
        self.assertEqual(wall_thick, 220)

if __name__ == '__main__':
    unittest.main()
