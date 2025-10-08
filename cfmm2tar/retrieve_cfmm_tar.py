#!/usr/bin/env python3
"""
query,retrieve sort,and tar

Author: YingLi Lu
Email:  yinglilu@gmail.com
Date:   2018-05-22

note:
    Works on Linux/Mac only.
    Tested on Ubuntu 16.04, python 2.7.13
    findscu, and getscu are from dcm4che, not dcmtk!
"""

import logging
import os
import shutil
import sys

import pydicom

from . import Dcm4cheUtils, DicomSorter, sort_rules

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s-%(levelname)s-%(message)s", datefmt="%Y/%m/%d %I:%M:%S"
)


def insert_tag(dicom_dir):
    """
    walk dicom files in dicom_dir, and insert tags if missing
    """

    logger = logging.getLogger(__name__)

    for root, _dirs, filenames in os.walk(dicom_dir):
        for filename in filenames:
            full_filename = os.path.join(root, filename)
            try:
                ds = pydicom.dcmread(full_filename, stop_before_pixels=True)

                if "ProtocolName" not in ds:
                    ds.add_new((0x0018, 0x1030), "LO", "unnamed")
                    ds.save_as(full_filename)
                    # logger.info("Inserted ProtocolName 'unnamed' to {}".format(full_filename))

                if "SeriesDescription" not in ds:
                    ds.add_new((0x0008, 0x103E), "LO", "unnamed")
                    ds.save_as(full_filename)
                    # logger.info(inserted SeriesDescription 'unnamed' to {}".format(full_filename))

                if "ContentDate" not in ds:
                    if "StudyDate" in ds:
                        date = ds.StudyDate
                    elif "SeriesDate" in ds:
                        date = ds.SeriesDate
                    elif "AcquisitionDate" in ds:
                        date = ds.AcquisitionDate
                    else:
                        date = "19700101"

                    ds.add_new((0x0008, 0x0023), "DA", date)
                    ds.save_as(full_filename)
                    # logger.info("inserted ContentDate {} to {}".format(date, full_filename))

            except Exception as e:
                logger.exception(e)


def extract_series_metadata(dicom_dir):
    """
    Extract series-level metadata from retrieved DICOM files.
    
    Returns a list of dicts, one per series found.
    Each dict contains heudiconv dicominfo.tsv-like fields.
    """
    logger = logging.getLogger(__name__)
    
    # Dictionary to collect series metadata: SeriesInstanceUID -> metadata dict
    series_dict = {}
    # Track number of instances per series for dim3
    series_instance_counts = {}
    
    try:
        for root, _dirs, filenames in os.walk(dicom_dir):
            for filename in filenames:
                full_filename = os.path.join(root, filename)
                try:
                    ds = pydicom.dcmread(full_filename, stop_before_pixels=True)
                    
                    series_uid = str(ds.get("SeriesInstanceUID", ""))
                    if not series_uid:
                        continue
                    
                    # Count instances per series
                    series_instance_counts[series_uid] = series_instance_counts.get(series_uid, 0) + 1
                    
                    # If we already have this series, just update the count and continue
                    if series_uid in series_dict:
                        continue
                    
                    # Extract series metadata (similar to heudiconv dicominfo.tsv)
                    image_type = ds.get("ImageType", [])
                    if hasattr(image_type, "__iter__") and not isinstance(image_type, str):
                        image_type_str = "\\".join(str(x) for x in image_type)
                    else:
                        image_type_str = str(image_type)
                    
                    # Check if derived or motion corrected
                    is_derived = "DERIVED" in image_type_str.upper()
                    is_motion_corrected = "MOCO" in image_type_str.upper() or "MOSAIC" in image_type_str.upper()
                    
                    series_metadata = {
                        "StudyInstanceUID": str(ds.get("StudyInstanceUID", "")),
                        "SeriesInstanceUID": series_uid,
                        "PatientName": str(ds.get("PatientName", "")),
                        "PatientID": str(ds.get("PatientID", "")),
                        "StudyDate": str(ds.get("StudyDate", "")),
                        "StudyDescription": str(ds.get("StudyDescription", "")),
                        "SeriesNumber": str(ds.get("SeriesNumber", "")),
                        "SeriesDescription": str(ds.get("SeriesDescription", "")),
                        "ProtocolName": str(ds.get("ProtocolName", "")),
                        "SequenceName": str(ds.get("SequenceName", "")),
                        "ImageType": image_type_str,
                        "is_derived": str(is_derived),
                        "is_motion_corrected": str(is_motion_corrected),
                        "dim1": str(ds.get("Rows", "")),
                        "dim2": str(ds.get("Columns", "")),
                        "dim3": "",  # Will be filled in after counting all instances
                        "tr": str(ds.get("RepetitionTime", "")),
                        "te": str(ds.get("EchoTime", "")),
                        "fa": str(ds.get("FlipAngle", "")),
                        "slice_thickness": str(ds.get("SliceThickness", "")),
                        "acquisition_time": str(ds.get("AcquisitionTime", "")),
                        "Modality": str(ds.get("Modality", "")),
                    }
                    
                    series_dict[series_uid] = series_metadata
                    
                except Exception as e:
                    # Not a DICOM file or error reading, skip
                    continue
        
        # Update dim3 with instance counts
        for series_uid, metadata in series_dict.items():
            metadata["dim3"] = str(series_instance_counts.get(series_uid, ""))
        
        return list(series_dict.values())
        
    except Exception as e:
        logger.warning(f"Could not extract series metadata from DICOM files: {e}")
        return []


