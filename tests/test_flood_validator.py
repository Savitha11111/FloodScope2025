import unittest
from unittest.mock import patch, MagicMock
from services.flood_validator import FloodDataValidator

class TestFloodDataValidator(unittest.TestCase):
    def setUp(self):
        self.validator = FloodDataValidator()
        self.lat = 12.9716
        self.lon = 77.5946
    
    @patch('services.flood_validator.requests.get')
    def test_validate_flood_conditions_success(self, mock_get):
        # Mock precipitation validation
        mock_precip = MagicMock()
        mock_precip.json.return_value = {
            'rain': {'1h': 10}
        }
        mock_get.return_value = mock_precip
        
        result = self.validator.validate_flood_conditions(self.lat, self.lon)
        
        self.assertIn('validation_score', result)
        self.assertIn('final_assessment', result)
        self.assertIn('flood_indicators', result)
    
    @patch('services.flood_validator.requests.get')
    def test_validate_flood_conditions_api_failure(self, mock_get):
        mock_get.side_effect = Exception("API failure")
        
        result = self.validator.validate_flood_conditions(self.lat, self.lon)
        
        self.assertIn('validation_score', result)
        self.assertIn('final_assessment', result)
        self.assertIn('flood_indicators', result)

if __name__ == '__main__':
    unittest.main()
