#!/usr/bin/env python3
"""Discover and aggregate tabular datasets in this repository.

Outputs:
- aggregation_summary.json
- aggregation_summary.csv
- aggregation_rows_per_file.svg (always)
- aggregation_rows_per_file.png (if matplotlib is available)
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List

ROOT = Path(__file__).resolve().parent
EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules"}
DATA_EXTENSIONS = {".csv", ".tsv", ".json"}


def iter_data_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        if path.name in {
            "aggregation_summary.json",
            "aggregation_summary.csv",
            "aggregate_datasets.py",
            "aggregation_rows_per_file.png",
            "aggregation_rows_per_file.svg",
        }:
            continue
        if path.suffix.lower() in DATA_EXTENSIONS:
            yield path


def safe_float(value: object):
    try:
        if value is None:
            return None
        text = str(value).strip().replace(",", "")
        if text == "":
            return None
        return float(text)
    except (ValueError, TypeError):
        return None


def aggregate_table_rows(rows: List[Dict[str, object]]) -> Dict[str, object]:
    row_count = len(rows)
    columns = sorted({k for row in rows for k in row.keys()})

    numeric_column_stats = {}
    for column in columns:
        nums = []
        for row in rows:
            number = safe_float(row.get(column))
            if number is not None:
                nums.append(number)
        if nums:
            numeric_column_stats[column] = {
                "count": len(nums),
                "sum": round(sum(nums), 6),
                "mean": round(sum(nums) / len(nums), 6),
                "min": min(nums),
                "max": max(nums),
            }

    return {
        "rows": row_count,
        "columns": columns,
        "numeric_columns": numeric_column_stats,
    }


def read_rows(path: Path) -> List[Dict[str, object]]:
    if path.suffix.lower() in {".csv", ".tsv"}:
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            return [dict(row) for row in reader]

    if path.suffix.lower() == ".json":
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return data
        return []

    return []


def write_flat_csv(summary: Dict[str, object], out_path: Path) -> None:
    fields = [
        "file",
        "rows",
        "columns_count",
        "columns",
        "numeric_columns_count",
        "numeric_columns",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for file_name, stats in summary["files"].items():
            columns = stats.get("columns", [])
            numeric_cols = sorted((stats.get("numeric_columns", {}) or {}).keys())
            writer.writerow(
                {
                    "file": file_name,
                    "rows": stats.get("rows", 0),
                    "columns_count": len(columns),
                    "columns": " | ".join(columns),
                    "numeric_columns_count": len(numeric_cols),
                    "numeric_columns": " | ".join(numeric_cols),
                }
            )


def write_rows_svg(summary: Dict[str, object], out_path: Path) -> None:
    files = list(summary["files"].keys())
    rows = [summary["files"][file]["rows"] for file in files]

    width = 900
    height = 420
    margin = 50
    chart_w = width - margin * 2
    chart_h = height - margin * 2

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width/2}" y="30" text-anchor="middle" font-size="18" font-family="Arial">Rows per dataset file</text>',
    ]

    if files:
        max_rows = max(max(rows), 1)
        bar_w = max(chart_w / max(len(files), 1) * 0.7, 10)
        gap = chart_w / max(len(files), 1)
        parts.append(f'<line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="black"/>')

        for i, (name, value) in enumerate(zip(files, rows)):
            bar_h = (value / max_rows) * (chart_h - 20)
            x = margin + i * gap + (gap - bar_w) / 2
            y = height - margin - bar_h
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{bar_h:.2f}" fill="#2E86AB"/>')
            parts.append(f'<text x="{x + bar_w/2:.2f}" y="{y - 6:.2f}" text-anchor="middle" font-size="11" font-family="Arial">{value}</text>')
            parts.append(f'<text x="{x + bar_w/2:.2f}" y="{height-margin+14}" text-anchor="middle" font-size="10" font-family="Arial" transform="rotate(20 {x + bar_w/2:.2f} {height-margin+14})">{name}</text>')
    else:
        parts.append(f'<text x="{width/2}" y="{height/2}" text-anchor="middle" font-size="14" font-family="Arial">No supported datasets found</text>')

    parts.append('</svg>')
    out_path.write_text("\n".join(parts), encoding="utf-8")


def write_rows_plot(summary: Dict[str, object], out_path: Path) -> bool:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return False

    files = list(summary["files"].keys())
    rows = [summary["files"][file]["rows"] for file in files]

    fig, ax = plt.subplots(figsize=(10, 5))
    if files:
        ax.bar(range(len(files)), rows, color="#2E86AB")
        ax.set_xticks(range(len(files)))
        ax.set_xticklabels(files, rotation=45, ha="right")
        ax.set_ylabel("Rows")
        ax.set_title("Rows per dataset file")
    else:
        ax.text(0.5, 0.5, "No supported datasets found", ha="center", va="center", fontsize=12)
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def main() -> int:
    files = sorted(iter_data_files(ROOT))

    per_file = {}
    total_rows = 0
    for file_path in files:
        rel = str(file_path.relative_to(ROOT))
        rows = read_rows(file_path)
        stats = aggregate_table_rows(rows)
        total_rows += stats["rows"]
        per_file[rel] = stats

    summary = {
        "files_detected": len(files),
        "total_rows": total_rows,
        "files": per_file,
        "note": "No supported datasets were found." if not files else "Aggregation complete.",
    }

    json_out_path = ROOT / "aggregation_summary.json"
    json_out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    csv_out_path = ROOT / "aggregation_summary.csv"
    write_flat_csv(summary, csv_out_path)

    svg_out_path = ROOT / "aggregation_rows_per_file.svg"
    write_rows_svg(summary, svg_out_path)

    plot_out_path = ROOT / "aggregation_rows_per_file.png"
    plot_written = write_rows_plot(summary, plot_out_path)

    print(f"Wrote summary JSON to {json_out_path}")
    print(f"Wrote summary CSV to {csv_out_path}")
    print(f"Wrote visualization SVG to {svg_out_path}")
    if plot_written:
        print(f"Wrote visualization PNG to {plot_out_path}")
    else:
        print("Visualization PNG skipped: matplotlib is unavailable in this environment")
    print(f"Files detected: {len(files)} | Total rows: {total_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
