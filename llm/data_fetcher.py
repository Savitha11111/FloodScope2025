import os
from datetime import datetime, timedelta
import numpy as np
import rasterio
from rasterio.transform import from_origin
from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, CRS, BBox

from .config import (
    RAW_IMAGE_DIR,
    SENTINEL_HUB_CLIENT_ID,
    SENTINEL_HUB_CLIENT_SECRET,
    require_sentinel_hub_credentials,
)

# Sentinel Hub Configuration
config = SHConfig()

# Updated evalscript for Sentinel-2 with 6 bands: B02, B03, B04, B08, B11, B12
EVALSCRIPT_SENTINEL2_6BANDS = """
//VERSION=3
function setup() {
  return {
    input: ["B02", "B03", "B04", "B08", "B11", "B12"],
    output: { bands: 6 }
  };
}
function evaluatePixel(sample) {
  return [sample.B02, sample.B03, sample.B04, sample.B08, sample.B11, sample.B12];
}
"""

# Minimal evalscript for Sentinel-1 SAR VV and VH bands
EVALSCRIPT_SENTINEL1_VV_VH = """
//VERSION=3
function setup() {
  return {
    input: ["VV", "VH"],
    output: { bands: 2 }
  };
}
function evaluatePixel(sample) {
  return [sample.VV, sample.VH];
}
"""

def fetch_image(lat, lon, date, sensor="Sentinel-2"):
    """
    Fetches a real-time image from Sentinel-2 or Sentinel-1 using Sentinel Hub API.
    """
    require_sentinel_hub_credentials()
    config.sh_client_id = SENTINEL_HUB_CLIENT_ID
    config.sh_client_secret = SENTINEL_HUB_CLIENT_SECRET
    print(f"\nFetching Real-Time {sensor} Image using Sentinel Hub...")

    bbox = BBox([lon - 0.01, lat - 0.01, lon + 0.01, lat + 0.01], CRS.WGS84)
    collection = DataCollection.SENTINEL2_L2A if sensor == "Sentinel-2" else DataCollection.SENTINEL1_IW

    input_data = [
        SentinelHubRequest.input_data(
            data_collection=collection,
            time_interval=(date, date)
        )
    ]

    evalscript = EVALSCRIPT_SENTINEL2_6BANDS if sensor == "Sentinel-2" else EVALSCRIPT_SENTINEL1_VV_VH

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=input_data,
        bbox=bbox,
        config=config,
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)]
    )

    image = request.get_data()[0]

    # Save multi-band image using rasterio
    image_path = os.path.join(RAW_IMAGE_DIR, f"{sensor}_{lat}_{lon}_{date}.tiff")

    height, width, bands = image.shape
    transform = from_origin(lon - 0.01, lat + 0.01, 0.0001, 0.0001)  # approximate transform

    with rasterio.open(
        image_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=bands,
        dtype=image.dtype,
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        for i in range(bands):
            dst.write(image[:, :, i], i + 1)

    print(f"✅ Image saved at: {image_path}")
    return image_path
