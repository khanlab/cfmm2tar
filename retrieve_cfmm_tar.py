#!/usr/bin/env python
'''
query,retrieve sort,and tar

Author: YingLi Lu
Email:  yinglilu@gmail.com
Date:   2018-05-22

note:
    Works on Linux/Mac only.
    Tested on Ubuntu 16.04, python 2.7.13
    findscu, and getscu are from dcm4che, not dcmtk!
'''

import os
import sys
import logging
import shutil

import pydicom

import DicomSorter
import sort_rules
import Dcm4cheUtils

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s-%(levelname)s-%(message)s', datefmt='%Y/%m/%d %I:%M:%S')


def insert_tag(dicom_dir):
    '''
    walk dicom files in dicom_dir, and insert tags if missing
    '''

    logger = logging.getLogger(__name__)

    for root, dirs, filenames in os.walk(dicom_dir):
        for filename in filenames:
            full_filename = os.path.join(root, filename)
            try:
                ds = pydicom.read_file(full_filename, stop_before_pixels=True)

                if "ProtocolName" not in ds:

                    ds.add_new((0x0018, 0x1030), 'LO', 'unnamed')
                    ds.save_as(full_filename)
                    #logger.info("Inserted ProtocolName 'unnamed' to {}".format(full_filename))

                if "SeriesDescription" not in ds:
                    ds.add_new((0x0008, 0x103e), 'LO', 'unnamed')
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
                        date = '19700101'

                    ds.add_new((0x0008, 0x0023), 'DA', date)
                    ds.save_as(full_filename)
                    # logger.info("inserted ContentDate {} to {}".format(date, full_filename))

            except Exception as e:
                logger.exception(e)


