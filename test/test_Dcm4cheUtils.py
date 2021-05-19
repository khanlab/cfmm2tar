
import logging
import Dcm4cheUtils

logging.basicConfig(
    level=logging.DEBUG, format='%(lineno)d-%(asctime)s-%(levelname)s-%(message)s', datefmt='%Y/%m/%d %I:%M:%S')


CONNECT = 'CFMM-Public@dicom.cfmm.robarts.ca:11112'
#MATCHING_KEY = "-m StudyDescription='Khan*' -m StudyDate='20171116'"
MATCHING_KEY = "-m StudyDescription='*' -m StudyDate='20180518'"
# if dcm4che installed on local and in PATH
# DCM4CHE_PATH=''
DCM4CHE_PATH = 'docker run -v /home:/home --rm yinglilu/dcm4che:0.3'
OUTPUT_DIR = '/home/ylu/test/Dcm4cheUtils'
DOWNLOADED_UID_FILENAME = 'downloaded_uid.txt'
UWO_CREDENTIALS_FILES = '/home/ylu/.uwo_credentials'

# read username password from credential file
with open(UWO_CREDENTIALS_FILES) as f:
    contents = f.read().split('\n')

USERNAME = contents[0]
PASSWORD = contents[1]

cfmm_dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
    CONNECT, USERNAME, PASSWORD, DCM4CHE_PATH)

logging.info('------testing------ _get_NumberOfStudyRelatedInstances')
r = cfmm_dcm4che_utils._get_NumberOfStudyRelatedInstances(MATCHING_KEY)
logging.info(r)

logging.info('------testing------ get_StudyInstanceUID_by_matching_key')
r = cfmm_dcm4che_utils.get_StudyInstanceUID_by_matching_key(MATCHING_KEY)
logging.info(r)

logging.info('------testing------ get_all_pi_names')
r = cfmm_dcm4che_utils.get_all_pi_names()
logging.info(r)

logging.info('------testing------ ready_for_retrieve')
r = cfmm_dcm4che_utils._ready_for_retrieve(MATCHING_KEY)
logging.info(r)

logging.info('------testing------ retrieve_by_key')
dicom_dirs = cfmm_dcm4che_utils.retrieve_by_key(
    MATCHING_KEY, OUTPUT_DIR, DOWNLOADED_UID_FILENAME)
logging.info(dicom_dirs)
