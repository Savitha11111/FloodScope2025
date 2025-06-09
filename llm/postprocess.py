import cv2
import os
import numpy as np
from config import RESULTS_DIR

def postprocess_mask(mask_path):
    """
    Postprocesses the flood mask (remove noise, refine).
    """
    print("\n🌀 Postprocessing Flood Mask:", mask_path)
    
    # Load the Flood Mask
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise FileNotFoundError(f"\n❌ Mask Not Found: {mask_path}")

    # Apply Morphological Operations (Remove Noise)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask_cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask_cleaned = cv2.morphologyEx(mask_cleaned, cv2.MORPH_CLOSE, kernel)
    
    # Save the Cleaned Mask
    cleaned_mask_path = os.path.join(RESULTS_DIR, "cleaned_flood_mask.png")
    cv2.imwrite(cleaned_mask_path, mask_cleaned)
    
    print("\n✅ Cleaned Flood Mask Saved:", cleaned_mask_path)
    return cleaned_mask_path
