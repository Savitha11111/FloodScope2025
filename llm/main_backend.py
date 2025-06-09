from data_fetcher import fetch_image
from preprocess import preprocess_image
from model_inference import run_flood_detection as run_prithvi_inference
from ai4g_inference import run_ai4g_sar_inference
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim

def check_cloud_coverage(image_path):
    # Placeholder function to check cloud coverage in Sentinel-2 image
    # Returns True if cloud coverage is low enough, False otherwise
    # Implement actual cloud detection logic here
    return True

def main():
    print("\\n🌐 Flood Detection System - Prithvi and AI4G Models (Sentinel-2 and Sentinel-1)\\n")
    
    location_name = input("Enter Location Name (e.g., Bangalore, Delhi): ").strip()
    lat_input = input("Enter Latitude (optional): ").strip()
    lon_input = input("Enter Longitude (optional): ").strip()

    if lat_input and lon_input:
        try:
            lat = float(lat_input)
            lon = float(lon_input)
            print(f"📍 Using provided coordinates: Latitude: {lat}, Longitude: {lon}")
        except ValueError:
            print("❌ Invalid latitude or longitude input. Exiting.")
            return
    else:
        geolocator = Nominatim(user_agent="flood_detection_app")
        location = geolocator.geocode(location_name)
        if not location:
            print(f"❌ Could not find location: {location_name}")
            return
        lat = location.latitude
        lon = location.longitude
        print(f"📍 Resolved Location: {location_name} -> Latitude: {lat}, Longitude: {lon}")

    base_date_str = input("Enter Base Date (YYYY-MM-DD): ").strip()
    base_date = datetime.strptime(base_date_str, "%Y-%m-%d")

    print("Select Sensor Type:")
    print("1 - Automatic (Sentinel-2 with fallback to Sentinel-1)")
    print("2 - Sentinel-2 (Optical) Only")
    print("3 - Sentinel-1 (SAR) Only")
    sensor_choice = input("Enter choice (1/2/3): ").strip()

    if sensor_choice not in ['1', '2', '3']:
        print("❌ Invalid sensor choice. Exiting.")
        return

    if sensor_choice == '2':
        # Sentinel-2 only
        dates = [(base_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(2, -1, -1)]
        preprocessed_images = []
        for date in dates:
            raw_image = fetch_image(lat, lon, date, sensor="Sentinel-2")
            if not check_cloud_coverage(raw_image):
                print(f"☁️ High cloud coverage detected on {date}. Consider using Sentinel-1.")
            processed_image = preprocess_image(raw_image, date_str=date)
            preprocessed_images.append(processed_image)
        run_prithvi_inference(preprocessed_images)

    elif sensor_choice == '3':
        # Sentinel-1 only
        pre_date = (base_date - timedelta(days=1)).strftime("%Y-%m-%d")
        post_date = base_date.strftime("%Y-%m-%d")
        pre_vv = fetch_image(lat, lon, pre_date, sensor="Sentinel-1")
        pre_vh = fetch_image(lat, lon, pre_date, sensor="Sentinel-1")
        post_vv = fetch_image(lat, lon, post_date, sensor="Sentinel-1")
        post_vh = fetch_image(lat, lon, post_date, sensor="Sentinel-1")
        run_ai4g_sar_inference(pre_vv, pre_vh, post_vv, post_vh)

    else:
        # Automatic: try Sentinel-2 first, fallback to Sentinel-1 if cloudy
        dates = [(base_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(2, -1, -1)]
        preprocessed_images = []
        use_sentinel1 = False
        for date in dates:
            raw_image = fetch_image(lat, lon, date, sensor="Sentinel-2")
            if not check_cloud_coverage(raw_image):
                use_sentinel1 = True
                break
            processed_image = preprocess_image(raw_image, date_str=date)
            preprocessed_images.append(processed_image)
        if use_sentinel1:
            print("☁️ Cloud coverage too high for Sentinel-2. Switching to Sentinel-1 SAR model.")
            pre_date = (base_date - timedelta(days=1)).strftime("%Y-%m-%d")
            post_date = base_date.strftime("%Y-%m-%d")
            pre_vv = fetch_image(lat, lon, pre_date, sensor="Sentinel-1")
            pre_vh = fetch_image(lat, lon, pre_date, sensor="Sentinel-1")
            post_vv = fetch_image(lat, lon, post_date, sensor="Sentinel-1")
            post_vh = fetch_image(lat, lon, post_date, sensor="Sentinel-1")
            run_ai4g_sar_inference(pre_vv, pre_vh, post_vv, post_vh)
        else:
            run_prithvi_inference(preprocessed_images)

    print("\\n✅ Complete Workflow Done!")

if __name__ == "__main__":
    main()
