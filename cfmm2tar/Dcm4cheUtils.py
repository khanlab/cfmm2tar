#!/usr/bin/env python3
'''
Define a Dcm4cheUtils class, which can get StudyInstanceUID by matching key, retrieve dicom files to a destination directory.

Author: YingLi Lu
Email:  yinglilu@gmail.com
Date:   2018-05-22

note:
    Works on Linux/Mac only.
    Tested on Ubuntu 16.04, python 2.7.13
'''

import os
import subprocess
import logging
import time

# for quote python strings for safe use in posix shells
import shlex


class Dcm4cheUtils():
    '''
    dcm4che utils
    '''

    def __init__(self, connect, username, password, dcm4che_path='', other_options=''):
        self.logger = logging.getLogger(__name__)
        self.connect = connect
        self.username = username
        self.password = password
        self.dcm4che_path = dcm4che_path

        self._findscu_str = \
            '''{} findscu'''.format(self.dcm4che_path) +\
            ' --bind  DEFAULT --tls-aes ' +\
            ' --connect {}'.format(self.connect) +\
            ' --accept-timeout 10000 ' +\
            ' {} '.format(other_options) +\
            ''' --user {} '''.format(shlex.quote(self.username)) +\
            ''' --user-pass {} '''.format(shlex.quote(self.password))

        self._getscu_str = \
            '''{} getscu'''.format(self.dcm4che_path) +\
            ' --bind  DEFAULT --tls-aes ' +\
            ' --connect {} '.format(self.connect) +\
            ' --accept-timeout 10000 ' + \
            ' {} '.format(other_options) + \
            ''' --user {} '''.format(shlex.quote(self.username)) +\
            ''' --user-pass {} '''.format(shlex.quote(self.password))
    def _get_stdout_stderr_returncode(self, cmd):
        """
        Execute the external command and get its stdout, stderr and return code
        """
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        return_code = proc.returncode

        return out, err, return_code

    def _get_NumberOfStudyRelatedInstances(self, matching_key):
        '''
        get StudyInstanceUID list by matching key

        input:
            matching_key:
                example: -m StudyDescription='Khan*' -m StudyDate='20171116'
            dcm4che_path:
                default is '', can be a docker/singularity container

        output:string
            StudyInstanceUID1\n
            StudyInstanceUID2\n
            ...
        '''

        # findscu

        cmd = self._findscu_str +\
            ''' {}'''.format(matching_key) +\
            ' -r 00201208' +\
            ' |grep -i NumberOfStudyRelatedInstances ' +\
            ' |cut -d[ -f 2|cut -d] -f 1 |sed "/^$/d"'

        out, err, return_code = self._get_stdout_stderr_returncode(cmd)

        # local dcm4che
        if err:
            # no output of the annonying docker's dcm4che's java info
            if err != 'Picked up _JAVA_OPTIONS: -Xmx2048m\n':
                self.logger.error(err)

        instances_str = out.decode('UTF-8')
        return instances_str

    def _ready_for_retrieve(self, matching_key, sleep_sec=2):
        '''
        pre=get mathing's key's NumberOfStudyRelatedInstances
        if pre not empty:
            wait 20-30 seconds
            current = get PI+Today's NumberOfStudyRelatedInstances
            if pre==current (means transfer from scanner to pacs finished!)
                return True
        '''

        pre = self._get_NumberOfStudyRelatedInstances(
            matching_key)

        # if not empty, means found study on PACS
        if pre:
            time.sleep(sleep_sec)
            current = self._get_NumberOfStudyRelatedInstances(
                matching_key)

            # transfer from scanner to pacs finished, ready for retrieve
            if pre == current:
                return True
            else:
                self.logger.info('Wating: data still sending to PACS server.')
                return False
        else:
            self.logger.info('No new data to retrieve yet!\n')
            return False

    def get_StudyInstanceUID_by_matching_key(self, matching_key):
        '''
        find StudyInstanceUID[s] by matching key

        input:
            matching_key:
              example: -m StudyDescription='Khan*' -m StudyDate='20171116'
        output:
            list,[StudyInstanceUID1,StudyInstanceUID2,...]
        '''

        # findscu --bind DEFAULT --connect CFMM-Public@dicom.cfmm.robarts.ca:11112 -m StudyDescription='Khan*' -m StudyDate='20171116' --tls-aes --user username --user-pass password -r StudyInstanceUID |grep -i 0020,000D |cut -d '[' -f 2 | cut -d ']' -f 1
        cmd = self._findscu_str +\
            ''' {} '''.format(matching_key) +\
            ' -r StudyInstanceUID' +\
            ' |grep -i 0020,000D |cut -d[ -f 2 | cut -d] -f 1'  # grep StudyInstanceUID
        out, err, return_code = self._get_stdout_stderr_returncode(cmd)

        # local dcm4che
        if err:
            # no output of the annonying docker dcm4che's java info
            if err != 'Picked up _JAVA_OPTIONS: -Xmx2048m\n':
                self.logger.error(err)

        StudyInstanceUID_list_temp = out

        # remove empty lines
        StudyInstanceUID_list = [
            x.decode('UTF-8') for x in StudyInstanceUID_list_temp.splitlines() if x]

        return StudyInstanceUID_list

    def get_study_metadata_by_matching_key(self, matching_key):
        '''
        Get study metadata (UIDs and other study info) by matching key

        input:
            matching_key:
              example: -m StudyDescription='Khan*' -m StudyDate='20171116'
        output:
            list of dicts, each containing:
                [{'StudyInstanceUID': '...', 
                  'PatientName': '...', 
                  'StudyDate': '...',
                  'StudyDescription': '...',
                  'PatientID': '...'},
                 ...]
        '''
        import re
        
        # Request multiple DICOM tags in the query
        # Note: Not using -X flag as it doesn't produce XML in all versions
        # Instead, parse the debug output which is more reliable
        cmd = self._findscu_str +\
            ''' {} '''.format(matching_key) +\
            ' -r StudyInstanceUID' +\
            ' -r PatientName' +\
            ' -r StudyDate' +\
            ' -r StudyDescription' +\
            ' -r PatientID'
        
        out, err, return_code = self._get_stdout_stderr_returncode(cmd)
        
        if err and err != b'Picked up _JAVA_OPTIONS: -Xmx2048m\n' and err != 'Picked up _JAVA_OPTIONS: -Xmx2048m\n':
            self.logger.error(err)
        
        # Parse the debug output (similar to grep/cut approach used elsewhere)
        studies = []
        try:
            current_study = {}
            in_response = False  # Track if we're in a C-FIND-RSP section
            
            lines = out.decode('UTF-8').split('\n')
            
            for line in lines:
                # Track when we enter/exit response sections
                # Only parse DICOM tags from C-FIND-RSP (responses), not C-FIND-RQ (requests)
                if 'C-FIND-RSP Dataset:' in line:
                    in_response = True
                    continue
                elif 'C-FIND-RQ' in line or 'C-FIND-RSP[' in line:
                    in_response = False
                    continue
                
                # Only process DICOM tags if we're in a response section
                if not in_response:
                    continue
                    
                # Look for lines with DICOM tags in format: (xxxx,xxxx) VR [value] Description
                # Example: (0020,000D) UI [1.3.12.2.1107...] StudyInstanceUID
                match = re.match(r'\(([0-9A-Fa-f]{4}),([0-9A-Fa-f]{4})\)\s+\w+\s+\[([^\]]*)\]\s+(.+)', line)
                if match:
                    tag = f"{match.group(1)},{match.group(2)}"
                    value = match.group(3).strip()
                    keyword = match.group(4).strip()
                    
                    # Map DICOM tags to our field names
                    # StudyInstanceUID comes last and marks the end of a study
                    if tag == '0020,000D':  # StudyInstanceUID
                        current_study['StudyInstanceUID'] = value
                        # Save this complete study only if it has a valid StudyInstanceUID
                        if 'StudyInstanceUID' in current_study and current_study['StudyInstanceUID']:
                            studies.append(current_study)
                        # Start fresh for next study
                        current_study = {}
                    elif tag == '0010,0010':  # PatientName
                        current_study['PatientName'] = value
                    elif tag == '0010,0020':  # PatientID
                        current_study['PatientID'] = value
                    elif tag == '0008,0020':  # StudyDate
                        current_study['StudyDate'] = value
                    elif tag == '0008,1030':  # StudyDescription
                        current_study['StudyDescription'] = value
            
            # Fill in missing fields with empty strings
            for study in studies:
                for field in ['PatientName', 'PatientID', 'StudyDate', 'StudyDescription']:
                    if field not in study:
                        study[field] = ''
                        
        except Exception as e:
            self.logger.error(f"Error parsing study metadata: {e}")
            
        return studies

    def get_all_pi_names(self):
        """Find all PIs the user has access to (by StudyDescription).

        Specifically, find all StudyDescriptions, take the portion before
        the caret, and return each unique value."""
        cmd = self._findscu_str +\
            " -r StudyDescription " +\
            "| grep StudyDescription " +\
            "| cut -d[ -f 2 | cut -d] -f 1 " +\
            "| grep . " +\
            "| cut -d^ -f 1 " +\
            "| sort -u"

        out, err, _ = self._get_stdout_stderr_returncode(cmd)

        if err and err != "Picked up _JAVA_OPTIONS: -Xmx2048m\n":
            self.logger.error(err)

        return out.splitlines()


    def retrieve_by_StudyInstanceUID(self, StudyInstanceUID, output_dir, timeout_sec=1800):
        '''
        retrive dicom file by key StudyInstanceUID. If PACS not ready for retrieving(e.g. console still sending data to PACS), it will keep checking until time out (30 mins)

        input:
            StudyInstanceUID: StudyInstanceUID key value
            output_dir: save retrieved dicom files to
            timeout_sec: keep checking if ready_for_retrieve before timeout

        output: output_sub_dir
            output_sub_dir:os.path.join(output_dir,StudyInstanceUID)

        note:
            Dicom files retrieved to output_sub_dir
        '''

        self.logger.info('checking if PACS ready for retrieving...')

        # check PACS server data completeness
        start_time = time.time()
        time_elapsed = 0
        while time_elapsed < timeout_sec:
            if self._ready_for_retrieve("-m StudyInstanceUID='{}'".format(StudyInstanceUID)):
                break
            else:
                self.logger.info('Will try again automatically.')
                time_elapsed = time.time() - start_time

        else:  # time out
            self.logger.info('Auto try time out! try again later.')
            return None

        # output_dir=os.path.join(output_dir,clean_path(key_value))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # record output sub dirs
        output_sub_dir = os.path.join(output_dir, StudyInstanceUID)

        # create sub dir(StudyInstanceUID)
        if not os.path.exists(output_sub_dir):
            os.makedirs(output_sub_dir)

        # retrieve
        self.logger.info('retrieving...')
        # getscu --bind DEFAULT --connect CFMM-Public@dicom.cfmm.robarts.ca:11112 --tls-aes --user YOUR_UWO_USERNAME --user-pass YOUR_PASSWORD -m StudyInstanceUID=1.3.12.2.1107.5.2.34.18932.30000017052914152689000000013
        cmd = self._getscu_str +\
            ''' -m StudyInstanceUID={} '''.format(StudyInstanceUID) +\
            ' --directory {}'.format(output_sub_dir)

        out, err, return_code = self._get_stdout_stderr_returncode(cmd)

        if err:
            if err != 'Picked up _JAVA_OPTIONS: -Xmx2048m\n':
                self.logger.error(err)

        return output_sub_dir

    def _retrieve_by_key_useless(self, matching_key, output_dir, downloaded_uids_filename='', timeout_sec=1800):
        '''
        retrive dicom file by key. If PACS not ready for retrieving(e.g. console still sending data to PACS), it will keep checking until time out (30 mins)

        input:
            key_name: specify matching key, for instance StudyInstanceUID
            key_value: matching key's value, for instance, 1.2.3.4.5.6.....
            output_dir: save retrieved dicom files to
            timeout_sec: keep checking if ready_for_retrieve before timeout
            downloaded_uids_filename: file record downloaded StudyInstanceUIDs

        output: (output_sub_dirs,StudyInstanceUID_list)
            output_sub_dirs:[os.path.join(output_dir,key_value1),os.path.join(output_dir,key_value2),...]
            StudyInstanceUID_list:[StudyInstanceUID1,StudyInstanceUID2,...]

        note:
            Dicom files retrieved to output_dir
        '''

        self.logger.info('checking if PACS ready for retrieving...')

        # check PACS server data completeness
        start_time = time.time()
        time_elapsed = 0
        while time_elapsed < timeout_sec:
            if self._ready_for_retrieve(matching_key):
                break
            else:
                self.logger.info('Will try again automatically.')
                time_elapsed = time.time() - start_time

        else:  # time out
            self.logger.info('Auto try time out! try again later.')
            return None

        # output_dir=os.path.join(output_dir,clean_path(key_value))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # get StudyInstanceUID
        StudyInstanceUID_list = self.get_StudyInstanceUID_by_matching_key(
            matching_key)

        # load downloaded StudyInstanceUIDs
        downloaded_uids = []
        if downloaded_uids_filename:
            with open(downloaded_uids_filename, 'r') as f:
                # downloaded_uids=f.read().replace('\n', ' ')
                downloaded_uids = f.read().splitlines()

        # retrive
        output_sub_dirs = []
        for index, StudyInstanceUID in enumerate(StudyInstanceUID_list):

            # check if StudyInstanceUID has been downloaded
            if StudyInstanceUID in downloaded_uids:
                self.logger.info('Skipping #{} of {}: existing StudyInstanceUID-{}\n'.format(
                    index+1, len(StudyInstanceUID_list), StudyInstanceUID))
                continue

            self.logger.info('Retrieving #{} of {}: StudyInstanceUID-{}\n'.format(
                index+1, len(StudyInstanceUID_list), StudyInstanceUID))

            # record output sub dirs
            output_sub_dir = os.path.join(output_dir, StudyInstanceUID)
            output_sub_dirs.append(output_sub_dir)

            # create sub dirs(StudyInstanceUID)
            if not os.path.exists(output_sub_dir):
                os.makedirs(output_sub_dir)

            # retrieve
            # getscu --bind DEFAULT --connect CFMM-Public@dicom.cfmm.robarts.ca:11112 --tls-aes --user YOUR_UWO_USERNAME --user-pass YOUR_PASSWORD -m StudyInstanceUID=1.3.12.2.1107.5.2.34.18932.30000017052914152689000000013
            cmd = self._getscu_str +\
                ''' -m StudyInstanceUID={} '''.format(StudyInstanceUID) +\
                ' --directory {}'.format(output_sub_dir)

            out, err, return_code = self._get_stdout_stderr_returncode(cmd)

            if err:
                if err != 'Picked up _JAVA_OPTIONS: -Xmx2048m\n':
                    self.logger.error(err)

        return output_sub_dirs, StudyInstanceUID_list
