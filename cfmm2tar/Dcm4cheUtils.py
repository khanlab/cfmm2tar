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
        cmd = self._findscu_str +\
            ''' {} '''.format(matching_key) +\
            ' -r StudyInstanceUID' +\
            ' -r PatientName' +\
            ' -r StudyDate' +\
            ' -r StudyDescription' +\
            ' -r PatientID' +\
            ' -X'  # XML output for easier parsing
        
        out, err, return_code = self._get_stdout_stderr_returncode(cmd)
        
        if err and err != b'Picked up _JAVA_OPTIONS: -Xmx2048m\n' and err != 'Picked up _JAVA_OPTIONS: -Xmx2048m\n':
            self.logger.error(err)
        
        # Parse the XML output
        studies = []
        try:
            import xml.etree.ElementTree as ET
            import re
            
            # Find all complete XML documents in the output using regex
            # Look for <?xml...?> declarations followed by their content
            output_text = out.decode('UTF-8')
            
            # Match XML documents: <?xml...?> followed by content up to </NativeDicomModel>
            xml_pattern = r'(<\?xml[^?]*\?>\s*<NativeDicomModel[^>]*>.*?</NativeDicomModel>)'
            xml_matches = re.findall(xml_pattern, output_text, re.DOTALL)
            
            for xml_str in xml_matches:
                if not xml_str.strip():
                    continue
                
                try:
                    root = ET.fromstring(xml_str)
                    study = {}
                    
                    # Extract DICOM attributes
                    for attr in root.findall('.//DicomAttribute'):
                        tag = attr.get('tag')
                        keyword = attr.get('keyword')
                        value_elem = attr.find('Value')
                        
                        if value_elem is not None and value_elem.text:
                            if keyword == 'StudyInstanceUID':
                                study['StudyInstanceUID'] = value_elem.text.strip()
                            elif keyword == 'PatientName':
                                study['PatientName'] = value_elem.text.strip()
                            elif keyword == 'StudyDate':
                                study['StudyDate'] = value_elem.text.strip()
                            elif keyword == 'StudyDescription':
                                study['StudyDescription'] = value_elem.text.strip()
                            elif keyword == 'PatientID':
                                study['PatientID'] = value_elem.text.strip()
                    
                    # Only add if we have at least a StudyInstanceUID
                    if 'StudyInstanceUID' in study:
                        # Fill in missing fields with empty strings
                        for field in ['PatientName', 'StudyDate', 'StudyDescription', 'PatientID']:
                            if field not in study:
                                study[field] = ''
                        studies.append(study)
                        
                except ET.ParseError as e:
                    # Only log at debug level as this is expected for malformed chunks
                    self.logger.debug(f"Failed to parse XML chunk: {e}")
                    continue
                    
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
