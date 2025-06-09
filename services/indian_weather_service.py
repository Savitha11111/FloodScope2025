"""
IndianAPI Weather Service
Provides accurate weather data for Indian locations using IMD data
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

class IndianWeatherService:
    """Service for fetching accurate Indian weather data from IndianAPI"""
    
    def __init__(self):
        """Initialize IndianAPI weather service"""
        self.api_key = os.getenv("INDIAN_API_KEY", "sk-live-AVq9PzDJT1KJyE2qkmGkglXeGYXftADTDUBXruYs")
        self.base_url = "https://indianapi.in/api"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_indian_weather_data(self, lat: float, lon: float, location_name: str = "") -> Dict[str, Any]:
        """
        Get comprehensive weather data for Indian locations using IMD data
        
        Args:
            lat: Latitude
            lon: Longitude
            location_name: Name of the location (optional)
            
        Returns:
            Comprehensive weather data with precipitation, temperature, and flood indicators
        """
        try:
            # Check if location is in India (approximate bounds)
            if not self._is_indian_location(lat, lon):
                return {"status": "not_india", "message": "Location outside India, use global API"}
            
            # Get current weather from IndianAPI India endpoint
            current_weather = self._get_current_weather_india(lat, lon)
            
            # Get forecast data
            forecast_data = self._get_forecast_data_india(lat, lon)
            
            # Process and combine data
            processed_data = self._process_indian_weather_data(current_weather, forecast_data, lat, lon)
            
            return processed_data
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"IndianAPI weather fetch failed: {str(e)}",
                "fallback_needed": True
            }
    
    def _is_indian_location(self, lat: float, lon: float) -> bool:
        """Check if coordinates are within India's approximate bounds"""
        # India's approximate geographical bounds
        return (6.0 <= lat <= 37.0) and (68.0 <= lon <= 97.0)
    
    def _get_current_weather_india(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get current weather data from IndianAPI India endpoint"""
        try:
            url = f"{self.base_url}/weather/india/current"
            params = {
                "lat": lat,
                "lon": lon
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API returned status {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Current weather request failed: {str(e)}"}
    
    def _get_forecast_data_india(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get forecast data from IndianAPI India endpoint"""
        try:
            url = f"{self.base_url}/weather/india/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "days": 5
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Forecast API returned status {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Forecast request failed: {str(e)}"}
    
    def _process_indian_weather_data(self, current: Dict, forecast: Dict, lat: float, lon: float) -> Dict[str, Any]:
        """Process IndianAPI weather data for flood analysis"""
        try:
            processed = {
                "status": "success",
                "source": "IndianAPI_IMD",
                "location": {"lat": lat, "lon": lon},
                "timestamp": (datetime.utcnow() + timedelta(hours=5, minutes=30)).isoformat(),
                "current_conditions": {},
                "precipitation": {},
                "flood_indicators": {},
                "confidence": 0.95  # Very high confidence for official IMD data
            }
            
            # Process current weather data
            if "data" in current and not current.get("error"):
                weather_data = current["data"]
                
                processed["current_conditions"] = {
                    "temperature": weather_data.get("temperature", 0),
                    "humidity": weather_data.get("humidity", 0),
                    "pressure": weather_data.get("pressure", 0),
                    "wind_speed": weather_data.get("wind_speed", 0),
                    "visibility": weather_data.get("visibility", 10),
                    "weather_description": weather_data.get("description", ""),
                    "feels_like": weather_data.get("feels_like", weather_data.get("temperature", 0))
                }
                
                # Extract precipitation data
                precipitation_24h = weather_data.get("precipitation_24h", 0)
                precipitation_1h = weather_data.get("precipitation_1h", 0)
                
                processed["precipitation"] = {
                    "current_intensity": precipitation_1h,
                    "last_24h": precipitation_24h,
                    "intensity_level": self._classify_precipitation_intensity(precipitation_1h),
                    "flood_risk_level": self._assess_flood_risk_from_precipitation(precipitation_24h)
                }
                
                # Enhanced flood risk indicators specific to Indian conditions
                processed["flood_indicators"] = {
                    "heavy_rain_alert": precipitation_24h > 64.5,  # IMD heavy rain threshold
                    "very_heavy_rain_alert": precipitation_24h > 115.5,  # IMD very heavy rain
                    "extremely_heavy_rain_alert": precipitation_24h > 204.4,  # IMD extremely heavy
                    "monsoon_intensity": self._calculate_monsoon_intensity(weather_data),
                    "urban_flood_risk": self._assess_urban_flood_risk(precipitation_24h, weather_data),
                    "data_freshness": "real_time_imd",
                    "official_source": True
                }
                
                # Override confidence based on data quality
                if precipitation_24h > 0 or weather_data.get("humidity", 0) > 0:
                    processed["confidence"] = 0.98  # Maximum confidence for active weather data
            
            # Process forecast data for extended precipitation
            if "data" in forecast and not forecast.get("error"):
                forecast_precip = self._extract_forecast_precipitation(forecast["data"])
                processed["precipitation"]["forecast_24h"] = forecast_precip["next_24h"]
                processed["precipitation"]["forecast_48h"] = forecast_precip["next_48h"]
                processed["flood_indicators"]["extended_risk"] = forecast_precip["next_24h"] > 50
            
            return processed
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Data processing failed: {str(e)}",
                "fallback_needed": True
            }
    
    def _classify_precipitation_intensity(self, precipitation_1h: float) -> str:
        """Classify precipitation intensity based on IMD standards"""
        if precipitation_1h > 7.5:
            return "heavy"
        elif precipitation_1h > 2.5:
            return "moderate"
        elif precipitation_1h > 0.1:
            return "light"
        else:
            return "none"
    
    def _assess_flood_risk_from_precipitation(self, precipitation_24h: float) -> str:
        """Assess flood risk based on 24h precipitation using Indian standards"""
        if precipitation_24h > 204.4:
            return "extreme"
        elif precipitation_24h > 115.5:
            return "very_high"
        elif precipitation_24h > 64.5:
            return "high"
        elif precipitation_24h > 25:
            return "moderate"
        elif precipitation_24h > 10:
            return "low"
        else:
            return "minimal"
    
    def _calculate_monsoon_intensity(self, weather_data: Dict) -> str:
        """Calculate monsoon intensity based on multiple factors"""
        humidity = weather_data.get("humidity", 0)
        wind_speed = weather_data.get("wind_speed", 0)
        pressure = weather_data.get("pressure", 1013)
        
        # Monsoon indicators
        monsoon_score = 0
        if humidity > 80:
            monsoon_score += 2
        elif humidity > 70:
            monsoon_score += 1
        
        if pressure < 1010:
            monsoon_score += 2
        elif pressure < 1012:
            monsoon_score += 1
        
        if 10 <= wind_speed <= 25:
            monsoon_score += 1
        
        if monsoon_score >= 4:
            return "intense"
        elif monsoon_score >= 2:
            return "moderate"
        else:
            return "weak"
    
    def _assess_urban_flood_risk(self, precipitation_24h: float, weather_data: Dict) -> str:
        """Assess urban flood risk considering Indian city drainage capacity"""
        # Urban drainage typically handles 25-50mm/hour in Indian cities
        base_risk = self._assess_flood_risk_from_precipitation(precipitation_24h)
        
        # Adjust for urban factors
        humidity = weather_data.get("humidity", 0)
        if humidity > 85 and precipitation_24h > 50:
            # High humidity + significant rain = poor drainage efficiency
            if base_risk == "moderate":
                return "high"
            elif base_risk == "low":
                return "moderate"
        
        return base_risk
    
    def _extract_forecast_precipitation(self, forecast_data: list) -> Dict[str, float]:
        """Extract precipitation forecast for next 24h and 48h"""
        try:
            current_time = datetime.utcnow()
            precip_24h = 0
            precip_48h = 0
            
            for item in forecast_data:
                if "datetime" in item and "precipitation" in item:
                    forecast_time = datetime.fromisoformat(item["datetime"].replace('Z', '+00:00'))
                    time_diff = (forecast_time - current_time).total_seconds() / 3600
                    
                    precipitation = item.get("precipitation", 0)
                    
                    if 0 <= time_diff <= 24:
                        precip_24h += precipitation
                    elif 24 < time_diff <= 48:
                        precip_48h += precipitation
            
            return {
                "next_24h": precip_24h,
                "next_48h": precip_48h
            }
            
        except Exception:
            return {"next_24h": 0, "next_48h": 0}