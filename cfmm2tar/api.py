#!/usr/bin/env python3
"""
Python API for cfmm2tar - programmatic access to DICOM download functionality.

This module provides a Python API that can be used as an alternative to the CLI,
suitable for use in Python scripts or Snakemake workflows.
"""

import os
import tempfile
from typing import Any

from . import dcm4che_utils, retrieve_cfmm_tar


def _get_credentials(username: str | None = None, password: str | None = None) -> tuple[str, str]:
    """
    Get credentials from various sources in order of precedence.

    Order of precedence:
    1. Provided username/password parameters
    2. ~/.uwo_credentials file
    3. Environment variables (UWO_USERNAME, UWO_PASSWORD)

    Args:
        username: Optional username (takes precedence if provided)
        password: Optional password (takes precedence if provided)

    Returns:
        Tuple of (username, password)

    Raises:
        ValueError: If credentials cannot be found from any source
    """
    # If both provided, use them
    if username is not None and password is not None:
        return username, password

    # Try to read from credentials file
    credentials_file = os.path.expanduser("~/.uwo_credentials")
    if os.path.exists(credentials_file):
        try:
            with open(credentials_file) as f:
                lines = f.read().splitlines()
                if len(lines) >= 2:
                    file_username = lines[0].strip()
                    file_password = lines[1].strip()
                    # Use file credentials for any missing values
                    if username is None:
                        username = file_username
                    if password is None:
                        password = file_password
        except Exception:
            pass  # Continue to environment variables if file reading fails

    # Try environment variables for any still-missing values
    if username is None:
        username = os.environ.get("UWO_USERNAME")
    if password is None:
        password = os.environ.get("UWO_PASSWORD")

    # Validate we have both
    if username is None or password is None:
        raise ValueError(
            "Credentials not found. Please provide username/password, "
            "create ~/.uwo_credentials file (line 1: username, line 2: password), "
            "or set UWO_USERNAME and UWO_PASSWORD environment variables."
        )

    return username, password