def main(uwo_username,
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
         dcm4che_path,
         list_only_mode=False):
    '''
    main workflow: for each study: query,retrieve,tar
    '''

    logger = logging.getLogger(__name__)

    # Dcm4cheUtils
    cfmm_dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
        connect, uwo_username, uwo_password, dcm4che_path, other_options)

    if study_instance_uid == "'*'":
        #  matching key
        matching_key = "-m StudyDescription='{}' -m StudyDate='{}' -m PatientName='{}'".format(
            PI_matching_key, study_date, patient_name
        )

        # get all StudyInstanceUIDs (dropping duplicates)
        StudyInstanceUIDs = list(set(cfmm_dcm4che_utils.get_StudyInstanceUID_by_matching_key(matching_key)))
        
        # For list-only mode, also get full metadata
        if list_only_mode:
            study_metadata_list = cfmm_dcm4che_utils.get_study_metadata_by_matching_key(matching_key)
        else:
            study_metadata_list = None
    else:
        StudyInstanceUIDs = [study_instance_uid.replace('"', "",).replace("'", "")]
        study_metadata_list = None

    # If list-only mode, just write UIDs and metadata to TSV and exit
    if list_only_mode:
        logger.info('List-only mode: Writing {} studies to {}'.format(
            len(StudyInstanceUIDs) if not study_metadata_list else len(study_metadata_list), 
            downloaded_uids_filename))
        
        if downloaded_uids_filename:
            # Read existing file to avoid duplicates
            existing_uids = set()
            file_exists = os.path.exists(downloaded_uids_filename)
            
            if file_exists:
                with open(downloaded_uids_filename, 'r') as f:
                    # Skip header if it exists
                    lines = f.readlines()
                    if lines and lines[0].startswith('StudyInstanceUID'):
                        lines = lines[1:]
                    for line in lines:
                        parts = line.strip().split('\t')
                        if parts:
                            existing_uids.add(parts[0])
            
            # Write new studies in TSV format
            with open(downloaded_uids_filename, 'a') as f:
                # Write header if file is new or empty
                if not file_exists or os.path.getsize(downloaded_uids_filename) == 0:
                    f.write('StudyInstanceUID\tPatientName\tStudyDate\tStudyDescription\tPatientID\tStudyID\n')
                
                # If we have full metadata, use it
                if study_metadata_list:
                    for study in study_metadata_list:
                        uid = study.get('StudyInstanceUID', '')
                        if uid and uid not in existing_uids:
                            patient_name = study.get('PatientName', '')
                            study_date = study.get('StudyDate', '')
                            study_desc = study.get('StudyDescription', '')
                            patient_id = study.get('PatientID', '')
                            study_id = study.get('StudyID', '')
                            
                            f.write('{}\t{}\t{}\t{}\t{}\t{}\n'.format(
                                uid, patient_name, study_date, study_desc, patient_id, study_id))
                            logger.info('Added study: {} - {} - {}'.format(uid, patient_name, study_date))
                        elif uid:
                            logger.info('Study already in list: {}'.format(uid))
                else:
                    # Fallback: write only UIDs (when using -u option for specific UID)
                    for uid in StudyInstanceUIDs:
                        if uid not in existing_uids:
                            f.write('{}\t\t\t\t\t\n'.format(uid))
                            logger.info('Added UID: {}'.format(uid))
                        else:
                            logger.info('UID already in list: {}'.format(uid))
        
        logger.info('List-only mode complete. {} studies written.'.format(
            len(StudyInstanceUIDs) if not study_metadata_list else len(study_metadata_list)))
        return

    # retrieve each study by StudyInstanceUID
    for index, StudyInstanceUID in enumerate(StudyInstanceUIDs):
        # load downloaded StudyInstanceUIDs file
        downloaded_uids = []
        if downloaded_uids_filename:
            with open(downloaded_uids_filename, 'r') as f:
                lines = f.readlines()
                # Handle both TSV format (new) and plain text format (old)
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('StudyInstanceUID'):
                        # Skip empty lines and header
                        continue
                    # For TSV format, extract first column (UID)
                    if '\t' in line:
                        uid = line.split('\t')[0]
                        downloaded_uids.append(uid)
                    else:
                        # Plain text format (backward compatibility)
                        downloaded_uids.append(line)

        # check if StudyInstanceUID has been downloaded
        if StudyInstanceUID in downloaded_uids:
            logger.info(
                'Skipping existing StudyInstanceUID-{}\n'.format(StudyInstanceUID))
            continue

        logger.info('Retrieving #{} of {}: StudyInstanceUID-{}\n'.format(
            index+1, len(StudyInstanceUIDs), StudyInstanceUID))

        # retrieve
        # retrieved_dicom_dir: example '/retrieve_dest_dir/1.3.12.2.1107.xx'
        retrieved_dicom_dir = cfmm_dcm4che_utils.retrieve_by_StudyInstanceUID(
            StudyInstanceUID, retrieve_dest_dir, timeout_sec=1800)

        logger.info('retrieved dicoms to {}'.format(retrieved_dicom_dir))

        # insert ProtocolName and SeriesDescription tag
        # some cfmm 9.4T data missing these two tags, which cause error when run tar2bids(heudiconv)
        insert_tag(retrieved_dicom_dir)

        #######
        # tar
        #######
        if not os.path.exists(tar_dest_dir):
            os.makedirs(tar_dest_dir)

        with DicomSorter.DicomSorter(retrieved_dicom_dir, sort_rules.sort_rule_CFMM, tar_dest_dir) as d:
            # according to CFMM's rule, folder depth is 5:
            # pi/project/study_date/patient/studyID_and_hash_studyInstanceUID
            # a list with one element, retrieved_dicom_dir contain's one study
            tar_full_filenames = d.tar(5)

            # if there is no dicom files in the retrieved folder, tar_full_filenames is None
            if not tar_full_filenames:
                continue

            # logging
            tar_full_filename = tar_full_filenames[0]
            logger.info("tar file created: {}".format(tar_full_filename))

            # .uid file
            uid_full_filename = tar_full_filename[:-3]+"uid"
            with open(uid_full_filename, 'w') as f:
                f.write(StudyInstanceUID+'\n')

            logger.info("uid file created: {}".format(uid_full_filename))

        # update downloaded_uids_filename
        if downloaded_uids_filename:
            # Check if file exists and has header
            file_exists = os.path.exists(downloaded_uids_filename)
            has_header = False
            
            if file_exists:
                with open(downloaded_uids_filename, 'r') as f:
                    first_line = f.readline()
                    if first_line.startswith('StudyInstanceUID'):
                        has_header = True
            
            with open(downloaded_uids_filename, 'a') as f:
                # If file doesn't exist or is empty, write header
                if not file_exists or (file_exists and os.path.getsize(downloaded_uids_filename) == 0):
                    f.write('StudyInstanceUID\tPatientName\tStudyDate\tStudyDescription\tPatientID\tStudyID\n')
                
                # Write UID in TSV format (empty fields for metadata as we don't have it during download)
                if has_header or not file_exists:
                    f.write(StudyInstanceUID+'\t\t\t\t\t\n')
                else:
                    # Old format - just UID
                    f.write(StudyInstanceUID+'\n')

        #  remove retrieved dir
        if not keep_sorted_dest_dir_flag:
            shutil.rmtree(retrieved_dicom_dir)


if __name__ == "__main__":
    if len(sys.argv) < 11:
        print(sys.argv)
        print("Usage: python " + os.path.basename(__file__) +
              " uwo_username \
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
                 [downloaded_uids_filename] \
                 [dcm4che_path] \
                 [list_only_mode]")
        sys.exit()

    else:
        uwo_username = sys.argv[1]
        uwo_password = sys.argv[2]
        connect = sys.argv[3]
        PI_matching_key = sys.argv[4]
        retrieve_dest_dir = sys.argv[5]
        keep_sorted_dicom_flag = (sys.argv[6] == 'True')
        tgz_dest_dir = sys.argv[7]
        study_date = sys.argv[8]
        patient_name = sys.argv[9]
        study_instance_uid = sys.argv[10]
        if len(sys.argv) > 11:
            other_options = sys.argv[11]
        else:
            other_options = ''
        if len(sys.argv) > 12:
            downloaded_uids_filename = sys.argv[12]
        else:
            downloaded_uids_filename = ''

        if len(sys.argv) > 13:
            # use dcm4che singularity/docker container runs on host
            dcm4che_path = sys.argv[13]
        else:
            # dcm4che installed on host or singularity container's PATH
            dcm4che_path = ''

        if len(sys.argv) > 14:
            list_only_mode = (sys.argv[14] == 'True')
        else:
            list_only_mode = False

        main(uwo_username,
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
             dcm4che_path,
             list_only_mode)
