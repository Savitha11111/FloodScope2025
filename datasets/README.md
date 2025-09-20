# Benchmark Datasets for FloodScope2025

The dual-model flood mapping workflow relies on three public benchmarks that pair Sentinel-1 radar, Sentinel-2 optical, and authoritative flood annotations. These datasets are **not** redistributed with the repository because of licensing and storage limits; instead, use the documented scripts to download and prepare them directly from the official sources.

## Dataset Overview

| Dataset | Modality | Contents | License / Access | Raw Size (approx.) |
|---------|----------|----------|------------------|--------------------|
| **Sen1Floods11** | Sentinel-1 (VV/VH), Sentinel-2 (RGB/NIR), flood masks | 4,840 paired pre-/post-event chips | [IEEE DataPort](https://ieee-dataport.org/open-access/sen1floods11) (free registration) | 18 GB |
| **FloodNet** | High-resolution aerial RGB imagery | 234 annotated tiles across flood classes | [Official site](https://floodnet.ai) (form submission) | 12 GB |
| **Copernicus EMS Flood Maps** | Vector & raster flood delineations | Event-specific shapefiles/rasters | [Copernicus EMS](https://emergency.copernicus.eu) (open access) | Varies per event (0.5–2 GB each) |

All datasets should be staged in the `datasets/` directory using the structure below:

```
datasets/
  sen1floods11/
    raw/
    interim/
    processed/
  floodnet/
    raw/
    interim/
    processed/
  copernicus_ems/
    raw/
    interim/
    processed/
  metadata/
    sen1floods11_scenes.csv
    floodnet_tiles.csv
    copernicus_events.csv
```

* `raw/` holds the downloaded archives and original files.
* `interim/` contains temporary extraction outputs.
* `processed/` houses harmonised GeoTIFF chips, masks, and metadata ready for model ingestion.
* `metadata/` stores consolidated CSV manifests with spatial/temporal metadata for evaluation and threshold studies.

## Download Workflow

Use the provided scripts to fetch each dataset into the correct location:

```bash
# Sen1Floods11 (requires manual asset link or pre-downloaded archive)
python datasets/download_sen1floods11.py \
  --output-root datasets/sen1floods11 \
  --manual-archive /path/to/Sen1Floods11.zip

# FloodNet
python datasets/download_floodnet.py --output-root datasets/floodnet

# Copernicus EMS (example event)
python datasets/download_copernicus_ems.py --event-id EMSR452 --output-root datasets/copernicus_ems
```

Each script streams the official archives, verifies checksums, and logs provenance into `datasets/metadata/`. Some sources require manual authentication; in those cases the script prompts for API tokens or uses previously downloaded archives that you supply via the `--manual-archive` flag.

After download, run the preprocessing utilities to harmonise the data with the evaluation pipeline:

```bash
python datasets/processing/sen1floods11.py --output-root datasets/sen1floods11
python datasets/processing/floodnet.py --output-root datasets/floodnet
python datasets/processing/copernicus_ems.py --output-root datasets/copernicus_ems
```

The processing stage generates chips in a consistent CRS (EPSG:4326), resamples bands to 10 m, assembles multi-sensor stacks, and exports metadata CSVs summarising each tile (cloud coverage, acquisition times, labels).

## Provenance & Integrity Tracking

* Each download script records SHA256 checksums in `datasets/metadata/checksums_<dataset>.txt` to ensure data integrity.
* Licenses and citation details are appended to `datasets/metadata/LICENSES.md` so downstream notebooks can reference them automatically.
* The preprocessing utilities emit coverage reports (`*_coverage.json`) with statistics on class balance, geographic spread, and cloud distributions to support the CloudAnalyzer threshold study.

## Disk Space Requirements

Plan for roughly 80 GB of free disk space to hold all raw archives, intermediate tiles, and processed evaluation chips. The preprocessing scripts expose `--keep-intermediate` to delete `interim/` data once harmonisation is complete.

## Citation

Please cite the original authors when publishing results:

* Bonafilia et al., *Sen1Floods11: A georeferenced dataset to train and test deep learning flood algorithms for Sentinel-1* (2020).
* Rahnemoonfar et al., *FloodNet: A High Resolution Aerial Imagery Dataset for Post Flood Scene Understanding* (2021).
* European Commission, *Copernicus Emergency Management Service Mapping*.  

Refer to `datasets/metadata/LICENSES.md` for full citation text.
