# models/prithvi_transformers/model_loader.py

from transformers import AutoModel, AutoProcessor, AutoConfig

def load_prithvi_model():
    """
    Loads the IBM-NASA Prithvi Model (Sentinel-2) using Transformers.
    """
    print("\n🚀 Loading IBM-NASA Prithvi Model (Sentinel-2) using Transformers...")
    
    # Directly specify num_labels and label mappings in the config dictionary
    config = AutoConfig.from_pretrained(
        "ibm-nasa-geospatial/Prithvi-EO-1.0-100M",
        num_labels=2,
        id2label={0: "Non-Flooded", 1: "Flooded"},
        label2id={"Non-Flooded": 0, "Flooded": 1}
    )
    
    # Load model with config
    model = AutoModel.from_pretrained("ibm-nasa-geospatial/Prithvi-EO-1.0-100M", config=config)
    processor = AutoProcessor.from_pretrained("ibm-nasa-geospatial/Prithvi-EO-1.0-100M")
    
    print("✅ IBM-NASA Prithvi Model Loaded Successfully with num_labels = 2 (Binary Classification)")
    return model, processor
