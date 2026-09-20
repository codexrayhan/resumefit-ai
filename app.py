"""Step 1 runner: process the datasets and train the ResumeFit AI model."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.data_cleaner import process_job_descriptions, process_resumes
from src.model_trainer import train_classifier

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument(
        "--processed-dir", type=Path, default=ROOT / "data" / "processed"
    )
    parser.add_argument("--models-dir", type=Path, default=ROOT / "models")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10_000,
        help="Rows read at a time from job_descriptions.csv.",
    )
    args = parser.parse_args()
    if args.chunk_size < 1:
        parser.error("--chunk-size must be at least 1")

    print("ResumeFit New | Step 1: data cleaning, processing, and training")
    resumes_path = process_resumes(args.raw_dir, args.processed_dir)
    process_job_descriptions(args.raw_dir, args.processed_dir, args.chunk_size)
    train_classifier(resumes_path, args.models_dir)
    print("\nStep 1 completed successfully.")


if __name__ == "__main__":
    main()
