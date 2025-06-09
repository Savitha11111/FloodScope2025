import os
import subprocess
from config import PRITHVI_MODEL_PATH, PRITHVI_CONFIG_PATH, RESULTS_DIR

def run_flood_detection(image_paths):
    print("\\n🚀 Running Prithvi Model for Flood Detection...")
    data_files_str = " ".join(image_paths)
    command = f"""
    python3 models/prithvi_transformers/Prithvi-EO-1.0-100M/inference.py \\
        --config_path {PRITHVI_CONFIG_PATH} \\
        --checkpoint {PRITHVI_MODEL_PATH} \\
        --output_dir {RESULTS_DIR} \\
        --rgb_outputs \\
        --data_files {data_files_str}
    """
    subprocess.run(command, shell=True, check=True)
    print("\\n✅ Flood Mask Saved in:", RESULTS_DIR)
