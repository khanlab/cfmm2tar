#!/usr/bin/env ython3
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
from pathlib import Path

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


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Retrieves studies from dicom server based on Principal^Project, Date and/or PatientName. "
        "If no search strings provided, all studies are downloaded. "
        "Uses credentials in ~/.uwo_credentials (line1: username, line2: password) or prompts for username/password",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -d '20170530' myfolder
      All scans on specific date

  %(prog)s -d '20170530-' myfolder
      All scans since date

  %(prog)s -d '20170530-20170827' myfolder
      All scans in date range

  %(prog)s -p 'Khan^NeuroAnalytics' myfolder
      Specific Principal^Project on all dates

  %(prog)s -n '*subj01*' myfolder
      Specific PatientName search

  %(prog)s -u '12345.123456.123.1234567' myfolder
      Specific StudyInstanceUID

  %(prog)s -U ~/downloaded_uid_list.txt -n '*subj01*' myfolder
      Specify downloaded_uid_list file

  %(prog)s -M study_metadata.tsv -p 'Khan^NeuroAnalytics' -d '20170530'
      Query and write study metadata to TSV file (no download)

  %(prog)s --uid-from-file study_metadata.tsv myfolder
      Download studies using UIDs from metadata file

  %(prog)s -t /scratch/$USER/cfmm2tar_intermediate_dicoms -n '*subj01*' myfolder
      Specify intermediate dicoms dir
        """,
    )

    # Optional options
    parser.add_argument(
        "-U",
        "--downloaded-uid-list",
        dest="downloaded_uid_list",
        default="",
        help="Path to downloaded_uid_list file (default: no tracking)",
    )
    parser.add_argument(
        "-M",
        "--metadata-file",
        dest="metadata_file",
        default="",
        help="Path to metadata TSV file. If specified, only query and write metadata (no download). Can later use with --uid-from-file to download.",
    )
    parser.add_argument(
        "--save-metadata",
        dest="save_metadata",
        default="",
        help="Path to save metadata TSV during download (includes tar file paths)",
    )
    parser.add_argument(
        "--uid-from-file",
        dest="uid_from_file",
        default="",
        help="Path to file containing StudyInstanceUIDs to download (one per line or TSV with StudyInstanceUID column)",
    )
    parser.add_argument(
        "-c",
        "--credentials",
        dest="credentials_file",
        default=os.path.expanduser("~/.uwo_credentials"),
        help="Path to uwo_credentials file (default: ~/.uwo_credentials)",
    )
    parser.add_argument(
        "-t",
        "--intermediate-dir",
        dest="intermediate_dir",
        default="",
        help="Path to intermediate_dicoms_dir (default: <output folder>/cfmm2tar_intermediate_dicoms)",
    )
    parser.add_argument(
        "-s",
        "--server",
        dest="dicom_connection",
        default=os.environ.get("DICOM_CONNECTION", "CFMM@dicom.cfmm.uwo.ca:11112"),
        help="DICOM server connection string (default: from DICOM_CONNECTION env var or CFMM@dicom.cfmm.uwo.ca:11112)",
    )
    parser.add_argument(
        "-x",
        "--other-options",
        dest="other_options",
        default=os.environ.get("OTHER_OPTIONS", ""),
        help="Other options to pass to dcm4che tools (default: from OTHER_OPTIONS env var)",
    )
    parser.add_argument(
        "--refresh-trust-store",
        dest="refresh_trust_store",
        action="store_true",
        help="Force refresh the cached JKS trust store used for TLS connections",
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
        "--principal",
        dest="study_search",
        default="*",
        help='Principal^Project search string (default: "*" for all)',
    )
    parser.add_argument(
        "-u",
        "--uid",
        dest="study_instance_uid",
        default="*",
        help="StudyInstanceUID (Note: this will override other search options)",
    )

    # Positional argument
    parser.add_argument(
        "-o",
        "--output_dir",
        dest="output_dir",
        default="cfmm2tar",
        help="Output folder for retrieved DICOM data",
    )

    args = parser.parse_args()

    # Handle metadata-only mode (query and write to TSV, no download)
    if args.metadata_file:
        # We'll need credentials for query even in metadata mode
        username, password = read_credentials(args.credentials_file)

        if username is None or password is None:
            username = input("UWO Username: ")
            password = getpass.getpass("UWO Password: ")

        # Import here to access Dcm4cheUtils
        from cfmm2tar import Dcm4cheUtils

        # Create dcm4che utils instance
        cfmm_dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
            args.dicom_connection,
            username,
            password,
            args.other_options,
            force_refresh_trust_store=args.refresh_trust_store,
        )

        # Build matching key
        matching_key = f"-m StudyDescription='{args.study_search}' -m StudyDate='{args.date_search}' -m PatientName='{args.name_search}'"

        # Get study metadata
        print("Querying study metadata with search criteria:")
        print(f"  Principal^Project: {args.study_search}")
        print(f"  Date: {args.date_search}")
        print(f"  PatientName: {args.name_search}")

        studies = cfmm_dcm4che_utils.get_study_metadata_by_matching_key(matching_key)

        if not studies:
            print("No studies found matching the search criteria.")
            sys.exit(0)

        print(f"Found {len(studies)} studies")

        # Write to TSV file
        import csv

        with open(args.metadata_file, "w", newline="") as f:
            fieldnames = [
                "StudyInstanceUID",
                "PatientName",
                "PatientID",
                "StudyDate",
                "StudyDescription",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            for study in studies:
                writer.writerow(study)

        print(f"Study metadata written to: {args.metadata_file}")
        print("\nTo download these studies later, use:")
        print(f"  cfmm2tar --uid-from-file {args.metadata_file} <output_dir>")
        sys.exit(0)

    # Handle uid-from-file mode (download specific UIDs from file)
    study_instance_uid = args.study_instance_uid
    if args.uid_from_file:
        # Read UIDs from file
        uids = []
        with open(args.uid_from_file) as f:
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
            print(f"No StudyInstanceUIDs found in {args.uid_from_file}")
            sys.exit(1)

        print(f"Will download {len(uids)} studies from {args.uid_from_file}")

    # Read or prompt for credentials
    username, password = read_credentials(args.credentials_file)

    if username is None or password is None:
        username = input("UWO Username: ")
        password = getpass.getpass("UWO Password: ")

    # Setup directories
    output_dir = args.output_dir
    intermediate_dir = args.intermediate_dir

    if not intermediate_dir:
        intermediate_dir = os.path.join(output_dir, "cfmm2tar_intermediate_dicoms")

    # Create output directories
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(intermediate_dir, exist_ok=True)

    # Setup downloaded UID list file if specified
    downloaded_uid_list = args.downloaded_uid_list
    if downloaded_uid_list:
        downloaded_uid_dir = os.path.dirname(downloaded_uid_list)
        if downloaded_uid_dir and not os.path.exists(downloaded_uid_dir):
            os.makedirs(downloaded_uid_dir, exist_ok=True)
        if not os.path.exists(downloaded_uid_list):
            Path(downloaded_uid_list).touch()

    # Call the main retrieve function
    keep_sorted_dicom = False

    try:
        if args.uid_from_file:
            # Download each UID from the file
            for i, uid in enumerate(uids):
                print(f"\nDownloading study {i + 1}/{len(uids)}: {uid}")
                retrieve_cfmm_tar.main(
                    uwo_username=username,
                    uwo_password=password,
                    connect=args.dicom_connection,
                    PI_matching_key=args.study_search,
                    retrieve_dest_dir=intermediate_dir,
                    keep_sorted_dest_dir_flag=keep_sorted_dicom,
                    tar_dest_dir=output_dir,
                    study_date=args.date_search,
                    patient_name=args.name_search,
                    study_instance_uid=uid,
                    other_options=args.other_options,
                    downloaded_uids_filename=downloaded_uid_list,
                    metadata_tsv_filename=args.save_metadata,
                    force_refresh_trust_store=args.refresh_trust_store,
                )
        else:
            # Normal mode - use search criteria
            retrieve_cfmm_tar.main(
                uwo_username=username,
                uwo_password=password,
                connect=args.dicom_connection,
                PI_matching_key=args.study_search,
                retrieve_dest_dir=intermediate_dir,
                keep_sorted_dest_dir_flag=keep_sorted_dicom,
                tar_dest_dir=output_dir,
                study_date=args.date_search,
                patient_name=args.name_search,
                study_instance_uid=study_instance_uid,
                other_options=args.other_options,
                downloaded_uids_filename=downloaded_uid_list,
                metadata_tsv_filename=args.save_metadata,
                force_refresh_trust_store=args.refresh_trust_store,
            )

        # Clean up intermediate directory if empty
        try:
            os.rmdir(intermediate_dir)
        except OSError:
            # Directory not empty, that's fine
            pass

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