def main(
    uwo_username,
    uwo_password,
    connect,
    PI_matching_key,
    retrieve_dest_dir,
    keep_sorted_dest_dir_flag,
    tar_dest_dir,
    study_date,
    patient_name,
    study_instance_uid,
    other_options,
    downloaded_uids_filename,
    metadata_tsv_filename="",
    force_refresh_trust_store=False,
    series_metadata_flag=False,
    series_filter=None,
):
    """
    main workflow: for each study: query,retrieve,tar
    
    Args:
        series_metadata_flag: If True, write series-level metadata to TSV
        series_filter: Optional dict of {StudyUID: [SeriesUID1, SeriesUID2, ...]} 
                      to filter specific series during retrieval
    """

    logger = logging.getLogger(__name__)

    # Dcm4cheUtils
    cfmm_dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
        connect,
        uwo_username,
        uwo_password,
        other_options,
        force_refresh_trust_store=force_refresh_trust_store,
    )

    if study_instance_uid == "*":
        #  matching key
        matching_key = f"-m StudyDescription='{PI_matching_key}' -m StudyDate='{study_date}' -m PatientName='{patient_name}'"

        # get all StudyInstanceUIDs (dropping duplicates)
        StudyInstanceUIDs = list(
            set(cfmm_dcm4che_utils.get_StudyInstanceUID_by_matching_key(matching_key))
        )
    else:
        StudyInstanceUIDs = [
            study_instance_uid.replace(
                '"',
                "",
            ).replace("'", "")
        ]

    # retrieve each study by StudyInstanceUID
    for index, StudyInstanceUID in enumerate(StudyInstanceUIDs):
        # load downloaded StudyInstanceUIDs file
        downloaded_uids = []
        if downloaded_uids_filename:
            with open(downloaded_uids_filename) as f:
                # downloaded_uids=f.read().replace('\n', ' ')
                downloaded_uids = f.read().splitlines()

        # check if StudyInstanceUID has been downloaded
        if StudyInstanceUID in downloaded_uids:
            logger.info(f"Skipping existing StudyInstanceUID-{StudyInstanceUID}\n")
            continue

        logger.info(
            f"Retrieving #{index + 1} of {len(StudyInstanceUIDs)}: StudyInstanceUID-{StudyInstanceUID}\n"
        )

        # retrieve
        # retrieved_dicom_dir: example '/retrieve_dest_dir/1.3.12.2.1107.xx'
        retrieved_dicom_dir = cfmm_dcm4che_utils.retrieve_by_StudyInstanceUID(
            StudyInstanceUID, retrieve_dest_dir, timeout_sec=1800
        )

        logger.info(f"retrieved dicoms to {retrieved_dicom_dir}")

        # Extract metadata from the first DICOM file for TSV export
        study_metadata = {}
        series_metadata_list = []
        
        if metadata_tsv_filename:
            if series_metadata_flag:
                # Extract series-level metadata
                series_metadata_list = extract_series_metadata(retrieved_dicom_dir)
                
                # Filter series if series_filter is provided
                if series_filter and StudyInstanceUID in series_filter:
                    allowed_series = set(series_filter[StudyInstanceUID])
                    series_metadata_list = [
                        s for s in series_metadata_list 
                        if s.get("SeriesInstanceUID") in allowed_series
                    ]
                    logger.info(f"Filtered to {len(series_metadata_list)} series based on filter")
            else:
                # Original study-level metadata extraction
                try:
                    # Walk through retrieved directory to find a DICOM file
                    for root, _dirs, filenames in os.walk(retrieved_dicom_dir):
                        for filename in filenames:
                            full_filename = os.path.join(root, filename)
                            try:
                                ds = pydicom.dcmread(full_filename, stop_before_pixels=True)
                                # Extract metadata
                                study_metadata = {
                                    "StudyInstanceUID": str(
                                        ds.get("StudyInstanceUID", StudyInstanceUID)
                                    ),
                                    "PatientName": str(ds.get("PatientName", "")),
                                    "PatientID": str(ds.get("PatientID", "")),
                                    "StudyDate": str(ds.get("StudyDate", "")),
                                    "StudyDescription": str(ds.get("StudyDescription", "")),
                                }
                                break  # Found metadata, exit inner loop
                            except Exception:
                                continue  # Not a DICOM file, try next
                        if study_metadata:
                            break  # Found metadata, exit outer loop
                except Exception as e:
                    logger.warning(f"Could not extract metadata from DICOM files: {e}")

        # insert ProtocolName and SeriesDescription tag
        # some cfmm 9.4T data missing these two tags, which cause error when run tar2bids(heudiconv)
        insert_tag(retrieved_dicom_dir)

        #######
        # tar
        #######
        if not os.path.exists(tar_dest_dir):
            os.makedirs(tar_dest_dir)

        with DicomSorter.DicomSorter(
            retrieved_dicom_dir, sort_rules.sort_rule_CFMM, tar_dest_dir
        ) as d:
            # according to CFMM's rule, folder depth is 5:
            # pi/project/study_date/patient/studyID_and_hash_studyInstanceUID
            # a list with one element, retrieved_dicom_dir contain's one study
            tar_full_filenames = d.tar(5)

            # if there is no dicom files in the retrieved folder, tar_full_filenames is None
            if not tar_full_filenames:
                continue

            # logging
            tar_full_filename = tar_full_filenames[0]
            logger.info(f"tar file created: {tar_full_filename}")

            # .uid file
            uid_full_filename = tar_full_filename[:-3] + "uid"
            with open(uid_full_filename, "w") as f:
                f.write(StudyInstanceUID + "\n")

            logger.info(f"uid file created: {uid_full_filename}")

        # Write metadata to TSV file if specified
        if metadata_tsv_filename:
            import csv

            if series_metadata_flag and series_metadata_list:
                # Write series-level metadata
                # Add tar file path to each series
                for series_meta in series_metadata_list:
                    series_meta["TarFilePath"] = tar_full_filename

                # Check if file exists to determine if we need to write header
                file_exists = os.path.exists(metadata_tsv_filename)

                with open(metadata_tsv_filename, "a", newline="") as f:
                    fieldnames = [
                        "StudyInstanceUID",
                        "SeriesInstanceUID",
                        "PatientName",
                        "PatientID",
                        "StudyDate",
                        "StudyDescription",
                        "SeriesNumber",
                        "SeriesDescription",
                        "ProtocolName",
                        "SequenceName",
                        "ImageType",
                        "is_derived",
                        "is_motion_corrected",
                        "dim1",
                        "dim2",
                        "dim3",
                        "tr",
                        "te",
                        "fa",
                        "slice_thickness",
                        "acquisition_time",
                        "Modality",
                        "TarFilePath",
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")

                    # Write header if file is new
                    if not file_exists:
                        writer.writeheader()

                    for series_meta in series_metadata_list:
                        writer.writerow(series_meta)

                logger.info(f"Series metadata ({len(series_metadata_list)} series) written to: {metadata_tsv_filename}")
            
            elif study_metadata:
                # Write study-level metadata (original behavior)
                # Add tar file path to metadata
                study_metadata["TarFilePath"] = tar_full_filename

                # Check if file exists to determine if we need to write header
                file_exists = os.path.exists(metadata_tsv_filename)

                with open(metadata_tsv_filename, "a", newline="") as f:
                    fieldnames = [
                        "StudyInstanceUID",
                        "PatientName",
                        "PatientID",
                        "StudyDate",
                        "StudyDescription",
                        "TarFilePath",
                    ]
                    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")

                    # Write header if file is new
                    if not file_exists:
                        writer.writeheader()

                    writer.writerow(study_metadata)

                logger.info(f"metadata written to: {metadata_tsv_filename}")

        # update downloaded_uids_filename
        if downloaded_uids_filename:
            with open(downloaded_uids_filename, "a") as f:
                f.write(StudyInstanceUID + "\n")

        #  remove retrieved dir
        if not keep_sorted_dest_dir_flag:
            shutil.rmtree(retrieved_dicom_dir)


if __name__ == "__main__":
    if len(sys.argv) < 11:
        print(sys.argv)
        print(
            "Usage: python "
            + os.path.basename(__file__)
            + " uwo_username \
                 uwo_password \
                 connect \
                 PI_matching_key \
                 retrieve_dest_dir \
                 keep_sorted_dicom_flag \
                 tgz_dest_dir \
                 scan_date \
                 patient_name \
                 study_instance_uid \
                 other_options \
                 [downloaded_uids_filename]"
        )
        sys.exit()

    else:
        uwo_username = sys.argv[1]
        uwo_password = sys.argv[2]
        connect = sys.argv[3]
        PI_matching_key = sys.argv[4]
        retrieve_dest_dir = sys.argv[5]
        keep_sorted_dicom_flag = sys.argv[6] == "True"
        tgz_dest_dir = sys.argv[7]
        study_date = sys.argv[8]
        patient_name = sys.argv[9]
        study_instance_uid = sys.argv[10]
        if len(sys.argv) > 11:
            other_options = sys.argv[11]
        else:
            other_options = ""
        if len(sys.argv) > 12:
            downloaded_uids_filename = sys.argv[12]
        else:
            downloaded_uids_filename = ""

        main(
            uwo_username,
            uwo_password,
            connect,
            PI_matching_key,
            retrieve_dest_dir,
            keep_sorted_dicom_flag,
            tgz_dest_dir,
            study_date,
            patient_name,
            study_instance_uid,
            other_options,
            downloaded_uids_filename,
        )
