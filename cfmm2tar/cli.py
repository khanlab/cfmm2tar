#!/usr/bin/env python3
"""
CLI script for cfmm2tar - Download a tarballed DICOM dataset from the CFMM DICOM server

Author: Ali Khan, YingLi Lu
Date: 2017-11-21
Updated: 2024 (Python 3 conversion)
"""

import argparse
import os
import sys
import getpass
from pathlib import Path

# Import the main function from retrieve_cfmm_tar module
from cfmm2tar import retrieve_cfmm_tar


def read_credentials(credentials_file):
    """Read UWO credentials from file."""
    try:
        with open(credentials_file, 'r') as f:
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
  
  %(prog)s -t /scratch/$USER/cfmm2tar_intermediate_dicoms -n '*subj01*' myfolder
      Specify intermediate dicoms dir
        """
    )
    
    # Optional options
    parser.add_argument('-U', '--downloaded-uid-list', dest='downloaded_uid_list',
                        default='',
                        help='Path to downloaded_uid_list file (default: no tracking)')
    parser.add_argument('-c', '--credentials', dest='credentials_file',
                        default=os.path.expanduser('~/.uwo_credentials'),
                        help='Path to uwo_credentials file (default: ~/.uwo_credentials)')
    parser.add_argument('-t', '--intermediate-dir', dest='intermediate_dir',
                        default='',
                        help='Path to intermediate_dicoms_dir (default: <output folder>/cfmm2tar_intermediate_dicoms)')
    parser.add_argument('-s', '--server', dest='dicom_connection',
                        default=os.environ.get('DICOM_CONNECTION', 'CFMM@dicom.cfmm.uwo.ca:11112'),
                        help='DICOM server connection string (default: from DICOM_CONNECTION env var or CFMM@dicom.cfmm.uwo.ca:11112)')
    parser.add_argument('-x', '--other-options', dest='other_options',
                        default=os.environ.get('OTHER_OPTIONS', ''),
                        help='Other options to pass to dcm4che tools (default: from OTHER_OPTIONS env var)')
    
    # Search options
    parser.add_argument('-d', '--date', dest='date_search',
                        default='-',
                        help='Date search string (default: "-" for all dates)')
    parser.add_argument('-n', '--name', dest='name_search',
                        default='*',
                        help='PatientName search string (default: "*" for all names)')
    parser.add_argument('-p', '--principal', dest='study_search',
                        default='*',
                        help='Principal^Project search string (default: "*" for all)')
    parser.add_argument('-u', '--uid', dest='study_instance_uid',
                        default='*',
                        help='StudyInstanceUID (Note: this will override other search options)')
    
    # Positional argument
    parser.add_argument('output_dir',
                        help='Output folder for retrieved DICOM data')
    
    args = parser.parse_args()
    
    # Read or prompt for credentials
    username, password = read_credentials(args.credentials_file)
    
    if username is None or password is None:
        username = input("UWO Username: ")
        password = getpass.getpass("UWO Password: ")
    
    # Setup directories
    output_dir = args.output_dir
    intermediate_dir = args.intermediate_dir
    
    if not intermediate_dir:
        intermediate_dir = os.path.join(output_dir, 'cfmm2tar_intermediate_dicoms')
    
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
            study_instance_uid=args.study_instance_uid,
            other_options=args.other_options,
            downloaded_uids_filename=downloaded_uid_list,
            dcm4che_path=''
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


if __name__ == '__main__':
    main()
