import os
import numpy as np
import rasterio
from rasterio.enums import Resampling
from config import PROCESSED_IMAGE_DIR

def preprocess_image(image_path, date_str=None):
    print(f"\\n🔧 Preprocessing Image: {image_path}")
    
    with rasterio.open(image_path) as src:
        image = src.read(
            out_shape=(
                src.count,
                224,
                224
            ),
            resampling=Resampling.bilinear
        )
        image = np.transpose(image, (1, 2, 0))
        profile = src.profile

    if date_str:
        processed_image_path = os.path.join(PROCESSED_IMAGE_DIR, f"preprocessed_image_{date_str}.tiff")
    else:
        processed_image_path = os.path.join(PROCESSED_IMAGE_DIR, "preprocessed_image.tiff")

    profile.update({
        'height': 224,
        'width': 224,
        'transform': rasterio.transform.from_bounds(*src.bounds, 224, 224),
        'count': image.shape[2],
        'dtype': image.dtype
    })

    with rasterio.open(processed_image_path, 'w', **profile) as dst:
        dst.write(np.transpose(image, (2, 0, 1)))

    print(f"✅ Preprocessed Image Saved: {processed_image_path}")
    return processed_image_path
