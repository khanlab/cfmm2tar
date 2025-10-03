#!/bin/bash

#query,retrieve,and tgz CFMM's dicom data from sharcnet.

# In order to run this script as a cron task:
#   1.save your uwo username and password to ~/.uwo_credentials:
#     <username>
#     <password>
#     chmod 600 ~/.uwo_credentials 
#   2.setup passwordless ssh login to graham.sharnet.ca 

#Author: Ali Khan, YingLi Lu
#e-mail: 
#date: 2017-11-21

#for test:
#  StudyDate='20171108' #This study date has three patients, each has one study
#  StudyDate='20170529' #smaller data


function usage { 

  echo "Retrieves studies from dicom server based on Principal^Project, Date and/or PatientName.  If no search strings provided, all studies are downloaded"
  echo "Uses credentials in ~/.uwo_credentials (line1: username, line2: password)  or prompts for username/password" 
  echo ""
  echo "Usage: `basename $0` [optional options] <search options>  <output folder> "
  echo "                       "
  echo "    Optional options:  "
  echo "        -U 'path/to/downloaded_uid_list[default:no]'"
  echo "        -c 'path/to/uwo_credentials[default:~/.uwo_credentials]'"
  echo "        -t 'path/to/intermediate_dicoms_dir[default:<output folder>/cfmm2tar_intermediate_dicoms'"
  echo "        -s 'AETITLE@hostname:11112'"
  echo "                       "
  echo "    Search Options:  "
  echo "        -d 'Date'"
  echo "        -n 'PatientName'"
  echo "        -p 'Principal^Project'"
  echo "        -u 'StudyInstanceUID' (Note: this is _not_ a search string, it will override any other search options and download the single specified StudyInstanceUID.)"
  echo ""
  echo "	Example (all scans on specific date): `basename $0` -d '20170530' myfolder"
  echo "	Example (all scans since date): `basename $0` -d '20170530-' myfolder"
  echo "	Example (all scans in date range): `basename $0` -d '20170530-20170827' myfolder"
  echo "	Example (specific Principal^Project on all dates): `basename $0` -p 'Khan^NeuroAnalytics'  myfolder"
  echo "	Example (specific PatientName searc): `basename $0` -n '*subj01*'  myfolder"
  echo "        Example (specific StudyInstanceUID): `basename $0` -u '12345.123456.123.1234567' myfolder"
  echo "	Example (specify downloaded_uid_list file): `basename $0` -U ~/downloaded_uid_list.txt -n '*subj01*'  myfolder"
  echo "	Example (specify intermediate dicoms dir): `basename $0` -t /scratch/\$USER/cfmm2tar_intermediate_dicoms -n '*subj01*'  myfolder"
}

execpath=`dirname $0`
execpath=`realpath $execpath`


# new usage to be:
# -d (YYYYMMDD - default '-')
# -n (PatientName - default '*')
# -p (Principal^Project - default '*')
DATE_SEARCH=\'-\'
STUDY_SEARCH=\'*\'
NAME_SEARCH=\'*\'
STUDYINSTANCEUID=\'*\'

DOWNLOADED_UID_LIST=
UWO_CREDNTIALS=~/.uwo_credentials
DICOMS_DIR=

while getopts "d:n:p:u:U:c:t:s:x:" options; do
 case $options in
    d ) DATE_SEARCH=\'$OPTARG\';;
    n ) NAME_SEARCH=\'$OPTARG\';;
    p ) STUDY_SEARCH=\'$OPTARG\';;
    u ) STUDYINSTANCEUID=\'$OPTARG\';;
    U ) DOWNLOADED_UID_LIST=$OPTARG;;
    c ) UWO_CREDNTIALS=$OPTARG;;
    s ) DICOM_CONNECTION=$OPTARG;;
    t ) DICOMS_DIR=$OPTARG;;
    x ) OTHER_OPTIONS="${OPTARG}";;
    * ) usage
	exit 1;;
 esac
done

shift $((OPTIND-1))

if [ "$#" -lt 1 ]
then
	usage
	exit 1
fi

if [ ! -e $UWO_CREDNTIALS ]
then
read -p "UWO Username: " UWO_USERNAME
read -srp "UWO Password: " UWO_PASSWORD
else
UWO_USERNAME=$(sed -n '1 p' ${UWO_CREDNTIALS})
UWO_PASSWORD=$(sed -n '2 p' ${UWO_CREDNTIALS})
fi

# check if DOWNLOADED_UID_LIST file exit or not
if [ ! -f $DOWNLOADED_UID_LIST ]; then
    dirname_temp=`dirname $DOWNLOADED_UID_LIST`
    if [ ! -d $dirname_temp ]; then
      echo $dirname_temp
      mkdir -p $dirname_temp
    fi
    touch $DOWNLOADED_UID_LIST
fi

KEEP_SORTED_DICOM='False'

OUTPUT_DIR=$1
#retrieve dicoms to this folder
if [ -z "$DICOMS_DIR" ] #empty: not specify '-t /path/to/dir' in command line
then
    DICOMS_DIR=$OUTPUT_DIR/cfmm2tar_intermediate_dicoms
fi

mkdir -p $OUTPUT_DIR $DICOMS_DIR

#singularity image defined in CONFIG_DCM_RETRIEVE file
python $execpath/retrieve_cfmm_tar.py \
${UWO_USERNAME} \
${UWO_PASSWORD} \
${DICOM_CONNECTION} \
${STUDY_SEARCH} \
${DICOMS_DIR} \
${KEEP_SORTED_DICOM} \
${OUTPUT_DIR} \
${DATE_SEARCH} \
${NAME_SEARCH} \
${STUDYINSTANCEUID} \
"${OTHER_OPTIONS}" \
${DOWNLOADED_UID_LIST}

#clean-up after ourselves
rmdir $DICOMS_DIR
