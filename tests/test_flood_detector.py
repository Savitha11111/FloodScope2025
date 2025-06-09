import unittest
import numpy as np
from services.flood_detector import FloodDetector

class TestFloodDetector(unittest.TestCase):
    def setUp(self):
        self.detector = FloodDetector()
        self.sample_sar_data = {
            'sensor_type': 'SAR',
            'image_array': np.random.rand(512, 512, 2).astype(np.float32),
            'derived_products': {
                'cross_pol_ratio': np.random.rand(512, 512),
                'texture': np.random.rand(512, 512)
            }
        }
        self.sample_optical_data = {
            'sensor_type': 'optical',
            'image_array': np.random.rand(512, 512, 6).astype(np.float32),
            'derived_products': {
                'ndwi': np.random.rand(512, 512),
                'ndvi': np.random.rand(512, 512),
                'mndwi': np.random.rand(512, 512)
            }
        }
    
    def test_detect_floods_sar(self):
        result = self.detector.detect_floods(self.sample_sar_data)
        self.assertIn('flood_mask', result)
        self.assertIn('flood_probability', result)
        self.assertIn('confidence_map', result)
        self.assertIn('flood_regions', result)
        self.assertEqual(result['sensor_type'], 'SAR')
    
    def test_detect_floods_optical(self):
        result = self.detector.detect_floods(self.sample_optical_data)
        self.assertIn('flood_mask', result)
        self.assertIn('flood_probability', result)
        self.assertIn('confidence_map', result)
        self.assertIn('flood_regions', result)
        self.assertEqual(result['sensor_type'], 'optical')
    
    def test_unsupported_sensor(self):
        with self.assertRaises(Exception):
            self.detector.detect_floods({'sensor_type': 'unknown', 'image_array': np.array([])})

if __name__ == '__main__':
    unittest.main()
