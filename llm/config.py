import os

# Sentinel Hub credentials (replace with your actual credentials)
SENTINEL_HUB_CLIENT_ID = "8dad49a1-81bf-4ce7-82f0-d5c90b461bee"
SENTINEL_HUB_CLIENT_SECRET = "IllXbv8V3M9GlQjvxvBfFxJ2x16HAp1h"

# Directly Setting Sentinel Hub Credentials (Environment Variables)
os.environ["SH_CLIENT_ID"] = SENTINEL_HUB_CLIENT_ID
os.environ["SH_CLIENT_SECRET"] = SENTINEL_HUB_CLIENT_SECRET

# Model Configuration (Paths)
PRITHVI_MODEL_PATH = "models/prithvi_transformers/Prithvi-EO-1.0-100M/Prithvi_EO_V1_100M.pt"
PRITHVI_CONFIG_PATH = "models/prithvi_transformers/Prithvi-EO-1.0-100M/config.yaml"

# Data Directories
RAW_IMAGE_DIR = "data/raw/"
PROCESSED_IMAGE_DIR = "data/processed/"
RESULTS_DIR = "data/results/"

# Ensure directories exist
os.makedirs(RAW_IMAGE_DIR, exist_ok=True)
os.makedirs(PROCESSED_IMAGE_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

CLOUD_COVERAGE_THRESHOLD = float(os.getenv("CLOUD_COVERAGE_THRESHOLD", "0.3"))
