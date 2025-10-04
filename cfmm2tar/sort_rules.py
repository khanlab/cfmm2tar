#!/usr/bin/env python3
"""
dicom sort rule functions:

    sort_rule_demo: a simple demo sort rule
    sort_rule_CFMM: CFMM's sort rule

Author: YingLi Lu
Email:  yinglilu@gmail.com
Date:   2018-05-22

note:
    Tested on windows 10/ubuntu 16.04, python 2.7.14
"""

import logging
import os
import re

import pydicom


def sort_rule_demo(filename):
    """
    A simple sort rule:

    patient_name
      |-study_date
        |-series_number
          |-{patient_name}.{study_data}.{series_number}.{image_instance_number:04d}.dcm
          ...
        |-series_number
        ...

    intput:
        filename: dicom filename
    output:
        a dictionary:
            key: filename
            value: patient_name/study_date/sereis_number/{patient_name}.{study_data}.{series_number}.{image:04d}.dcm

    """
    logger = logging.getLogger(__name__)

    def clean_path(path):
        return re.sub(r"[^a-zA-Z0-9.-]", "_", f"{path}")

    try:
        dataset = pydicom.dcmread(filename, stop_before_pixels=True)

        patient_name = clean_path(str(dataset.PatientName).replace("^", "_"))
        print("patient_name", patient_name)
        study_date = clean_path(dataset.StudyDate)
        series_number = clean_path(f"{dataset.SeriesNumber:04d}")

        path = os.path.join(patient_name, study_date, series_number)
        sorted_filename = (
            f"{patient_name}.{study_date}.{dataset.SeriesNumber}.{dataset.InstanceNumber:04d}.dcm"
        )
        sorted_filename = clean_path(sorted_filename)

    except Exception as e:
        logger.exception(f"something wrong with {filename}")
        logger.exception(e)
        return None

    sorted_full_filename = os.path.join(path, sorted_filename)
    return sorted_full_filename


def sort_rule_CFMM(filename):
    """
    CFMM's Dicom sort rule

    intput:
        filename: dicom filename
    output:
        a dictionary:
            key: filename
            value: pi/project/study_date/patient/studyID_and_hash_studyInstanceUID/series_number
                   /{patient}.{modality}.{study}.{series:04d}.{image:04d}.{date}.{unique}.dcm

    CFMM's DICOM data Hierarchical structure: (same with CFMM's dcmrcvr.https://gitlab.com/cfmm/dcmrcvr)
    root_dir/
        -PI->first part of StudyDescription: John^Project.
            -project ->second part of StudyDescription: John^3T_Project.
                -19700101 ->StudyDate
                    -1970_01_01_C001 ->patientName
                    -1.AC168B21 -> dataset.StudyID + '.' + hashcode(dataset.StudyInstanceUID)
                            -0001->series number
                            -0002
                            -0003
                            -0004
                            -0005
                            -0006
                            -0007
                            ...
                    -1970_01_01_C002
                        -1.AC168B24
                            ...
                    -1970_01_01_C003
                        -1.AC168B3C
    """

    logger = logging.getLogger(__name__)

    def clean_path(path):
        return re.sub(r"[^a-zA-Z0-9.-]", "_", f"{path}")

    def hashcode(value):
        code = 0
        for character in value:
            code = (code * 31 + ord(character)) & 0xFFFFFFFF
        return f"{code:08X}"

    try:
        dataset = pydicom.dcmread(filename, stop_before_pixels=True)

        # CFMM's newer data:'PI^project'->['PI','project']
        # CFMM's older GE data:'PI project'->['PI','project']
        pi_project = dataset.StudyDescription.replace("^", " ").split()
        pi = clean_path(pi_project[0])
        project = clean_path(pi_project[1])
        study_date = clean_path(dataset.StudyDate)
        patient = clean_path(str(dataset.PatientName).partition("^")[0])
        studyID_and_hash_studyInstanceUID = clean_path(
            ".".join([dataset.StudyID or "NA", hashcode(dataset.StudyInstanceUID)])
        )
        series_number = clean_path(f"{dataset.SeriesNumber:04d}")

        path = os.path.join(
            pi, project, study_date, patient, studyID_and_hash_studyInstanceUID, series_number
        )
        sorted_filename = f"{patient.upper()}.{dataset.Modality}.{dataset.StudyDescription.upper()}.{dataset.SeriesNumber:04d}.{dataset.InstanceNumber:04d}.{dataset.StudyDate}.{hashcode(dataset.SOPInstanceUID)}.dcm"
    except Exception as e:
        logger.exception(f"something wrong with {filename}")
        logger.exception(e)
        return None

    sorted_full_filename = os.path.join(path, sorted_filename)

    return sorted_full_filename
