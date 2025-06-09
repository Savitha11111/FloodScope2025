import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from services.ambee_flood_service import AmbeeFloodService

class TestAmbeeFloodService(unittest.TestCase):
    def setUp(self):
        self.service = AmbeeFloodService()
        self.lat = 12.9716
        self.lon = 77.5946
    
    @patch('services.ambee_flood_service.requests.get')
    def test_get_current_flood_data_success(self, mock_get):
        # Mock disaster data response
        mock_disaster_response = MagicMock()
        mock_disaster_response.raise_for_status.return_value = None
        mock_disaster_response.json.return_value = {
            'data': [
                {'eventType': 'FLOOD', 'severity': 6, 'affectedArea': 100}
            ]
        }
        
        # Mock weather data response
        mock_weather_response = MagicMock()
        mock_weather_response.raise_for_status.return_value = None
        mock_weather_response.json.return_value = {
            'data': {'precipitation': 120}
        }
        
        # Setup side effects for requests.get
        mock_get.side_effect = [mock_disaster_response, mock_weather_response]
        
        result = self.service.get_current_flood_data(self.lat, self.lon)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['flood_risk_level'], 'very_high')
        self.assertGreater(result['confidence_score'], 0)
        self.assertEqual(result['affected_area_km2'], 100)
    
    @patch('services.ambee_flood_service.requests.get')
    def test_get_current_flood_data_api_failure(self, mock_get):
        mock_get.side_effect = Exception("API failure")
        
        result = self.service.get_current_flood_data(self.lat, self.lon)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Processing error', result['error'])
    
    @patch('services.ambee_flood_service.requests.get')
    def test_get_flood_forecast_success(self, mock_get):
        mock_forecast_response = MagicMock()
        mock_forecast_response.raise_for_status.return_value = None
        mock_forecast_response.json.return_value = {
            'data': [
                {'date': '2025-06-01', 'riskScore': 0.8, 'severity': 'high', 'confidence': 0.9}
            ]
        }
        mock_get.return_value = mock_forecast_response
        
        result = self.service.get_flood_forecast(self.lat, self.lon)
        
        self.assertEqual(result['status'], 'success')
        self.assertTrue(len(result['forecast']) > 0)
    
    @patch('services.ambee_flood_service.requests.get')
    def test_get_historical_flood_data_success(self, mock_get):
        mock_historical_response = MagicMock()
        mock_historical_response.raise_for_status.return_value = None
        mock_historical_response.json.return_value = {
            'data': [
                {'eventId': '1', 'date': '2025-05-01', 'severity': 'moderate', 'alertScore': 3, 'durationHours': 5, 'affectedAreaKm2': 50}
            ]
        }
        mock_get.return_value = mock_historical_response
        
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        result = self.service.get_historical_flood_data(self.lat, self.lon, start_date, end_date)
        
        self.assertEqual(result['status'], 'success')
        self.assertTrue(len(result['events']) > 0)

if __name__ == '__main__':
    unittest.main()
