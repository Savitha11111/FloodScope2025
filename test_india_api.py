#!/usr/bin/env python3
"""
Test Indian weather API responses for flood detection
"""
import os
import requests
import json
from datetime import datetime

def test_indian_weather_api():
    """Test Indian weather API for Assam flood detection"""
    # Assam coordinates (multiple locations)
    test_locations = [
        {"name": "Guwahati, Assam", "lat": 26.1445, "lon": 91.7362},
        {"name": "Dibrugarh, Assam", "lat": 27.4728, "lon": 94.9120},
        {"name": "Silchar, Assam", "lat": 24.8333, "lon": 92.7789},
        {"name": "Tezpur, Assam", "lat": 26.6335, "lon": 92.7996}
    ]
    
    api_key = os.getenv('OPENWEATHER_API_KEY', '')
    
    print("Testing Indian Weather API for Assam Flood Detection")
    print("="*60)
    
    for location in test_locations:
        print(f"\nTesting {location['name']} ({location['lat']}, {location['lon']})")
        print("-" * 50)
        
        # Current weather
        current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={location['lat']}&lon={location['lon']}&appid={api_key}&units=metric"
        
        try:
            response = requests.get(current_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Extract flood-relevant data
                main = data.get('main', {})
                weather = data.get('weather', [{}])[0]
                
                print(f"Current Weather:")
                print(f"  Temperature: {main.get('temp', 'N/A')}°C")
                print(f"  Humidity: {main.get('humidity', 'N/A')}%")
                print(f"  Pressure: {main.get('pressure', 'N/A')} hPa")
                print(f"  Condition: {weather.get('description', 'N/A')}")
                print(f"  Rain: {data.get('rain', {}).get('1h', 0)} mm/h")
                
                # Calculate flood risk based on conditions
                humidity = main.get('humidity', 0)
                rain_1h = data.get('rain', {}).get('1h', 0)
                pressure = main.get('pressure', 1013)
                
                flood_indicators = []
                if humidity > 85:
                    flood_indicators.append("High humidity")
                if rain_1h > 10:
                    flood_indicators.append("Heavy rainfall")
                if pressure < 1000:
                    flood_indicators.append("Low pressure system")
                
                print(f"  Flood Indicators: {', '.join(flood_indicators) if flood_indicators else 'None detected'}")
                
            else:
                print(f"Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"API Error: {e}")
        
        # 5-day forecast for flood prediction
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={location['lat']}&lon={location['lon']}&appid={api_key}&units=metric"
        
        try:
            response = requests.get(forecast_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n5-Day Forecast Analysis:")
                total_rain = 0
                heavy_rain_periods = 0
                
                for item in data.get('list', [])[:8]:  # Next 24 hours
                    rain = item.get('rain', {}).get('3h', 0)
                    total_rain += rain
                    if rain > 5:  # Heavy rain threshold
                        heavy_rain_periods += 1
                
                print(f"  Expected Rain (24h): {total_rain:.1f} mm")
                print(f"  Heavy Rain Periods: {heavy_rain_periods}")
                
                # Flood risk assessment
                if total_rain > 100:
                    risk = "EXTREME"
                elif total_rain > 50:
                    risk = "HIGH"
                elif total_rain > 25:
                    risk = "MODERATE"
                else:
                    risk = "LOW"
                
                print(f"  Flood Risk: {risk}")
                
        except Exception as e:
            print(f"Forecast Error: {e}")

if __name__ == "__main__":
    test_indian_weather_api()