# External Model Assets

FloodScope2025 integrates two vendor-provided inference stacks that are not bundled with the repository. Use the notes below to acquire and stage the models before running optical or radar inference.

## IBM–NASA Prithvi EO-1.0 (Optical)
1. Create (or sign in to) a Hugging Face account and navigate to [ibm-nasa-geospatial/Prithvi-100M](https://huggingface.co/ibm-nasa-geospatial/Prithvi-100M).
2. Accept the terms of use and download the `Prithvi_EO_V1_100M.pt` checkpoint together with its configuration YAML and inference script.
3. Place the files under `models/prithvi_transformers/Prithvi-EO-1.0-100M/` so that:
   ```
   models/prithvi_transformers/Prithvi-EO-1.0-100M/
     Prithvi_EO_V1_100M.pt
     config.yaml
     inference.py (optional helper from the official repo)
   ```
4. Update `llm/config.py` if you change filenames, and verify the setup using the smoke test in `models/prithvi_transformers/test_prithvi_model.py` once weights are available.

## Microsoft AI4Flood (SAR)
1. Clone or download the [microsoft/ai4g-floods](https://github.com/microsoft/ai4g-floods) repository.
2. Copy the `src/` utilities that implement inference (e.g., `src/utils/model.py`, `src/utils/image_processing.py`) into `models/ai4g_flood/`.
3. Download the published SAR checkpoint (`ai4g_sar_model.ckpt`) and place it inside `models/ai4g_flood/models/`.
4. Update `llm/ai4g_inference.py` paths if necessary and run the planned regression test (`tests/test_ai4flood_smoke.py`, to be added when weights are staged) to confirm integration.

Keep large artifacts out of Git; the repository only tracks lightweight configuration and helper scripts. Record SHA256 checksums for reproducibility and store them alongside the downloaded files.
