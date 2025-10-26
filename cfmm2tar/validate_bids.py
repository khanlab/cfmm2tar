#!/usr/bin/env python3
"""
BIDS Validator wrapper for cfmm2tar.

This module provides functionality to validate BIDS datasets using bids-validator-deno.
It can be used as a standalone script or integrated into pre-commit hooks.

Author: cfmm2tar contributors
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def find_bids_datasets(search_path="."):
    """
    Find BIDS datasets by looking for dataset_description.json files.

    Args:
        search_path: Path to search for BIDS datasets (default: current directory)

    Returns:
        List of Path objects pointing to BIDS dataset directories
    """
    search_path = Path(search_path).resolve()
    bids_datasets = []

    # Look for dataset_description.json files
    for desc_file in search_path.rglob("dataset_description.json"):
        # The parent directory of dataset_description.json is the BIDS root
        bids_root = desc_file.parent
        bids_datasets.append(bids_root)

    return bids_datasets


def validate_bids_dataset(dataset_path, validator_path="bids-validator-deno"):
    """
    Validate a BIDS dataset using bids-validator-deno.

    Args:
        dataset_path: Path to the BIDS dataset root directory
        validator_path: Path to bids-validator-deno executable (default: "bids-validator-deno")

    Returns:
        tuple: (success: bool, stdout: str, stderr: str)
    """
    dataset_path = Path(dataset_path).resolve()

    if not dataset_path.exists():
        return False, "", f"Dataset path does not exist: {dataset_path}"

    if not (dataset_path / "dataset_description.json").exists():
        return (
            False,
            "",
            f"Not a valid BIDS dataset (missing dataset_description.json): {dataset_path}",
        )

    try:
        # Run bids-validator-deno
        result = subprocess.run(
            [validator_path, str(dataset_path)],
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception on non-zero exit
        )

        success = result.returncode == 0
        return success, result.stdout, result.stderr

    except FileNotFoundError:
        return (
            False,
            "",
            f"bids-validator-deno not found. Install it with: pip install bids-validator-deno",
        )
    except Exception as e:
        return False, "", f"Error running validator: {e}"


def main():
    """Main entry point for the BIDS validator script."""
    parser = argparse.ArgumentParser(
        description="Validate BIDS datasets using bids-validator-deno",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/bids/dataset
      Validate a specific BIDS dataset

  %(prog)s --search /path/to/search
      Find and validate all BIDS datasets in a directory tree

  %(prog)s
      Find and validate all BIDS datasets in the current directory
        """,
    )

    parser.add_argument(
        "dataset",
        nargs="?",
        default=None,
        help="Path to BIDS dataset to validate (optional if using --search)",
    )

    parser.add_argument(
        "--search",
        dest="search_path",
        default=None,
        help="Search for BIDS datasets in this directory and validate all found datasets",
    )

    parser.add_argument(
        "--validator",
        dest="validator_path",
        default="bids-validator-deno",
        help="Path to bids-validator-deno executable (default: bids-validator-deno)",
    )

    args = parser.parse_args()

    # Determine what to validate
    datasets_to_validate = []

    if args.dataset:
        # Validate a specific dataset
        datasets_to_validate.append(Path(args.dataset))
    elif args.search_path:
        # Search for datasets
        datasets_to_validate = find_bids_datasets(args.search_path)
    else:
        # Search in current directory
        datasets_to_validate = find_bids_datasets(".")

    if not datasets_to_validate:
        print("No BIDS datasets found.", file=sys.stderr)
        return 0  # Not an error if no datasets found

    # Validate each dataset
    all_valid = True
    for dataset in datasets_to_validate:
        print(f"\nValidating BIDS dataset: {dataset}")
        print("=" * 80)

        success, stdout, stderr = validate_bids_dataset(dataset, args.validator_path)

        if stdout:
            print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)

        if success:
            print(f"✓ Dataset is valid: {dataset}")
        else:
            print(f"✗ Dataset validation failed: {dataset}", file=sys.stderr)
            all_valid = False

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
