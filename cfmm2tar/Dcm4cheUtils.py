#!/usr/bin/env python3
"""
Define a Dcm4cheUtils class, which can get StudyInstanceUID by matching key, retrieve dicom files to a destination directory.

Author: YingLi Lu
Email:  yinglilu@gmail.com
Date:   2018-05-22

note:
    Cross-platform compatible (uses XML parsing instead of shell commands).
    Originally tested on Ubuntu 16.04, python 2.7.13
"""

import logging
import os
import shutil
import tempfile

# for quote python strings for safe use in posix shells
import shlex
import subprocess
import time
import xml.etree.ElementTree as ET


class Dcm4cheUtils:
    """
    dcm4che utils
    """

    def __init__(self, connect, username, password, dcm4che_path="", other_options=""):
        self.logger = logging.getLogger(__name__)
        self.connect = connect
        self.username = username
        self.password = password
        self.dcm4che_path = dcm4che_path

        self._findscu_str = (
            f"""{self.dcm4che_path} findscu"""
            + " --bind  DEFAULT --tls-aes "
            + f" --connect {self.connect}"
            + " --accept-timeout 10000 "
            + f" {other_options} "
            + f""" --user {shlex.quote(self.username)} """
            + f""" --user-pass {shlex.quote(self.password)} """
        )

        self._getscu_str = (
            f"""{self.dcm4che_path} getscu"""
            + " --bind  DEFAULT --tls-aes "
            + f" --connect {self.connect} "
            + " --accept-timeout 10000 "
            + f" {other_options} "
            + f""" --user {shlex.quote(self.username)} """
            + f""" --user-pass {shlex.quote(self.password)} """
        )

    def _get_stdout_stderr_returncode(self, cmd):
        """
        Execute the external command and get its stdout, stderr and return code
        """
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = proc.communicate()
        return_code = proc.returncode

        return out, err, return_code

    def _execute_findscu_with_xml_output(self, matching_key, return_tags):
        """
        Execute findscu command with XML output to a temporary directory and parse the result.
        
        Args:
            matching_key: The matching key for the query (e.g., "-m StudyDescription='Khan*'")
            return_tags: List of DICOM tags to return (e.g., ["StudyInstanceUID", "PatientName"])
        
        Returns:
            ET.Element: Root element of the parsed XML, or None if parsing fails
        """
        # Create a temporary directory for XML output
        temp_dir = tempfile.mkdtemp(prefix="cfmm2tar_xml_")
        
        try:
            # Build the findscu command with XML output to file
            cmd = self._findscu_str + f""" {matching_key}"""
            
            # Add return tags
            for tag in return_tags:
                cmd += f" -r {tag}"
            
            # Add XML output options
            cmd += f" --xml --out-cat --out-dir {temp_dir}"
            
            # Execute the command
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            out, err = proc.communicate()
            return_code = proc.returncode
            
            # Check for errors
            if err:
                # Ignore the annoying Java info message
                if err != b"Picked up _JAVA_OPTIONS: -Xmx2048m\n" and err != "Picked up _JAVA_OPTIONS: -Xmx2048m\n":
                    self.logger.error(err)
            
            # Read the XML file from the temporary directory
            xml_file_path = os.path.join(temp_dir, "001.dcm")
            
            if not os.path.exists(xml_file_path):
                self.logger.warning(f"XML output file not found: {xml_file_path}")
                return None
            
            # Parse the XML file
            try:
                tree = ET.parse(xml_file_path)
                root = tree.getroot()
                return root
            except ET.ParseError as e:
                self.logger.error(f"Error parsing XML file: {e}")
                return None
            except Exception as e:
                self.logger.error(f"Error reading XML file: {e}")
                return None
                
        finally:
            # Clean up the temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _get_NumberOfStudyRelatedInstances(self, matching_key):
        """
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
        """

        # Execute findscu with XML output to file
        root = self._execute_findscu_with_xml_output(matching_key, ["00201208"])
        
        # Parse XML output
        instances = []
        if root is not None:
            try:
                # Find all DicomAttribute elements with tag="00201208" (NumberOfStudyRelatedInstances)
                for attr in root.findall(".//DicomAttribute[@tag='00201208']"):
                    value_elem = attr.find("Value")
                    if value_elem is not None and value_elem.text:
                        instances.append(value_elem.text.strip())
            except Exception as e:
                self.logger.error(f"Error processing XML: {e}")

        instances_str = "\n".join(instances)
        return instances_str

    def _ready_for_retrieve(self, matching_key, sleep_sec=2):
        """
        pre=get mathing's key's NumberOfStudyRelatedInstances
        if pre not empty:
            wait 20-30 seconds
            current = get PI+Today's NumberOfStudyRelatedInstances
            if pre==current (means transfer from scanner to pacs finished!)
                return True
        """

        pre = self._get_NumberOfStudyRelatedInstances(matching_key)

        # if not empty, means found study on PACS
        if pre:
            time.sleep(sleep_sec)
            current = self._get_NumberOfStudyRelatedInstances(matching_key)

            # transfer from scanner to pacs finished, ready for retrieve
            if pre == current:
                return True
            else:
                self.logger.info("Wating: data still sending to PACS server.")
                return False
        else:
            self.logger.info("No new data to retrieve yet!\n")
            return False

    def get_StudyInstanceUID_by_matching_key(self, matching_key):
        """
        find StudyInstanceUID[s] by matching key

        input:
            matching_key:
              example: -m StudyDescription='Khan*' -m StudyDate='20171116'
        output:
            list,[StudyInstanceUID1,StudyInstanceUID2,...]
        """

        # Execute findscu with XML output to file
        root = self._execute_findscu_with_xml_output(matching_key, ["StudyInstanceUID"])
        
        # Parse XML output
        StudyInstanceUID_list = []
        if root is not None:
            try:
                # Find all DicomAttribute elements with tag="0020000D" (StudyInstanceUID)
                for attr in root.findall(".//DicomAttribute[@tag='0020000D']"):
                    value_elem = attr.find("Value")
                    if value_elem is not None and value_elem.text:
                        uid = value_elem.text.strip()
                        if uid:  # Only add non-empty UIDs
                            StudyInstanceUID_list.append(uid)
            except Exception as e:
                self.logger.error(f"Error processing XML: {e}")

        return StudyInstanceUID_list

    def get_study_metadata_by_matching_key(self, matching_key):
        """
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
        """
        # Execute findscu with XML output to file
        return_tags = ["StudyInstanceUID", "PatientName", "StudyDate", "StudyDescription", "PatientID"]
        root = self._execute_findscu_with_xml_output(matching_key, return_tags)

        # Parse the XML output
        studies = []
        if root is not None:
            try:
                # Each NativeDicomModel represents one study result
                # The structure groups multiple DicomAttribute elements per study
                # We need to group them properly

                # dcm4che XML output wraps each C-FIND response in a separate structure
                # For findscu, we look for groups of DicomAttribute elements
                # that together form a complete study

                current_study = {}

                # Iterate through all DicomAttribute elements
                for attr in root.findall(".//DicomAttribute"):
                    tag = attr.get("tag")
                    value_elem = attr.find("Value")

                    if value_elem is not None and value_elem.text:
                        value = value_elem.text.strip()

                        # Map DICOM tags to field names
                        if tag == "0020000D":  # StudyInstanceUID
                            # If we already have a study in progress, save it
                            if current_study.get("StudyInstanceUID"):
                                studies.append(current_study)
                                current_study = {}
                            current_study["StudyInstanceUID"] = value
                        elif tag == "00100010":  # PatientName
                            current_study["PatientName"] = value
                        elif tag == "00100020":  # PatientID
                            current_study["PatientID"] = value
                        elif tag == "00080020":  # StudyDate
                            current_study["StudyDate"] = value
                        elif tag == "00081030":  # StudyDescription
                            current_study["StudyDescription"] = value

                # Don't forget the last study
                if current_study.get("StudyInstanceUID"):
                    studies.append(current_study)

                # Fill in missing fields with empty strings
                for study in studies:
                    for field in ["PatientName", "PatientID", "StudyDate", "StudyDescription"]:
                        if field not in study:
                            study[field] = ""

            except Exception as e:
                self.logger.error(f"Error processing XML: {e}")

        return studies

    def get_all_pi_names(self):
        """Find all PIs the user has access to (by StudyDescription).

        Specifically, find all StudyDescriptions, take the portion before
        the caret, and return each unique value."""

        # Execute findscu with XML output to file
        root = self._execute_findscu_with_xml_output("", ["StudyDescription"])

        # Parse XML output
        pi_names_set = set()
        if root is not None:
            try:
                # Find all DicomAttribute elements with tag="00081030" (StudyDescription)
                for attr in root.findall(".//DicomAttribute[@tag='00081030']"):
                    value_elem = attr.find("Value")
                    if value_elem is not None and value_elem.text:
                        study_desc = value_elem.text.strip()
                        # Take the part before the caret (^)
                        if study_desc:
                            pi_name = study_desc.split("^")[0]
                            if pi_name:  # Only add non-empty PI names
                                pi_names_set.add(pi_name)
            except Exception as e:
                self.logger.error(f"Error processing XML: {e}")

        # Return sorted list as bytes (to match original behavior)
        pi_names = [name.encode("UTF-8") for name in sorted(pi_names_set)]
        return pi_names

    def retrieve_by_StudyInstanceUID(self, StudyInstanceUID, output_dir, timeout_sec=1800):
        """
        retrive dicom file by key StudyInstanceUID. If PACS not ready for retrieving(e.g. console still sending data to PACS), it will keep checking until time out (30 mins)

        input:
            StudyInstanceUID: StudyInstanceUID key value
            output_dir: save retrieved dicom files to
            timeout_sec: keep checking if ready_for_retrieve before timeout

        output: output_sub_dir
            output_sub_dir:os.path.join(output_dir,StudyInstanceUID)

        note:
            Dicom files retrieved to output_sub_dir
        """

        self.logger.info("checking if PACS ready for retrieving...")

        # check PACS server data completeness
        start_time = time.time()
        time_elapsed = 0
        while time_elapsed < timeout_sec:
            if self._ready_for_retrieve(f"-m StudyInstanceUID='{StudyInstanceUID}'"):
                break
            else:
                self.logger.info("Will try again automatically.")
                time_elapsed = time.time() - start_time

        else:  # time out
            self.logger.info("Auto try time out! try again later.")
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
        self.logger.info("retrieving...")
        # getscu --bind DEFAULT --connect CFMM-Public@dicom.cfmm.robarts.ca:11112 --tls-aes --user YOUR_UWO_USERNAME --user-pass YOUR_PASSWORD -m StudyInstanceUID=1.3.12.2.1107.5.2.34.18932.30000017052914152689000000013
        cmd = (
            self._getscu_str
            + f""" -m StudyInstanceUID={StudyInstanceUID} """
            + f" --directory {output_sub_dir}"
        )

        out, err, return_code = self._get_stdout_stderr_returncode(cmd)

        if err:
            if err != "Picked up _JAVA_OPTIONS: -Xmx2048m\n":
                self.logger.error(err)

        return output_sub_dir

    def _retrieve_by_key_useless(
        self, matching_key, output_dir, downloaded_uids_filename="", timeout_sec=1800
    ):
        """
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
        """

        self.logger.info("checking if PACS ready for retrieving...")

        # check PACS server data completeness
        start_time = time.time()
        time_elapsed = 0
        while time_elapsed < timeout_sec:
            if self._ready_for_retrieve(matching_key):
                break
            else:
                self.logger.info("Will try again automatically.")
                time_elapsed = time.time() - start_time

        else:  # time out
            self.logger.info("Auto try time out! try again later.")
            return None

        # output_dir=os.path.join(output_dir,clean_path(key_value))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # get StudyInstanceUID
        StudyInstanceUID_list = self.get_StudyInstanceUID_by_matching_key(matching_key)

        # load downloaded StudyInstanceUIDs
        downloaded_uids = []
        if downloaded_uids_filename:
            with open(downloaded_uids_filename) as f:
                # downloaded_uids=f.read().replace('\n', ' ')
                downloaded_uids = f.read().splitlines()

        # retrive
        output_sub_dirs = []
        for index, StudyInstanceUID in enumerate(StudyInstanceUID_list):
            # check if StudyInstanceUID has been downloaded
            if StudyInstanceUID in downloaded_uids:
                self.logger.info(
                    f"Skipping #{index + 1} of {len(StudyInstanceUID_list)}: existing StudyInstanceUID-{StudyInstanceUID}\n"
                )
                continue

            self.logger.info(
                f"Retrieving #{index + 1} of {len(StudyInstanceUID_list)}: StudyInstanceUID-{StudyInstanceUID}\n"
            )

            # record output sub dirs
            output_sub_dir = os.path.join(output_dir, StudyInstanceUID)
            output_sub_dirs.append(output_sub_dir)

            # create sub dirs(StudyInstanceUID)
            if not os.path.exists(output_sub_dir):
                os.makedirs(output_sub_dir)

            # retrieve
            # getscu --bind DEFAULT --connect CFMM-Public@dicom.cfmm.robarts.ca:11112 --tls-aes --user YOUR_UWO_USERNAME --user-pass YOUR_PASSWORD -m StudyInstanceUID=1.3.12.2.1107.5.2.34.18932.30000017052914152689000000013
            cmd = (
                self._getscu_str
                + f""" -m StudyInstanceUID={StudyInstanceUID} """
                + f" --directory {output_sub_dir}"
            )

            out, err, return_code = self._get_stdout_stderr_returncode(cmd)

            if err:
                if err != "Picked up _JAVA_OPTIONS: -Xmx2048m\n":
                    self.logger.error(err)

        return output_sub_dirs, StudyInstanceUID_list
