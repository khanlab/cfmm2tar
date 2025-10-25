#!/usr/bin/env python3
"""
Example script demonstrating the cfmm2tar Python API.

This script shows various ways to use the cfmm2tar API for querying
and downloading DICOM studies programmatically.
"""

import os
from getpass import getpass

from cfmm2tar import download_studies, download_studies_from_metadata, query_metadata


def example_query_metadata():
    """Example: Query study metadata."""
    print("=" * 60)
    print("Example 1: Query study metadata")
    print("=" * 60)

    username = input("UWO Username: ")
    password = getpass("UWO Password: ")

    # Query studies as list of dicts
    studies = query_metadata(
        username=username,
        password=password,
        study_description="Khan^*",  # All Khan lab projects
        study_date="20240101-20240131",  # January 2024
        return_type="list",
    )

    print(f"\nFound {len(studies)} studies")
    for i, study in enumerate(studies[:5], 1):  # Show first 5
        print(f"{i}. {study['StudyDate']}: {study['StudyDescription']}")
        print(f"   UID: {study['StudyInstanceUID']}")
        print(f"   Patient: {study['PatientName']}")

    if len(studies) > 5:
        print(f"   ... and {len(studies) - 5} more")


def example_query_metadata_dataframe():
    """Example: Query study metadata as DataFrame."""
    print("\n" + "=" * 60)
    print("Example 2: Query metadata as pandas DataFrame")
    print("=" * 60)

    try:
        import pandas as pd
    except ImportError:
        print("pandas is not installed. Install with: pip install pandas")
        return

    username = input("UWO Username: ")
    password = getpass("UWO Password: ")

    # Query studies as DataFrame
    df = query_metadata(
        username=username,
        password=password,
        study_description="*",
        study_date="20240101-",  # All studies since Jan 2024
        return_type="dataframe",
    )

    print(f"\nFound {len(df)} studies")
    print("\nFirst few rows:")
    print(df.head())

    # Example analysis
    print("\nStudies per month:")
    df["Month"] = pd.to_datetime(df["StudyDate"], format="%Y%m%d").dt.to_period("M")
    print(df.groupby("Month").size())


def example_download_studies():
    """Example: Download studies by search criteria."""
    print("\n" + "=" * 60)
    print("Example 3: Download studies by search criteria")
    print("=" * 60)

    username = input("UWO Username: ")
    password = getpass("UWO Password: ")
    output_dir = input("Output directory: ")

    # Download studies
    print("\nDownloading studies...")
    result_dir = download_studies(
        username=username,
        password=password,
        output_dir=output_dir,
        study_description="Khan^TestProject",
        study_date="20240101",
        patient_name="*subj01*",
    )

    print(f"\nStudies downloaded to: {result_dir}")
    print(f"Metadata saved to: {os.path.join(result_dir, 'study_metadata.tsv')}")


def example_query_then_download():
    """Example: Complete workflow - query then download filtered studies."""
    print("\n" + "=" * 60)
    print("Example 4: Query then download filtered studies")
    print("=" * 60)

    try:
        import pandas as pd  # noqa: F401
    except ImportError:
        print("pandas is not installed. Install with: pip install pandas")
        return

    username = input("UWO Username: ")
    password = getpass("UWO Password: ")
    output_dir = input("Output directory: ")

    # Step 1: Query all available studies
    print("\nStep 1: Querying available studies...")
    studies_df = query_metadata(
        username=username,
        password=password,
        study_description="Khan^*",
        study_date="20240101-20240131",
        return_type="dataframe",
    )

    print(f"Found {len(studies_df)} total studies")
    print("\nAll studies:")
    print(studies_df[["StudyDate", "PatientName", "StudyDescription"]])

    # Step 2: Filter studies (example: only certain patients)
    print("\nStep 2: Filtering studies...")
    filtered_df = studies_df[studies_df["PatientName"].str.contains("subj0[1-3]", regex=True)]

    print(f"Filtered to {len(filtered_df)} studies")
    print("\nFiltered studies:")
    print(filtered_df[["StudyDate", "PatientName", "StudyDescription"]])

    # Ask for confirmation
    confirm = input("\nDownload these studies? (y/n): ")
    if confirm.lower() != "y":
        print("Download cancelled")
        return

    # Step 3: Download the filtered studies
    print("\nStep 3: Downloading filtered studies...")
    download_studies_from_metadata(
        username=username,
        password=password,
        output_dir=output_dir,
        metadata=filtered_df,
    )

    print(f"\nDownload complete! Studies saved to: {output_dir}")


def example_download_from_file():
    """Example: Download from a metadata TSV file."""
    print("\n" + "=" * 60)
    print("Example 5: Download from metadata file")
    print("=" * 60)

    username = input("UWO Username: ")
    password = getpass("UWO Password: ")
    metadata_file = input("Path to metadata TSV file: ")
    output_dir = input("Output directory: ")

    # Download from file
    print("\nDownloading studies from metadata file...")
    download_studies_from_metadata(
        username=username,
        password=password,
        output_dir=output_dir,
        metadata=metadata_file,
    )

    print(f"\nDownload complete! Studies saved to: {output_dir}")


def example_download_multiple_uids():
    """Example: Download multiple studies by UID."""
    print("\n" + "=" * 60)
    print("Example 6: Download multiple studies by UID")
    print("=" * 60)

    username = input("UWO Username: ")
    password = getpass("UWO Password: ")
    output_dir = input("Output directory: ")

    # Download multiple studies by UID
    study_uids = [
        "1.2.840.113619.2.55.3.1234567890.123",
        "1.2.840.113619.2.55.3.9876543210.456",
        "1.2.840.113619.2.55.3.1111111111.789",
    ]

    print(f"\nDownloading {len(study_uids)} studies by UID...")
    result_dir = download_studies(
        username=username,
        password=password,
        output_dir=output_dir,
        study_instance_uid=study_uids,
    )

    print(f"\nStudies downloaded to: {result_dir}")
    print(f"Metadata saved to: {os.path.join(result_dir, 'study_metadata.tsv')}")


def main():
    """Run examples."""
    print("cfmm2tar Python API Examples")
    print("=" * 60)
    print()
    print("Select an example to run:")
    print("1. Query study metadata (list)")
    print("2. Query study metadata (DataFrame)")
    print("3. Download studies by search criteria")
    print("4. Query then download filtered studies (complete workflow)")
    print("5. Download from metadata file")
    print("6. Download multiple studies by UID")
    print("0. Exit")
    print()

    choice = input("Enter choice (0-6): ")

    if choice == "1":
        example_query_metadata()
    elif choice == "2":
        example_query_metadata_dataframe()
    elif choice == "3":
        example_download_studies()
    elif choice == "4":
        example_query_then_download()
    elif choice == "5":
        example_download_from_file()
    elif choice == "6":
        example_download_multiple_uids()
    elif choice == "0":
        print("Exiting")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