def query_metadata(
    username: str | None = None,
    password: str | None = None,
    study_description: str = "*",
    study_date: str = "-",
    patient_name: str = "*",
    dicom_server: str = "CFMM@dicom.cfmm.uwo.ca:11112",
    dcm4che_options: str = "",
    force_refresh_trust_store: bool = False,
    return_type: str = "list",
) -> list[dict[str, Any]] | Any:
    """
    Query study metadata from the DICOM server without downloading files.

    This function queries the DICOM server and returns study metadata. It can return
    results as either a list of dictionaries or as a pandas DataFrame (if pandas is installed).

    Credentials are obtained in the following order of precedence:
    1. Provided username/password parameters
    2. ~/.uwo_credentials file (line 1: username, line 2: password)
    3. Environment variables (UWO_USERNAME, UWO_PASSWORD)

    Args:
        username: UWO username for authentication (optional, see credential precedence above)
        password: UWO password for authentication (optional, see credential precedence above)
        study_description: Study description / Principal^Project search string (default: "*" for all)
        study_date: Date search string (default: "-" for all dates)
                   Can be a single date (YYYYMMDD), date range (YYYYMMDD-YYYYMMDD),
                   or open-ended (YYYYMMDD- for all dates since)
        patient_name: PatientName search string (default: "*" for all names)
        dicom_server: DICOM server connection string (default: "CFMM@dicom.cfmm.uwo.ca:11112")
        dcm4che_options: Additional options to pass to dcm4che tools (default: "")
        force_refresh_trust_store: Force refresh the cached JKS trust store (default: False)
        return_type: Return type - either "list" for list of dicts or "dataframe" for pandas DataFrame
                    (default: "list")

    Returns:
        If return_type="list": List of dictionaries, each containing:
            - StudyInstanceUID: Unique identifier for the study
            - PatientName: Patient name
            - PatientID: Patient ID
            - StudyDate: Date of the study (YYYYMMDD format)
            - StudyDescription: Study description (typically Principal^Project)

        If return_type="dataframe": pandas DataFrame with the same columns
            (requires pandas to be installed)

    Raises:
        ValueError: If credentials cannot be found from any source
        ImportError: If return_type="dataframe" but pandas is not installed
        Exception: If there are errors connecting to the DICOM server

    Example:
        Using credentials from ~/.uwo_credentials:
        >>> from cfmm2tar.api import query_metadata
        >>> studies = query_metadata(
        ...     study_description="Khan^NeuroAnalytics",
        ...     study_date="20240101-20240131"
        ... )
        >>> print(f"Found {len(studies)} studies")

        Providing credentials explicitly:
        >>> studies = query_metadata(
        ...     username="myuser",
        ...     password="mypass",
        ...     study_description="Khan^NeuroAnalytics",
        ...     study_date="20240101-20240131"
        ... )

        Using with DataFrame:
        >>> import pandas as pd
        >>> df = query_metadata(
        ...     study_description="Khan^*",
        ...     return_type="dataframe"
        ... )
        >>> print(df.head())
    """
    # Get credentials
    username, password = _get_credentials(username, password)

    # Validate return_type
    if return_type not in ["list", "dataframe"]:
        raise ValueError(f"return_type must be 'list' or 'dataframe', got: {return_type}")

    # If dataframe requested, check if pandas is available
    if return_type == "dataframe":
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas is required for return_type='dataframe'. "
                "Install it with: pip install pandas"
            ) from e

    # Create dcm4che utils instance
    cfmm_dcm4che_utils = dcm4che_utils.Dcm4cheUtils(
        dicom_server,
        username,
        password,
        dcm4che_options,
        force_refresh_trust_store=force_refresh_trust_store,
    )

    # Build matching key
    matching_key = f"-m StudyDescription='{study_description}' -m StudyDate='{study_date}' -m PatientName='{patient_name}'"

    # Get study metadata
    studies = cfmm_dcm4che_utils.get_study_metadata_by_matching_key(matching_key)

    # Return based on requested type
    if return_type == "dataframe":
        return pd.DataFrame(studies)
    else:
        return studies


