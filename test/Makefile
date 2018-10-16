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

MULTI_SCAN_DATE='20170529-'

LIST_DOWNLOADED_UIDS=./downloaded_uids.txt

# MATCHING_KEY="-m StudyDescription='Khan*' -m StudyDate='20171116'"
DCM4CHE_PATH='docker run -v /home:/home -v /tmp:/tmp --rm yinglilu/dcm4che:0.3'
#DCM4CHE_PATH=''

SINGULARITY=~/apps/singularity/bin/singularity
SINGULARITY_IMAGE=~/singularities/cfmm2tar.simg
SINGULARITY_FILE=Singularity.V0.0.1g

######
# test retrieve_cfmm_tar.py   
######
test_small:
	python ../retrieve_cfmm_tar.py ${USERNAME} ${PASSWORD} ${CONNECT} ${PI} ${SORTED_DEST_DIR} ${KEEP_SORTED_DICOM_FLAG} ${TGZ_DEST_DIR}  ${SCAN_DATE} ${PATIENT_NAME} ${LIST_DOWNLOADED_UIDS} ${DCM4CHE_PATH}

test_uids_file:
	#re-run test_small, should see 'Skipping...'
	python ../retrieve_cfmm_tar.py ${USERNAME} ${PASSWORD} ${CONNECT} ${PI} ${SORTED_DEST_DIR} ${KEEP_SORTED_DICOM_FLAG} ${TGZ_DEST_DIR}  ${SCAN_DATE} ${PATIENT_NAME} ${LIST_DOWNLOADED_UIDS} ${DCM4CHE_PATH}

test_multi_studies:
	python ../retrieve_cfmm_tar.py ${USERNAME} ${PASSWORD} ${CONNECT} ${PI} ${SORTED_DEST_DIR} ${KEEP_SORTED_DICOM_FLAG} ${TGZ_DEST_DIR}  ${MULTI_SCAN_DATE} ${PATIENT_NAME} ${LIST_DOWNLOADED_UIDS} ${DCM4CHE_PATH}

test_empty_dicom_folder:
	#retrieved folder is empty
	python ../retrieve_cfmm_tar.py ${USERNAME} ${PASSWORD} ${CONNECT} '*' ${SORTED_DEST_DIR} ${KEEP_SORTED_DICOM_FLAG} ${TGZ_DEST_DIR}  20181015 '*' ${LIST_DOWNLOADED_UIDS} ${DCM4CHE_PATH}

test_cmrr:
	#PI='*'
	#SCAN_DATE='*'
	#PATIENT_NAME=2017_11_30_MS12
	python ../retrieve_cfmm_tar.py ${USERNAME} ${PASSWORD} ${CONNECT} '*' ${SORTED_DEST_DIR} ${KEEP_SORTED_DICOM_FLAG} ${TGZ_DEST_DIR}  '*' '2017_11_30_MS12' ${LIST_DOWNLOADED_UIDS}


# test data: tissue 9.4T missing ProtocolName and SeriesDescption tag,wich causing error when run tar2bids(heudiconv)
# PI: Khan
# project: DiffModeling
# date: 20180626
# studyinstanceuid:2.16.756.5.5.100.8323328.90914.1530020752.11
test_cmrr2tar_insert_tag:
		python ../retrieve_cfmm_tar.py ${USERNAME} ${PASSWORD} ${CONNECT} '*' ${SORTED_DEST_DIR} ${KEEP_SORTED_DICOM_FLAG} ${TGZ_DEST_DIR}  '*' '20180626' ${LIST_DOWNLOADED_UIDS}

######
# test cfmm2tar
######
test_cfmm2tar_small:
	../cfmm2tar -d ${SCAN_DATE} ${TGZ_DEST_DIR}

test_cfmm2tar_t:
	#test -t
	../cfmm2tar -t ~/test/cfmm2tar_intermediate_dicoms -d ${SCAN_DATE} ${TGZ_DEST_DIR}

test_cfmm2tar_U:
	#test -t
	../cfmm2tar -U ~/test/uid/uid.txt -d ${SCAN_DATE} ${TGZ_DEST_DIR}

test_cfmm2tar_big:
	../cfmm2tar -d '20171108' ${TGZ_DEST_DIR}

test_cfmm2tar_multi_studies:
	../cfmm2tar -d '20171108-' ${TGZ_DEST_DIR}

test_cfmm2tar_cmrr:
	../cfmm2tar -n '2017_11_30_MS12' ${TGZ_DEST_DIR}


######
# test singularity
######
build:
	cd ../; sudo ${SINGULARITY} build --force ${SINGULARITY_IMAGE} ${SINGULARITY_FILE}; cd -
 	
test_singularity_cfmm2tar_cmrr:
	${SINGULARITY} run -B /mnt:/mnt -B /home:/home -B /scratch -B /tmp:/tmp ${SINGULARITY_IMAGE} -n '2017_11_30_MS12' ${TGZ_DEST_DIR}
