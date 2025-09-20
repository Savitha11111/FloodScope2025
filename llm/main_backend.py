import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from ai4g_inference import run_ai4g_sar_inference
from cloud_coverage import calculate_cloud_coverage
from data_fetcher import fetch_image
from model_inference import run_flood_detection as run_prithvi_inference
from geopy.geocoders import Nominatim
from preprocess import preprocess_image


logger = logging.getLogger(__name__)


DEFAULT_CLOUD_THRESHOLD = 0.3


@dataclass
class CloudCoverageStatus:
    """Outcome of a cloud coverage measurement."""

    coverage: Optional[float]
    is_clear: Optional[bool]
    error: Optional[str] = None


@dataclass
class OpticalPreparationResult:
    """Summary of preparing Sentinel-2 imagery for inference."""

    use_sentinel1: bool
    preprocessed_images: List[str]
    fallback_reason: Optional[str] = None
    fallback_date: Optional[str] = None
    fallback_coverage: Optional[float] = None


def check_cloud_coverage(image_path: str, threshold: float = DEFAULT_CLOUD_THRESHOLD) -> CloudCoverageStatus:
    """Evaluate cloud coverage for a Sentinel-2 scene.

    Args:
        image_path: Path to the downloaded Sentinel-2 image.
        threshold: Maximum acceptable cloud coverage ratio.

    Returns:
        CloudCoverageStatus describing the measurement outcome.
    """

    try:
        coverage = calculate_cloud_coverage(image_path)
    except Exception as exc:  # pragma: no cover - exception path validated via unit tests
        logger.exception("Unable to determine cloud coverage for %s", image_path)
        return CloudCoverageStatus(coverage=None, is_clear=None, error=str(exc))

    if coverage is None:
        message = "Cloud coverage calculation returned no value"
        logger.error("%s for %s", message, image_path)
        return CloudCoverageStatus(coverage=None, is_clear=None, error=message)

    is_clear = coverage <= threshold
    logger.debug(
        "Calculated cloud coverage %.2f%% for %s (threshold %.2f%%)",
        coverage * 100,
        image_path,
        threshold * 100,
    )
    return CloudCoverageStatus(coverage=coverage, is_clear=is_clear)


def prepare_optical_imagery(
    lat: float,
    lon: float,
    base_date: datetime,
    *,
    fetch_fn: Callable[[float, float, str, str], str] = fetch_image,
    preprocess_fn: Callable[[str, str], str] = preprocess_image,
    coverage_fn: Callable[[str], CloudCoverageStatus] = check_cloud_coverage,
) -> OpticalPreparationResult:
    """Fetch and preprocess Sentinel-2 imagery, reporting if radar fallback is required."""

    dates = [(base_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(2, -1, -1)]
    preprocessed_images: List[str] = []

    for date in dates:
        raw_image = fetch_fn(lat, lon, date, sensor="Sentinel-2")
        status = coverage_fn(raw_image)

        if status.error:
            logger.warning(
                "Falling back to Sentinel-1 because cloud coverage could not be assessed for %s: %s",
                date,
                status.error,
            )
            return OpticalPreparationResult(
                use_sentinel1=True,
                preprocessed_images=[],
                fallback_reason=status.error,
                fallback_date=date,
            )

        if not status.is_clear:
            logger.info(
                "Falling back to Sentinel-1 due to %.2f%% cloud coverage on %s",
                status.coverage * 100 if status.coverage is not None else float("nan"),
                date,
            )
            return OpticalPreparationResult(
                use_sentinel1=True,
                preprocessed_images=[],
                fallback_reason="high cloud coverage",
                fallback_date=date,
                fallback_coverage=status.coverage,
            )

        processed_image = preprocess_fn(raw_image, date_str=date)
        preprocessed_images.append(processed_image)

    return OpticalPreparationResult(use_sentinel1=False, preprocessed_images=preprocessed_images)

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
        optical_result = prepare_optical_imagery(lat, lon, base_date)
        if optical_result.use_sentinel1:
            print(
                "⚠️ Unable to obtain reliable cloud coverage for Sentinel-2 on {}. "
                "Please rerun with Sentinel-1 (SAR) for guaranteed observations.".format(
                    optical_result.fallback_date or base_date.strftime("%Y-%m-%d")
                )
            )
            return

        run_prithvi_inference(optical_result.preprocessed_images)

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
        # Automatic: try Sentinel-2 first, fallback to Sentinel-1 if cloudy or uncertain
        optical_result = prepare_optical_imagery(lat, lon, base_date)
        if optical_result.use_sentinel1:
            if optical_result.fallback_reason:
                print(
                    "☁️ Switching to Sentinel-1 SAR model because Sentinel-2 imagery on {date} "
                    "was unavailable or too cloudy ({reason}).".format(
                        date=optical_result.fallback_date or base_date.strftime("%Y-%m-%d"),
                        reason=(
                            f"{optical_result.fallback_coverage * 100:.1f}% cloud cover"
                            if optical_result.fallback_coverage is not None
                            else optical_result.fallback_reason
                        ),
                    )
                )
            else:
                print("☁️ Cloud coverage too high for Sentinel-2. Switching to Sentinel-1 SAR model.")

            pre_date = (base_date - timedelta(days=1)).strftime("%Y-%m-%d")
            post_date = base_date.strftime("%Y-%m-%d")
            pre_vv = fetch_image(lat, lon, pre_date, sensor="Sentinel-1")
            pre_vh = fetch_image(lat, lon, pre_date, sensor="Sentinel-1")
            post_vv = fetch_image(lat, lon, post_date, sensor="Sentinel-1")
            post_vh = fetch_image(lat, lon, post_date, sensor="Sentinel-1")
            run_ai4g_sar_inference(pre_vv, pre_vh, post_vv, post_vh)
        else:
            run_prithvi_inference(optical_result.preprocessed_images)

    print("\\n✅ Complete Workflow Done!")

if __name__ == "__main__":
    main()