def download_studies(
    output_dir: str,
    username: str | None = None,
    password: str | None = None,
    study_description: str = "*",
    study_date: str = "-",
    patient_name: str = "*",
    study_instance_uid: str = "*",
    temp_dir: str | None = None,
    dicom_server: str = "CFMM@dicom.cfmm.uwo.ca:11112",
    dcm4che_options: str = "",
    force_refresh_trust_store: bool = False,
    keep_sorted_dicom: bool = False,
) -> str:
    """
    Download DICOM studies from the server and create tar archives.

    This function downloads DICOM studies matching the specified criteria and creates
    tar archives in the output directory. Study metadata is automatically saved to
    a TSV file in the output directory.

    Credentials are obtained in the following order of precedence:
    1. Provided username/password parameters
    2. ~/.uwo_credentials file (line 1: username, line 2: password)
    3. Environment variables (UWO_USERNAME, UWO_PASSWORD)

    Args:
        output_dir: Output directory for tar archives and metadata
        username: UWO username for authentication (optional, see credential precedence above)
        password: UWO password for authentication (optional, see credential precedence above)
        study_description: Study description / Principal^Project search string (default: "*" for all)
        study_date: Date search string (default: "-" for all dates)
        patient_name: PatientName search string (default: "*" for all names)
        study_instance_uid: Specific StudyInstanceUID to download (default: "*")
                           If specified, this overrides other search criteria
        temp_dir: Temporary directory for intermediate DICOM files (default: system temp)
        dicom_server: DICOM server connection string (default: "CFMM@dicom.cfmm.uwo.ca:11112")
        dcm4che_options: Additional options to pass to dcm4che tools (default: "")
        force_refresh_trust_store: Force refresh the cached JKS trust store (default: False)
        keep_sorted_dicom: Keep the sorted DICOM files after creating tar (default: False)

    Returns:
        Path to the output directory containing the downloaded tar files

    Raises:
        ValueError: If credentials cannot be found from any source
        Exception: If there are errors downloading or processing the studies

    Example:
        Using credentials from ~/.uwo_credentials:
        >>> from cfmm2tar.api import download_studies
        >>> output = download_studies(
        ...     output_dir="/path/to/output",
        ...     study_description="Khan^NeuroAnalytics",
        ...     study_date="20240101"
        ... )
        >>> print(f"Downloaded studies to: {output}")

        Providing credentials explicitly:
        >>> output = download_studies(
        ...     output_dir="/path/to/output",
        ...     username="myuser",
        ...     password="mypass",
        ...     study_description="Khan^NeuroAnalytics",
        ...     study_date="20240101"
        ... )

        Download a specific study by UID:
        >>> download_studies(
        ...     output_dir="/path/to/output",
        ...     study_instance_uid="1.2.840.113619.2.55.3.1234567890.123"
        ... )
    """
    # Get credentials
    username, password = _get_credentials(username, password)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Setup temp directory
    if temp_dir is None:
        temp_dir = os.path.join(tempfile.gettempdir(), "cfmm2tar_temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Metadata file path
    metadata_tsv_filename = os.path.join(output_dir, "study_metadata.tsv")

    # Call the main retrieve function
    retrieve_cfmm_tar.main(
        uwo_username=username,
        uwo_password=password,
        connect=dicom_server,
        PI_matching_key=study_description,
        retrieve_dest_dir=temp_dir,
        keep_sorted_dest_dir_flag=keep_sorted_dicom,
        tar_dest_dir=output_dir,
        study_date=study_date,
        patient_name=patient_name,
        study_instance_uid=study_instance_uid,
        other_options=dcm4che_options,
        downloaded_uids_filename="",
        metadata_tsv_filename=metadata_tsv_filename,
        force_refresh_trust_store=force_refresh_trust_store,
    )

    # Clean up temp directory if empty
    try:
        os.rmdir(temp_dir)
    except OSError:
        # Directory not empty, that's fine
        pass

    return output_dir


def download_studies_from_metadata(
    output_dir: str,
    metadata: str | list[dict[str, Any]] | Any,
    username: str | None = None,
    password: str | None = None,
    temp_dir: str | None = None,
    dicom_server: str = "CFMM@dicom.cfmm.uwo.ca:11112",
    dcm4che_options: str = "",
    force_refresh_trust_store: bool = False,
    keep_sorted_dicom: bool = False,
) -> str:
    """
    Download DICOM studies using UIDs from metadata.

    This function downloads studies specified by StudyInstanceUIDs from either a
    metadata file (TSV), a list of dictionaries, or a pandas DataFrame.

    Credentials are obtained in the following order of precedence:
    1. Provided username/password parameters
    2. ~/.uwo_credentials file (line 1: username, line 2: password)
    3. Environment variables (UWO_USERNAME, UWO_PASSWORD)

    Args:
        output_dir: Output directory for tar archives and metadata
        metadata: Either:
                 - Path to TSV metadata file with StudyInstanceUID column
                 - List of dictionaries with 'StudyInstanceUID' key
                 - pandas DataFrame with 'StudyInstanceUID' column
        username: UWO username for authentication (optional, see credential precedence above)
        password: UWO password for authentication (optional, see credential precedence above)
        temp_dir: Temporary directory for intermediate DICOM files (default: system temp)
        dicom_server: DICOM server connection string (default: "CFMM@dicom.cfmm.uwo.ca:11112")
        dcm4che_options: Additional options to pass to dcm4che tools (default: "")
        force_refresh_trust_store: Force refresh the cached JKS trust store (default: False)
        keep_sorted_dicom: Keep the sorted DICOM files after creating tar (default: False)

    Returns:
        Path to the output directory containing the downloaded tar files

    Raises:
        ValueError: If credentials or metadata format is invalid, or no StudyInstanceUIDs found
        Exception: If there are errors downloading or processing the studies

    Example:
        Using a TSV file with credentials from ~/.uwo_credentials:
        >>> from cfmm2tar.api import download_studies_from_metadata
        >>> download_studies_from_metadata(
        ...     output_dir="/path/to/output",
        ...     metadata="study_metadata.tsv"
        ... )

        Providing credentials explicitly:
        >>> download_studies_from_metadata(
        ...     output_dir="/path/to/output",
        ...     metadata="study_metadata.tsv",
        ...     username="myuser",
        ...     password="mypass"
        ... )

        Using a DataFrame:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     'StudyInstanceUID': ['1.2.3.4', '5.6.7.8'],
        ...     'PatientName': ['Patient1', 'Patient2']
        ... })
        >>> download_studies_from_metadata(
        ...     output_dir="/path/to/output",
        ...     metadata=df
        ... )

        Using a list of dicts:
        >>> studies = [
        ...     {'StudyInstanceUID': '1.2.3.4', 'PatientName': 'Patient1'},
        ...     {'StudyInstanceUID': '5.6.7.8', 'PatientName': 'Patient2'}
        ... ]
        >>> download_studies_from_metadata(
        ...     output_dir="/path/to/output",
        ...     metadata=studies
        ... )
    """
    # Get credentials
    username, password = _get_credentials(username, password)

    # Extract UIDs based on metadata type
    uids = []

    if isinstance(metadata, str):
        # metadata is a file path
        import csv

        with open(metadata) as f:
            lines = f.readlines()

        # Check if it's a TSV with header
        if lines and "\t" in lines[0]:
            reader = csv.DictReader(lines, delimiter="\t")
            for row in reader:
                if "StudyInstanceUID" in row:
                    uid = row["StudyInstanceUID"].strip()
                    if uid:
                        uids.append(uid)
        else:
            # Simple text file, one UID per line
            for line in lines:
                uid = line.strip()
                if uid:
                    uids.append(uid)

    elif isinstance(metadata, list):
        # metadata is a list of dicts
        for item in metadata:
            if isinstance(item, dict) and "StudyInstanceUID" in item:
                uid = str(item["StudyInstanceUID"]).strip()
                if uid:
                    uids.append(uid)
            else:
                raise ValueError(
                    "Each item in metadata list must be a dict with 'StudyInstanceUID' key"
                )

    else:
        # Try to treat as pandas DataFrame
        try:
            # Check if it has the pandas DataFrame interface
            if hasattr(metadata, "to_dict") and "StudyInstanceUID" in metadata.columns:
                uids = metadata["StudyInstanceUID"].astype(str).tolist()
                uids = [uid.strip() for uid in uids if uid.strip()]
            else:
                raise ValueError(
                    "metadata must be a file path (str), list of dicts, or pandas DataFrame"
                )
        except AttributeError:
            raise ValueError(
                "metadata must be a file path (str), list of dicts, or pandas DataFrame"
            )

    if not uids:
        raise ValueError("No StudyInstanceUIDs found in metadata")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Setup temp directory
    if temp_dir is None:
        temp_dir = os.path.join(tempfile.gettempdir(), "cfmm2tar_temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Metadata file path
    metadata_tsv_filename = os.path.join(output_dir, "study_metadata.tsv")

    # Download each study
    for i, uid in enumerate(uids):
        print(f"\nDownloading study {i + 1}/{len(uids)}: {uid}")
        retrieve_cfmm_tar.main(
            uwo_username=username,
            uwo_password=password,
            connect=dicom_server,
            PI_matching_key="*",
            retrieve_dest_dir=temp_dir,
            keep_sorted_dest_dir_flag=keep_sorted_dicom,
            tar_dest_dir=output_dir,
            study_date="-",
            patient_name="*",
            study_instance_uid=uid,
            other_options=dcm4che_options,
            downloaded_uids_filename="",
            metadata_tsv_filename=metadata_tsv_filename,
            force_refresh_trust_store=force_refresh_trust_store,
        )

    # Clean up temp directory if empty
    try:
        os.rmdir(temp_dir)
    except OSError:
        # Directory not empty, that's fine
        pass

    return output_dir
