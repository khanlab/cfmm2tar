#!/usr/bin/env python3
"""
CLI script for cfmm2tar - Download a tarballed DICOM dataset from the CFMM DICOM server

Author: Ali Khan, YingLi Lu
Date: 2017-11-21
Updated: 2024 (Python 3 conversion)
"""

import argparse
import getpass
import os
import sys
import tempfile

# Import the main function from retrieve_cfmm_tar module
from cfmm2tar import retrieve_cfmm_tar


def read_credentials(credentials_file):
    """Read UWO credentials from file."""
    try:
        with open(credentials_file) as f:
            lines = f.read().splitlines()
            if len(lines) >= 2:
                return lines[0], lines[1]
    except FileNotFoundError:
        pass
    return None, None


def parse_metadata_tags(metadata_tags_list):
    """
    Parse metadata tags from CLI arguments.

    Args:
        metadata_tags_list: List of strings in format "TAG:NAME" (e.g., ["00100030:PatientBirthDate"])

    Returns:
        dict: Dictionary mapping DICOM tags to field names (e.g., {"00100030": "PatientBirthDate"})
    """
    if not metadata_tags_list:
        return {}

    additional_tags = {}
    for tag_spec in metadata_tags_list:
        if ":" not in tag_spec:
            print(
                f"Warning: Invalid tag format '{tag_spec}'. Expected TAG:NAME format. Skipping.",
                file=sys.stderr,
            )
            continue

        tag, name = tag_spec.split(":", 1)
        tag = tag.strip().upper().replace(" ", "")
        name = name.strip()

        if not tag or not name:
            print(
                f"Warning: Invalid tag format '{tag_spec}'. Both tag and name must be non-empty. Skipping.",
                file=sys.stderr,
            )
            continue

        additional_tags[tag] = name

    return additional_tags


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Retrieves studies from dicom server based on Principal^Project, Date and/or PatientName. "
        "If no search strings provided, all studies are downloaded. "
        "Uses credentials in ~/.uwo_credentials (line1: username, line2: password) or prompts for username/password",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -d '20170530' output_dir
      All scans on specific date

  %(prog)s -d '20170530-' output_dir
      All scans since date

  %(prog)s -d '20170530-20170827' output_dir
      All scans in date range

  %(prog)s -p 'Khan^NeuroAnalytics' output_dir
      Specific Principal^Project on all dates

  %(prog)s -n '*subj01*' output_dir
      Specific PatientName search

  %(prog)s -u '12345.123456.123.1234567' output_dir
      Specific StudyInstanceUID

  %(prog)s -u '12345.123456.123.1234567' -u '98765.987654.987.9876543' output_dir
      Multiple StudyInstanceUIDs

  %(prog)s -m -p 'Khan^NeuroAnalytics' -d '20170530' output_dir
      Query and write study metadata to TSV file (no download)

  %(prog)s -m --metadata-tags 00100030:PatientBirthDate -d '20170530' output_dir
      Query metadata with additional DICOM tag (PatientBirthDate)

  %(prog)s --from-metadata study_metadata.tsv output_dir
      Download studies using UIDs from metadata file

  %(prog)s --temp-dir /scratch/$USER/cfmm2tar_temp -n '*subj01*' output_dir
      Specify temporary directory for intermediate files
        """,
    )

    # Optional options
    parser.add_argument(
        "-m",
        "--metadata-only",
        dest="metadata_only",
        action="store_true",
        help="Only query and write metadata to study_metadata.tsv (no download). Can later use with --from-metadata to download.",
    )
    parser.add_argument(
        "--from-metadata",
        dest="from_metadata",
        default="",
        help="Path to metadata TSV file containing StudyInstanceUIDs to download (one per line or TSV with StudyInstanceUID column)",
    )
    parser.add_argument(
        "-c",
        "--credentials",
        dest="credentials_file",
        default=os.path.expanduser("~/.uwo_credentials"),
        help="Path to uwo_credentials file (default: ~/.uwo_credentials)",
    )
    parser.add_argument(
        "--temp-dir",
        dest="temp_dir",
        default="",
        help="Path to temporary directory for intermediate DICOM files (default: system temp directory)",
    )
    parser.add_argument(
        "--dcm4che-server",
        dest="dicom_connection",
        default=os.environ.get("DICOM_CONNECTION", "CFMM@dicom.cfmm.uwo.ca:11112"),
        help="DICOM server connection string (default: from DICOM_CONNECTION env var or CFMM@dicom.cfmm.uwo.ca:11112)",
    )
    parser.add_argument(
        "--dcm4che-options",
        dest="dcm4che_options",
        default=os.environ.get("OTHER_OPTIONS", ""),
        help="Other options to pass to dcm4che tools (default: from OTHER_OPTIONS env var)",
    )
    parser.add_argument(
        "--refresh-trust-store",
        dest="refresh_trust_store",
        action="store_true",
        help="Force refresh the cached JKS trust store used for TLS connections",
    )
    parser.add_argument(
        "--tls-cipher",
        dest="tls_cipher",
        default="TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
        help="TLS cipher suite for dcm4che tools (default: TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384)",
    )
    parser.add_argument(
        "--skip-derived",
        dest="skip_derived",
        action="store_true",
        help="Skip DICOM files with ImageType containing DERIVED (e.g., reformats, derived images)",
    )
    parser.add_argument(
        "--gzip",
        dest="use_gzip",
        action="store_true",
        help="Create gzip-compressed tar files (.tar.gz instead of .tar)",
    )
    parser.add_argument(
        "--metadata-tags",
        dest="metadata_tags",
        action="append",
        default=None,
        help="Additional DICOM tags to include in metadata TSV. Format: TAG:NAME (e.g., 00100030:PatientBirthDate). Can be specified multiple times.",
    )

    # Search options
    parser.add_argument(
        "-d",
        "--date",
        dest="date_search",
        default="-",
        help='Date search string (default: "-" for all dates)',
    )
    parser.add_argument(
        "-n",
        "--name",
        dest="name_search",
        default="*",
        help='PatientName search string (default: "*" for all names)',
    )
    parser.add_argument(
        "-p",
        "--description",
        dest="study_search",
        default="*",
        help='Study description / Principal^Project search string (default: "*" for all)',
    )
    parser.add_argument(
        "-u",
        "--uid",
        dest="study_instance_uid",
        action="append",
        default=None,
        help="StudyInstanceUID (can be specified multiple times; Note: this will override other search options)",
    )

    # Required positional argument
    parser.add_argument(
        "output_dir",
        help="Output directory for retrieved DICOM data (required)",
    )

    args = parser.parse_args()

    # Parse additional metadata tags
    additional_tags = parse_metadata_tags(args.metadata_tags)

    # Setup output directory
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Handle metadata-only mode (query and write to TSV, no download)
    if args.metadata_only:
        # We'll need credentials for query even in metadata mode
        username, password = read_credentials(args.credentials_file)

        if username is None or password is None:
            username = input("UWO Username: ")
            password = getpass.getpass("UWO Password: ")

        # Import here to access Dcm4cheUtils
        from cfmm2tar import dcm4che_utils

        # Create dcm4che utils instance
        cfmm_dcm4che_utils = dcm4che_utils.Dcm4cheUtils(
            args.dicom_connection,
            username,
            password,
            args.dcm4che_options,
            force_refresh_trust_store=args.refresh_trust_store,
            tls_cipher=args.tls_cipher,
        )

        # Build matching key
        matching_key = f"-m StudyDescription='{args.study_search}' -m StudyDate='{args.date_search}' -m PatientName='{args.name_search}'"

        # Get study metadata
        print("Querying study metadata with search criteria:")
        print(f"  Principal^Project: {args.study_search}")
        print(f"  Date: {args.date_search}")
        print(f"  PatientName: {args.name_search}")
        if additional_tags:
            print(
                f"  Additional tags: {', '.join(f'{tag}:{name}' for tag, name in additional_tags.items())}"
            )

        studies = cfmm_dcm4che_utils.get_study_metadata_by_matching_key(
            matching_key, additional_tags
        )

        if not studies:
            print("No studies found matching the search criteria.")
            sys.exit(0)

        print(f"Found {len(studies)} studies")

        # Write to TSV file in output_dir
        metadata_file = os.path.join(output_dir, "study_metadata.tsv")
        import csv

        with open(metadata_file, "w", newline="") as f:
            # Build fieldnames: default fields plus any additional tags
            fieldnames = [
                "StudyInstanceUID",
                "PatientName",
                "PatientID",
                "StudyDate",
                "StudyDescription",
            ]
            # Add additional tag field names in consistent order
            if additional_tags:
                fieldnames.extend(sorted(additional_tags.values()))

            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            for study in studies:
                writer.writerow(study)

        print(f"Study metadata written to: {metadata_file}")
        print("\nTo download these studies later, use:")
        print(f"  cfmm2tar --from-metadata {metadata_file} {output_dir}")
        sys.exit(0)

    # Handle from-metadata mode (download specific UIDs from file)
    study_instance_uids = args.study_instance_uid  # This is now a list or None
    if args.from_metadata:
        # Read UIDs from file
        uids = []
        with open(args.from_metadata) as f:
            lines = f.readlines()

        # Check if it's a TSV with header
        if lines and "\t" in lines[0]:
            # TSV format - look for StudyInstanceUID column
            import csv

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

        if not uids:
            print(f"No StudyInstanceUIDs found in {args.from_metadata}")
            sys.exit(1)

        print(f"Will download {len(uids)} studies from {args.from_metadata}")
        study_instance_uids = uids
    elif study_instance_uids:
        # UIDs provided via -u flag
        print(f"Will download {len(study_instance_uids)} studies by UID")

    # Read or prompt for credentials
    username, password = read_credentials(args.credentials_file)

    if username is None or password is None:
        username = input("UWO Username: ")
        password = getpass.getpass("UWO Password: ")

    # Setup directories
    output_dir = args.output_dir
    temp_dir = args.temp_dir

    # Use system temp directory if not specified
    if not temp_dir:
        temp_dir = os.path.join(tempfile.gettempdir(), "cfmm2tar_temp")

    # Create directories
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    # Always save metadata to output_dir/study_metadata.tsv during download
    metadata_tsv_filename = os.path.join(output_dir, "study_metadata.tsv")

    # Call the main retrieve function
    keep_sorted_dicom = False

    try:
        if study_instance_uids:
            # Download each UID (from -u flag or --from-metadata)
            for i, uid in enumerate(study_instance_uids):
                print(f"\nDownloading study {i + 1}/{len(study_instance_uids)}: {uid}")
                retrieve_cfmm_tar.main(
                    uwo_username=username,
                    uwo_password=password,
                    connect=args.dicom_connection,
                    PI_matching_key=args.study_search,
                    retrieve_dest_dir=temp_dir,
                    keep_sorted_dest_dir_flag=keep_sorted_dicom,
                    tar_dest_dir=output_dir,
                    study_date=args.date_search,
                    patient_name=args.name_search,
                    study_instance_uid=uid,
                    other_options=args.dcm4che_options,
                    downloaded_uids_filename="",
                    metadata_tsv_filename=metadata_tsv_filename,
                    force_refresh_trust_store=args.refresh_trust_store,
                    skip_derived=args.skip_derived,
                    additional_tags=additional_tags,
                    tls_cipher=args.tls_cipher,
                    use_gzip=args.use_gzip,
                )
        else:
            # Normal mode - use search criteria (no specific UIDs provided)
            retrieve_cfmm_tar.main(
                uwo_username=username,
                uwo_password=password,
                connect=args.dicom_connection,
                PI_matching_key=args.study_search,
                retrieve_dest_dir=temp_dir,
                keep_sorted_dest_dir_flag=keep_sorted_dicom,
                tar_dest_dir=output_dir,
                study_date=args.date_search,
                patient_name=args.name_search,
                study_instance_uid="*",
                other_options=args.dcm4che_options,
                downloaded_uids_filename="",
                metadata_tsv_filename=metadata_tsv_filename,
                force_refresh_trust_store=args.refresh_trust_store,
                skip_derived=args.skip_derived,
                additional_tags=additional_tags,
                tls_cipher=args.tls_cipher,
                use_gzip=args.use_gzip,
            )

        # Clean up temp directory if empty
        try:
            os.rmdir(temp_dir)
        except OSError:
            # Directory not empty, that's fine
            pass

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
