import unittest
import numpy as np
import cv2
import tempfile
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from data_pipeline.floorplan_preprocessing import preprocess_floorplan

class TestPreprocessing(unittest.TestCase):
    def test_preprocess_floorplan_output_exists(self):
        # Create a dummy white image
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test_input.jpg"
            output_path = Path(tmpdir) / "test_output.png"
            
            img = np.ones((100, 100, 3), dtype=np.uint8) * 255
            cv2.imwrite(str(input_path), img)
            
            preprocess_floorplan(str(input_path), str(output_path))
            
            self.assertTrue(output_path.exists())
            
            # Read output and check if it's binary (mostly)
            out_img = cv2.imread(str(output_path), cv2.IMREAD_GRAYSCALE)
            self.assertEqual(out_img.shape, (100, 100))

if __name__ == '__main__':
    unittest.main()
