# models/prithvi_transformers/model_loader.py

from transformers import AutoConfig, AutoModelForSemanticSegmentation, AutoProcessor

def load_prithvi_model():
    """
    Loads the IBM-NASA Prithvi Model (Sentinel-2) using Transformers.
    """
    print("\n🚀 Loading IBM-NASA Prithvi Model (Sentinel-2) using Transformers...")
    
    # Directly specify num_labels and label mappings in the config dictionary
    model_id = "ibm-nasa-geospatial/Prithvi-EO-1.0-100M"
    try:
        config = AutoConfig.from_pretrained(
            model_id,
            num_labels=2,
            id2label={0: "Non-Flooded", 1: "Flooded"},
            label2id={"Non-Flooded": 0, "Flooded": 1},
            trust_remote_code=True,
        )
        model = AutoModelForSemanticSegmentation.from_pretrained(
            model_id, config=config, trust_remote_code=True
        )
        processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    except Exception as exc:  # pragma: no cover - executed when weights unavailable offline
        raise RuntimeError(
            "Failed to load the Prithvi model from Hugging Face. Download the official "
            "checkpoint from IBM-NASA or set PRITHVI_MODEL_PATH to a local directory."
        ) from exc

    print("✅ IBM-NASA Prithvi Model Loaded Successfully with num_labels = 2 (Binary Classification)")
    return model, processor
