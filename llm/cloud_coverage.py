import rasterio
import numpy as np

import rasterio
import numpy as np

def calculate_cloud_coverage(image_path):
    """
    Calculate cloud coverage percentage using a simple brightness threshold heuristic on Sentinel-2 bands.
    Args:
        image_path (str): Path to the Sentinel-2 image (GeoTIFF).
    Returns:
        float: Estimated cloud coverage ratio (0 to 1).
    """
    try:
        with rasterio.open(image_path) as src:
            # Read bands: B02 (blue), B03 (green), B04 (red), B08 (NIR)
            blue = src.read(1).astype(float)
            green = src.read(2).astype(float)
            red = src.read(3).astype(float)
            nir = src.read(4).astype(float)

            # Normalize bands to 0-1 range assuming 12-bit data (0-4095)
            blue /= 4095.0
            green /= 4095.0
            red /= 4095.0
            nir /= 4095.0

            # Simple cloud detection heuristic: high reflectance in visible bands and low NDVI
            ndvi = (nir - red) / (nir + red + 1e-6)
            brightness = (blue + green + red) / 3.0

            cloud_mask = (brightness > 0.3) & (ndvi < 0.1)

            cloud_pixels = np.sum(cloud_mask)
            total_pixels = cloud_mask.size
            cloud_coverage = cloud_pixels / total_pixels
            return cloud_coverage
    except Exception as e:
        print(f"Error calculating cloud coverage: {e}")
        return 0.0
