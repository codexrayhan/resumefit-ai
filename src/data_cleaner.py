"""Step 1: clean and process the raw ResumeFit AI CSV files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

_NON_ALNUM_RE = re.compile(r"[^a-zA-Z0-9\s]")
_WHITESPACE_RE = re.compile(r"\s+")


def clean_text(value: object) -> str:
    """Lowercase text, remove symbols, and normalize whitespace."""
    if pd.isna(value):
        return ""
    text = _NON_ALNUM_RE.sub(" ", str(value).lower())
    return _WHITESPACE_RE.sub(" ", text).strip()


def process_resumes(raw_dir: Path, processed_dir: Path) -> Path:
    """Clean resume text and category labels for model training."""
    source = raw_dir / "resumes.csv"
    destination = processed_dir / "resumes_clean.csv"
    if not source.exists():
        raise FileNotFoundError(f"Missing raw dataset: {source}")

    print("\n[1/2] Cleaning resumes.csv")
    resumes = pd.read_csv(source, usecols=["Resume", "Category"])
    original_rows = len(resumes)
    resumes = resumes.dropna(subset=["Resume", "Category"])
    resumes["Resume"] = resumes["Resume"].map(clean_text)
    resumes["Category"] = resumes["Category"].map(clean_text)
    resumes = resumes[(resumes["Resume"] != "") & (resumes["Category"] != "")]
    category_counts = resumes["Category"].value_counts()
    resumes = resumes[
        resumes["Category"].isin(category_counts[category_counts >= 10].index)
    ]

    processed_dir.mkdir(parents=True, exist_ok=True)
    resumes.to_csv(destination, index=False)
    print(f"Rows kept: {len(resumes):,} / {original_rows:,}")
    print("Categories retained (minimum 10 resumes each): "
          f"{resumes['Category'].nunique()}")
    print(f"Saved: {destination}")
    return destination


def process_job_descriptions(
    raw_dir: Path, processed_dir: Path, chunk_size: int
) -> Path:
    """Process the large job-description CSV without loading it all at once."""
    source = raw_dir / "job_descriptions.csv"
    destination = processed_dir / "job_descriptions_clean.csv"
    if not source.exists():
        raise FileNotFoundError(f"Missing raw dataset: {source}")

    columns = ["Job Description", "skills", "Responsibilities"]
    print("\n[2/2] Processing job_descriptions.csv in chunks")
    processed_dir.mkdir(parents=True, exist_ok=True)
    first_chunk = True
    total_rows = 0

    for chunk in pd.read_csv(source, usecols=columns, chunksize=chunk_size):
        for column in columns:
            chunk[column] = chunk[column].fillna("").astype(str)
        chunk["full_jd_text"] = (
            chunk["Job Description"] + " "
            + chunk["skills"] + " "
            + chunk["Responsibilities"]
        ).map(clean_text)
        chunk.to_csv(
            destination,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False,
        )
        first_chunk = False
        total_rows += len(chunk)
        print(f"Processed rows: {total_rows:,}", end="\r")

    if first_chunk:
        raise ValueError("The job description dataset is empty.")
    print(f"\nRows processed: {total_rows:,}")
    print(f"Saved: {destination}")
    return destination


def main() -> None:
    """Run both CSV cleaning operations from the command line."""
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Clean ResumeFit AI resume and job-description CSV files."
    )
    parser.add_argument("--raw-dir", type=Path, default=root / "data" / "raw")
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=root / "data" / "processed",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10_000,
        help="Rows read at a time from job_descriptions.csv.",
    )
    args = parser.parse_args()
    if args.chunk_size < 1:
        parser.error("--chunk-size must be at least 1")

    print("ResumeFit New | Data cleaning and processing")
    process_resumes(args.raw_dir, args.processed_dir)
    process_job_descriptions(args.raw_dir, args.processed_dir, args.chunk_size)
    print("\nData cleaning completed successfully.")


if __name__ == "__main__":
    main()
