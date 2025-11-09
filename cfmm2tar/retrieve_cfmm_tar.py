#!/usr/bin/env python3
"""
query,retrieve sort,and tar

Author: YingLi Lu
Email:  yinglilu@gmail.com
Date:   2018-05-22

"""

import logging
import os
import shutil
import sys

import pydicom

from . import dcm4che_utils, dicom_sorter, sort_rules

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
    skip_derived=False,
    additional_tags=None,
):
    """
    main workflow: for each study: query,retrieve,tar
    """

    logger = logging.getLogger(__name__)

    # Dcm4cheUtils
    cfmm_dcm4che_utils = dcm4che_utils.Dcm4cheUtils(
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
            StudyInstanceUID, retrieve_dest_dir
        )

        logger.info(f"retrieved dicoms to {retrieved_dicom_dir}")

        # Extract metadata from the first DICOM file for TSV export
        study_metadata = {}
        if metadata_tsv_filename:
            try:
                # Walk through retrieved directory to find a DICOM file
                for root, _dirs, filenames in os.walk(retrieved_dicom_dir):
                    for filename in filenames:
                        full_filename = os.path.join(root, filename)
                        try:
                            ds = pydicom.dcmread(full_filename, stop_before_pixels=True)
                            # Extract default metadata
                            study_metadata = {
                                "StudyInstanceUID": str(
                                    ds.get("StudyInstanceUID", StudyInstanceUID)
                                ),
                                "PatientName": str(ds.get("PatientName", "")),
                                "PatientID": str(ds.get("PatientID", "")),
                                "StudyDate": str(ds.get("StudyDate", "")),
                                "StudyDescription": str(ds.get("StudyDescription", "")),
                            }
                            # Extract additional tags if specified
                            if additional_tags:
                                for tag_hex, field_name in additional_tags.items():
                                    try:
                                        # Convert hex tag string to tuple (e.g., "00100030" -> (0x0010, 0x0030))
                                        tag_group = int(tag_hex[:4], 16)
                                        tag_element = int(tag_hex[4:], 16)
                                        tag_value = ds.get((tag_group, tag_element), "")
                                        study_metadata[field_name] = str(tag_value)
                                    except Exception as e:
                                        logger.warning(f"Could not extract tag {tag_hex} ({field_name}): {e}")
                                        study_metadata[field_name] = ""
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

        with dicom_sorter.DicomSorter(
            retrieved_dicom_dir, sort_rules.sort_rule_CFMM, tar_dest_dir, skip_derived=skip_derived
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
        if metadata_tsv_filename and study_metadata:
            import csv

            # Add tar file path to metadata
            study_metadata["TarFilePath"] = tar_full_filename

            # Check if file exists to determine if we need to write header
            file_exists = os.path.exists(metadata_tsv_filename)

            with open(metadata_tsv_filename, "a", newline="") as f:
                # Build fieldnames: default fields plus any additional tags plus TarFilePath
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
                fieldnames.append("TarFilePath")

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
