import os
import sys
import torch
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling

# Add the absolute path to the 'models' directory to sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models')))

import torch.serialization
import pathlib
from ai4g_flood.src.utils.model import load_model
from ai4g_flood.src.utils.image_processing import db_scale, pad_to_nearest, create_patches, reconstruct_image_from_patches

def reproject_image(image, src_crs, src_transform, dst_crs, dst_transform, dst_shape):
    image = image.astype('float32')  # Reproject requires float32
    reprojected, _ = reproject(
        image,
        np.empty(dst_shape, dtype='float32'),
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=Resampling.nearest
    )
    return reprojected

def save_prediction(pred_image, output_filename, crs, transform):
    pred_image[pred_image == 0] = np.nan
    with rasterio.open(output_filename, 'w', driver='GTiff', height=pred_image.shape[0], width=pred_image.shape[1],
                       count=1, dtype=pred_image.dtype, crs=crs, transform=transform, compress='lzw', nodata=np.nan) as dst:
        dst.write(pred_image, 1)

def calculate_flood_change(vv_pre, vh_pre, vv_post, vh_post, params):
    vv_change = ((vv_post < params['vv_threshold']) & 
                 (vv_pre > params['vv_threshold']) & 
                 ((vv_pre - vv_post) > params['delta_amplitude'])).astype(int)
    vh_change = ((vh_post < params['vh_threshold']) & 
                 (vh_pre > params['vh_threshold']) & 
                 ((vh_pre - vh_post) > params['delta_amplitude'])).astype(int)
    
    zero_index = ((vv_post < params['vv_min_threshold']) | 
                  (vv_pre < params['vv_min_threshold']) | 
                  (vh_post < params['vh_min_threshold']) | 
                  (vh_pre < params['vh_min_threshold']))
    vv_change[zero_index] = 0
    vh_change[zero_index] = 0
    return np.stack((vv_change, vh_change), axis=2)

def read_and_preprocess(file_path, scale_factor):
    with rasterio.open(file_path) as src:
        if scale_factor == 1:
            image = src.read(1)
        else:
            image = src.read(
                1,
                out_shape=(
                    src.count,
                    int(src.height * scale_factor),
                    int(src.width * scale_factor)
                ),
                resampling=Resampling.bilinear
            )
        transform = src.transform * src.transform.scale(
            (src.width / image.shape[-1]),
            (src.height / image.shape[-2])
        )
        image = db_scale(image)
        return image, src.crs, transform

def run_ai4g_sar_inference(pre_vv, pre_vh, post_vv, post_vh, output_dir='./backend/data/results', model_path='./models/ai4g_flood/models/ai4g_sar_model.ckpt'):
    """
    Run AI4G SAR flood inference on the given pre and post event VV and VH images.
    Arguments:
        pre_vv, pre_vh, post_vv, post_vh: file paths to the SAR images
        output_dir: directory to save the output prediction
        model_path: path to the trained AI4G SAR model checkpoint
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Read and preprocess images
    vv_pre, vv_pre_crs, vv_pre_transform = read_and_preprocess(pre_vv, 1.0)
    vh_pre, vh_pre_crs, vh_pre_transform = read_and_preprocess(pre_vh, 1.0)
    vv_post, vv_post_crs, vv_post_transform = read_and_preprocess(post_vv, 1.0)
    vh_post, vh_post_crs, vh_post_transform = read_and_preprocess(post_vh, 1.0)

    # Use vv_post shape as the target shape
    target_shape = vv_post.shape

    # Reproject images to the same CRS and transform
    vv_pre = reproject_image(vv_pre, vv_pre_crs, vv_pre_transform, vv_post_crs, vv_post_transform, target_shape)
    vh_pre = reproject_image(vh_pre, vh_pre_crs, vh_pre_transform, vv_post_crs, vv_post_transform, target_shape)
    vh_post = reproject_image(vh_post, vh_post_crs, vh_post_transform, vv_post_crs, vv_post_transform, target_shape)

    # Calculate flood change mask
    params = {
        'vv_threshold': 100,
        'vh_threshold': 90,
        'delta_amplitude': 10,
        'vv_min_threshold': 75,
        'vh_min_threshold': 70
    }
    flood_change = calculate_flood_change(vv_pre, vh_pre, vv_post, vh_post, params)

    # Prepare input for the model
    input_size = 128
    flood_change = pad_to_nearest(flood_change, input_size, [0, 1])
    patches = create_patches(flood_change, (input_size, input_size), input_size)

    # Load model without weights_only argument, safe_globals handled in load_model
    model = load_model(model_path, device, in_channels=2, n_classes=2)
    model.eval()

    # Run inference
    predictions = []
    with torch.no_grad():
        for i in range(0, len(patches), 1024):
            batch = patches[i:i+1024]
            if len(batch) == 0:
                continue
            batch_tensor = torch.from_numpy(np.array(batch)).to(device)
            if device.type == 'cuda':
                batch_tensor = batch_tensor.half()
            else:
                batch_tensor = batch_tensor.float()
            output = model(batch_tensor)
            _, predicted = torch.max(output, 1)
            predicted = (predicted * 255).to(torch.int)
            if not True:  # keep_all_predictions is False
                predicted[(batch_tensor[:, 0] == 0) + (batch_tensor[:, 1] == 0)] = 0
            predictions.extend(predicted.cpu().numpy())

    # Reconstruct the image
    pred_image, _ = reconstruct_image_from_patches(predictions, flood_change.shape[:2], (input_size, input_size), input_size)
    pred_image = pred_image[:target_shape[0], :target_shape[1]]  # Crop to original size

    # Save the result
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, 'ai4g_flood_prediction.tif')
    save_prediction(pred_image, output_filename, vv_post_crs, vv_post_transform)
    print(f"AI4G SAR flood prediction saved to {output_filename}")
