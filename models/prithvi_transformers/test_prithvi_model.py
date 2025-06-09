# test_prithvi_model.py

from transformers import AutoModel, AutoProcessor
import torch

# Local import (your model loader function)
from model_loader import load_prithvi_model

# Load the Prithvi model and processor
print("\n🚀 Loading IBM-NASA Prithvi Model (Sentinel-2) using Transformers...")
model, processor = load_prithvi_model()

# Confirm model loading
print("✅ Model and Processor loaded successfully.")

# Set model to evaluation mode
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

# Sample test with a placeholder image (replace with actual test image path)
from PIL import Image

image_path = "sample_image.png"  # Replace with your test image path
image = Image.open(image_path)

# Preprocess the image
inputs = processor(images=image, return_tensors="pt").to(device)

# Make a prediction
with torch.no_grad():
    outputs = model(**inputs)

# Display the output
print("\n🔍 Model Output:", outputs)

# Post-process (if needed, depending on model type)

print("✅ Test completed.")