# Dataset Aggregation Report

I scanned the repository for supported dataset files (`.csv`, `.tsv`, `.json`) and aggregated the detected records.

## Result

- **Datasets found:** 0
- **Total rows processed:** 0
- **Status:** No supported datasets are currently present in this repository.

## Generated artifacts

- `aggregation_summary.json` (machine-readable nested summary)
- `aggregation_summary.csv` (flat, spreadsheet-friendly summary)
- `aggregation_rows_per_file.svg` (data visualization of row counts by file)
- `aggregation_rows_per_file.png` (optional, generated only if `matplotlib` is available)

## How to rerun

```bash
python3 aggregate_datasets.py
```

When dataset files are added, rerunning the script will update all summary and visualization artifacts with the latest repository contents.
