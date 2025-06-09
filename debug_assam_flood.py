#!/usr/bin/env python3
"""
Debug script to investigate why Assam flood data is showing as minimal
"""
import os
import requests
import json
from datetime import datetime

def test_ambee_api():
    """Test Ambee API responses for Assam coordinates"""
    # Assam coordinates (Guwahati area)
    lat, lon = 26.1445, 91.7362
    
    headers = {
        'x-api-key': os.getenv('AMBEE_API_KEY', ''),
        'Content-type': 'application/json'
    }
    
    print(f"Testing Ambee APIs for Assam coordinates: {lat}, {lon}")
    print("="*60)
    
    # Test Natural Disasters API
    disasters_url = f"https://api.ambeedata.com/disasters/by-lat-lng?lat={lat}&lng={lon}"
    try:
        response = requests.get(disasters_url, headers=headers, timeout=10)
        print(f"Natural Disasters API Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Disasters Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Disasters API Error: {e}")
    
    print("\n" + "="*60)
    
    # Test Weather API
    weather_url = f"https://api.ambeedata.com/weather/latest/by-lat-lng?lat={lat}&lng={lon}"
    try:
        response = requests.get(weather_url, headers=headers, timeout=10)
        print(f"Weather API Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Weather Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Weather API Error: {e}")

def test_indian_api():
    """Test IndianAPI responses for Assam"""
    api_key = os.getenv('OPENWEATHER_API_KEY', '')
    lat, lon = 26.1445, 91.7362
    
    print(f"\nTesting IndianAPI for Assam coordinates: {lat}, {lon}")
    print("="*60)
    
    # Test current weather
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        print(f"OpenWeather API Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Weather Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"OpenWeather API Error: {e}")

if __name__ == "__main__":
    print("FloodScope AI - Assam Flood Debug")
    print(f"Current time: {datetime.now()}")
    print("\nChecking API responses for extreme flood detection...")
    
    test_ambee_api()
    test_indian_api()