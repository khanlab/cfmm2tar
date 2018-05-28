SHELL := /bin/bash

CONNECT='CFMM-Public@dicom.cfmm.robarts.ca:11112'
CREDENTIALS_FILE = '/home/ylu/.uwo_credentials'
USERNAME=$(shell sed -n '1 p' ${CREDENTIALS_FILE})
PASSWORD=$(shell sed -n '2 p' ${CREDENTIALS_FILE})
	
PI='Khan*'
SORTED_DEST_DIR=/tmp
KEEP_SORTED_DICOM_FLAG=False
TGZ_DEST_DIR=/home/ylu/test/retrieve_cfmm_tgz
#  StudyDate='20171108' #This study date has three patients, each has one study
#  StudyDate='20170529' #smaller data
#  SCAN_DATE='20171116' # this study date, Khan's has 4 studies. The one StudyInstanceUID ends with 0010 has smaller data(3914 dicoms)
SCAN_DATE='20170529'
PATIENT_NAME='*'

LIST_DOWNLOADED_UIDS=/mnt/hgfs/projects/cfmm2tar/src/test/downloaded_uids.txt

# MATCHING_KEY="-m StudyDescription='Khan*' -m StudyDate='20171116'"
## DCM4CHE_PATH='docker run -v /home:/home --rm yinglilu/dcm4che:0.3'
DCM4CHE_PATH=''

SINGULARITY=~/apps/singularity/bin/singularity
SINGULARITY_IMAGE=~/singularities/cfmm2tar.simg
SINGULARITY_FILE=Singularity.v0.0.1c

######
# test retrieve_cfmm_tar.py   
######
test_small:
	python ../retrieve_cfmm_tar.py ${USERNAME} ${PASSWORD} ${CONNECT} ${PI} ${SORTED_DEST_DIR} ${KEEP_SORTED_DICOM_FLAG} ${TGZ_DEST_DIR}  ${SCAN_DATE} ${PATIENT_NAME} ${LIST_DOWNLOADED_UIDS} ${DCM4CHE_PATH}

test_uids:
	#test downloaded_uids_filename
	python ../retrieve_cfmm_tar.py ${USERNAME} ${PASSWORD} ${CONNECT} ${PI} ${SORTED_DEST_DIR} ${KEEP_SORTED_DICOM_FLAG} ${TGZ_DEST_DIR}  '20171116' ${PATIENT_NAME} ${LIST_DOWNLOADED_UIDS} ${DCM4CHE_PATH}

test_cmrr:
	#PI='*'
	#SCAN_DATE='*'
	#PATIENT_NAME=2017_11_30_MS12
	python ../retrieve_cfmm_tar.py ${USERNAME} ${PASSWORD} ${CONNECT} '*' ${SORTED_DEST_DIR} ${KEEP_SORTED_DICOM_FLAG} ${TGZ_DEST_DIR}  '*' '2017_11_30_MS12' ${LIST_DOWNLOADED_UIDS}

######
# test cfmm2tar
######
test_cfmm2tar_small:
	../cfmm2tar -d ${SCAN_DATE} ${TGZ_DEST_DIR}

test_cfmm2tar_big:
	../cfmm2tar -d '20171108' ${TGZ_DEST_DIR}

test_cfmm2tar_cmrr:
	../cfmm2tar -n '2017_11_30_MS12' ${TGZ_DEST_DIR}

######
# test singularity
######
build:
	cd ../; sudo ${SINGULARITY} build --force ${SINGULARITY_IMAGE} ${SINGULARITY_FILE}; cd -
 	#cd ../; sudo ${SINGULARITY} build --force ${SINGULARITY_IMAGE} ${SINGULARITY_FILE}; cd -

test_singularity_cfmm2tar_cmrr:
	sudo ${SINGULARITY} run -B /mnt:/mnt -B /home:/home -B /tmp:/tmp ${SINGULARITY_IMAGE} -n '2017_11_30_MS12' ${TGZ_DEST_DIR}

# #test
# python retrieve_cfmm_tgz.py 'ylu589' '801199Rs,' 'CFMM-Public@dicom.cfmm.robarts.ca:11112' 'Khan*' /home/ylu/test/retreve True /home/ylu/test/tgz  '20171116' '*' 