from datetime import datetime, timedelta

from .cloud_coverage import CloudCoverageError, calculate_cloud_coverage
from .config import CLOUD_COVERAGE_THRESHOLD

def check_cloud_coverage(image_path, *, threshold=None, coverage_fn=calculate_cloud_coverage, verbose=True):
    """Return a tuple ``(is_clear, coverage_fraction)``.

    When coverage cannot be measured the function conservatively returns
    ``is_clear = False`` and ``coverage_fraction = float('nan')`` so that the
    Sentinel-1 fallback is triggered instead of silently assuming clear skies.
    """

    threshold = CLOUD_COVERAGE_THRESHOLD if threshold is None else threshold
    try:
        coverage = float(coverage_fn(image_path))
    except CloudCoverageError as exc:
        if verbose:
            print(
                f"⚠️ Unable to measure cloud coverage for {image_path}: {exc}. "
                "Falling back to Sentinel-1."
            )
        return False, float("nan")

    if not (0.0 <= coverage <= 1.0) or coverage != coverage:  # NaN check via self-inequality
        if verbose:
            print(
                f"⚠️ Invalid cloud coverage value {coverage!r} for {image_path}. "
                "Treating scene as cloudy."
            )
        return False, float("nan")

    if verbose:
        print(
            f"☁️ Cloud coverage for {image_path}: {coverage * 100:.2f}% "
            f"(threshold {threshold * 100:.2f}%)"
        )
    return coverage < threshold, coverage

def main():
    from data_fetcher import fetch_image
    from preprocess import preprocess_image
    from model_inference import run_flood_detection as run_prithvi_inference
    from ai4g_inference import run_ai4g_sar_inference
    from geopy.geocoders import Nominatim

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
            is_clear, coverage = check_cloud_coverage(raw_image)
            if not is_clear:
                print(f"☁️ High cloud coverage detected on {date}: {coverage * 100:.2f}%")
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
            is_clear, coverage = check_cloud_coverage(raw_image)
            if not is_clear:
                use_sentinel1 = True
                print(f"☁️ Cloud coverage {coverage * 100:.2f}% exceeds threshold. Switching to Sentinel-1.")
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
