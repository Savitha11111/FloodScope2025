"""
Enhanced Indian Weather Service with Advanced Flood Detection
Provides comprehensive weather analysis specifically for Indian regions
"""
import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class EnhancedIndianWeatherService:
    """Enhanced weather service for Indian locations with flood detection"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY', '')
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
    def get_comprehensive_flood_assessment(self, lat: float, lon: float, location_name: str = "") -> Dict[str, Any]:
        """Get comprehensive flood assessment using multiple weather endpoints"""
        
        # Get current weather conditions
        current_weather = self._get_current_weather_detailed(lat, lon)
        
        # Get forecast data for flood prediction
        forecast_data = self._get_forecast_data(lat, lon)
        
        # Get historical weather patterns
        historical_data = self._get_weather_patterns(lat, lon)
        
        # Analyze flood conditions
        flood_assessment = self._analyze_flood_conditions(
            current_weather, forecast_data, historical_data, location_name, lat, lon
        )
        
        return flood_assessment
    
    def _get_current_weather_detailed(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get detailed current weather with all available parameters"""
        url = f"{self.base_url}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                return {
                    'status': 'success',
                    'temperature': data.get('main', {}).get('temp', 0),
                    'humidity': data.get('main', {}).get('humidity', 0),
                    'pressure': data.get('main', {}).get('pressure', 1013),
                    'rain_1h': data.get('rain', {}).get('1h', 0),
                    'rain_3h': data.get('rain', {}).get('3h', 0),
                    'wind_speed': data.get('wind', {}).get('speed', 0),
                    'clouds': data.get('clouds', {}).get('all', 0),
                    'visibility': data.get('visibility', 10000),
                    'weather_condition': data.get('weather', [{}])[0].get('main', 'Clear'),
                    'description': data.get('weather', [{}])[0].get('description', ''),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {'status': 'error', 'message': f"API error: {response.status_code}"}
                
        except Exception as e:
            return {'status': 'error', 'message': f"Request failed: {str(e)}"}
    
    def _get_forecast_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get 5-day forecast for flood prediction"""
        url = f"{self.base_url}/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Process forecast data for flood analysis
                forecast_analysis = {
                    'total_rain_24h': 0,
                    'total_rain_72h': 0,
                    'heavy_rain_periods': 0,
                    'continuous_rain_hours': 0,
                    'max_hourly_rain': 0,
                    'pressure_drop': False,
                    'forecast_items': []
                }
                
                for i, item in enumerate(data.get('list', [])[:24]):  # Next 72 hours (3-hour intervals)
                    rain_3h = item.get('rain', {}).get('3h', 0)
                    pressure = item.get('main', {}).get('pressure', 1013)
                    
                    if i < 8:  # First 24 hours
                        forecast_analysis['total_rain_24h'] += rain_3h
                    forecast_analysis['total_rain_72h'] += rain_3h
                    
                    if rain_3h > 10:  # Heavy rain threshold
                        forecast_analysis['heavy_rain_periods'] += 1
                    
                    if rain_3h > 0:
                        forecast_analysis['continuous_rain_hours'] += 3
                    
                    forecast_analysis['max_hourly_rain'] = max(
                        forecast_analysis['max_hourly_rain'], rain_3h / 3
                    )
                    
                    if pressure < 1000:
                        forecast_analysis['pressure_drop'] = True
                    
                    forecast_analysis['forecast_items'].append({
                        'datetime': item.get('dt_txt', ''),
                        'rain_3h': rain_3h,
                        'pressure': pressure,
                        'humidity': item.get('main', {}).get('humidity', 0)
                    })
                
                forecast_analysis['status'] = 'success'
                return forecast_analysis
                
            else:
                return {'status': 'error', 'message': f"Forecast API error: {response.status_code}"}
                
        except Exception as e:
            return {'status': 'error', 'message': f"Forecast request failed: {str(e)}"}
    
    def _get_weather_patterns(self, lat: float, lon: float) -> Dict[str, Any]:
        """Analyze weather patterns for the region"""
        # Check if location is in monsoon-affected region
        patterns = {
            'is_monsoon_region': False,
            'monsoon_season': False,
            'typical_rainfall': 0,
            'flood_prone': False
        }
        
        # Northeast India (including Assam) monsoon patterns
        if 23.0 <= lat <= 29.0 and 88.0 <= lon <= 97.0:
            patterns['is_monsoon_region'] = True
            patterns['flood_prone'] = True
            
            current_month = datetime.now().month
            if 6 <= current_month <= 9:
                patterns['monsoon_season'] = True
                patterns['typical_rainfall'] = 200  # mm per month during monsoon
        
        # Other monsoon regions in India
        elif 8.0 <= lat <= 37.0 and 68.0 <= lon <= 97.0:
            patterns['is_monsoon_region'] = True
            current_month = datetime.now().month
            if 6 <= current_month <= 9:
                patterns['monsoon_season'] = True
                patterns['typical_rainfall'] = 150
        
        return patterns
    
    def _analyze_flood_conditions(self, current: Dict, forecast: Dict, patterns: Dict, 
                                location_name: str, lat: float, lon: float) -> Dict[str, Any]:
        """Analyze all data to determine flood conditions"""
        
        if current.get('status') != 'success' or forecast.get('status') != 'success':
            return {
                'status': 'error',
                'message': 'Unable to retrieve weather data for flood analysis'
            }
        
        # Calculate flood risk indicators
        flood_indicators = []
        risk_score = 0
        
        # Current conditions analysis
        humidity = current.get('humidity', 0)
        pressure = current.get('pressure', 1013)
        current_rain = max(current.get('rain_1h', 0), current.get('rain_3h', 0) / 3)
        
        if humidity > 85:
            flood_indicators.append("High humidity (saturation conditions)")
            risk_score += 10
        
        if pressure < 1000:
            flood_indicators.append("Low pressure system (storm conditions)")
            risk_score += 15
        
        if current_rain > 5:
            flood_indicators.append(f"Active rainfall: {current_rain:.1f} mm/h")
            risk_score += current_rain * 2
        
        # Forecast analysis
        rain_24h = forecast.get('total_rain_24h', 0)
        rain_72h = forecast.get('total_rain_72h', 0)
        heavy_periods = forecast.get('heavy_rain_periods', 0)
        continuous_hours = forecast.get('continuous_rain_hours', 0)
        
        if rain_24h > 25:
            flood_indicators.append(f"Heavy rainfall forecast: {rain_24h:.1f} mm/24h")
            risk_score += rain_24h * 0.8
        
        if rain_72h > 100:
            flood_indicators.append(f"Sustained rainfall: {rain_72h:.1f} mm/72h")
            risk_score += rain_72h * 0.3
        
        if heavy_periods > 3:
            flood_indicators.append(f"Multiple heavy rain periods: {heavy_periods}")
            risk_score += heavy_periods * 5
        
        if continuous_hours > 12:
            flood_indicators.append(f"Continuous rainfall: {continuous_hours} hours")
            risk_score += continuous_hours
        
        # Regional factors
        if patterns.get('monsoon_season') and patterns.get('flood_prone'):
            flood_indicators.append("Monsoon season in flood-prone region")
            risk_score += 25
        
        # Regional flood risk assessment for monsoon season
        if patterns.get('monsoon_season') and patterns.get('flood_prone'):
            if rain_24h > 150 or continuous_hours > 36:
                flood_indicators.append("Heavy sustained rainfall during monsoon")
                risk_score += 40
            if heavy_periods > 5:
                flood_indicators.append("Multiple intense rainfall events")
                risk_score += 25
        
        # Determine risk level
        if risk_score > 100:
            risk_level = 'extreme'
        elif risk_score > 75:
            risk_level = 'high'
        elif risk_score > 50:
            risk_level = 'moderate'
        elif risk_score > 25:
            risk_level = 'low'
        else:
            risk_level = 'minimal'
        
        # Calculate affected area based on rainfall and risk level
        total_rainfall = rain_24h + (current_rain * 24)
        
        if total_rainfall > 0:
            # Base calculation on actual precipitation
            base_affected_area = total_rainfall / 12
            
            # Adjust based on risk level
            if risk_level == 'extreme':
                affected_area = base_affected_area * 4
                flood_percentage = min(25.0, total_rainfall / 6)
                water_level = total_rainfall / 80
            elif risk_level == 'high':
                affected_area = base_affected_area * 2.5
                flood_percentage = min(15.0, total_rainfall / 10)
                water_level = total_rainfall / 120
            elif risk_level == 'moderate':
                affected_area = base_affected_area * 1.5
                flood_percentage = min(8.0, total_rainfall / 15)
                water_level = total_rainfall / 150
            elif risk_level == 'low':
                affected_area = base_affected_area * 0.8
                flood_percentage = min(3.0, total_rainfall / 25)
                water_level = total_rainfall / 200
            else:
                affected_area = 0.0
                flood_percentage = 0.0
                water_level = 0.0
        else:
            affected_area = 0.0
            flood_percentage = 0.0
            water_level = 0.0
        
        # Confidence based on data quality and consistency
        confidence = 0.75  # Base confidence for Indian weather API
        if len(flood_indicators) > 3:
            confidence += 0.15
        if patterns.get('monsoon_season'):
            confidence += 0.10
        if risk_level == 'extreme':
            confidence = min(0.92, confidence + 0.15)  # Higher confidence for extreme conditions
        
        return {
            'status': 'success',
            'risk_level': risk_level,
            'confidence_score': min(confidence, 0.95),
            'affected_area_km2': affected_area,
            'precipitation_24h': total_rainfall,
            'flood_percentage': flood_percentage,
            'water_level_m': water_level,
            'risk_score': risk_score,
            'flood_indicators': flood_indicators,
            'current_conditions': {
                'temperature': current.get('temperature', 0),
                'humidity': humidity,
                'pressure': pressure,
                'rainfall_current': current_rain,
                'wind_speed': current.get('wind_speed', 0),
                'visibility': current.get('visibility', 10000)
            },
            'forecast_summary': {
                'rain_24h': rain_24h,
                'rain_72h': rain_72h,
                'heavy_periods': heavy_periods,
                'continuous_hours': continuous_hours
            },
            'regional_factors': patterns,
            'data_source': 'Enhanced Indian Weather API',
            'last_updated': datetime.now().isoformat()
        }