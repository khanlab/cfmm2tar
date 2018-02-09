#!/usr/bin/env python
'''
query,retrieve sort,and tar

note: findscu getscu are dcm4che's! not dcmtk's
'''

import glob
import os
import sys
from datetime import datetime
import re
import pydicom
import subprocess
import shutil
import time

import pipes


FNULL = open(os.devnull, 'w')
   
#check PACS data completeness
SLEEP_SEC=20
TIMEOUT_SEC=4*60*60 #4 hours


def clean_path(path):
    return re.sub(r'[^a-zA-Z0-9.-]', '_', '{0}'.format(path))

def hashcode(value):
    code = 0
    for character in value:
        code = (code * 31 + ord(character)) & 0xffffffff
    return '{0:08X}'.format(code)

def list_files_in_path(path):
    for file in os.listdir(path):
        full_file=os.path.join(path, file)
        if os.path.isfile(full_file):
            yield full_file

def find_StudyInstanceUID_by_matching_key(connect,matching_key,username,password):
    '''
    find StudyInstanceUID[s] by matching key

    input:
        connnect: PACS server info, for instance, 'CFMM-Public@dicom.cfmm.robarts.ca:11112'
        matching_key: -m StudyDescription='Khan*' -m StudyDate='20171116'
        username: UWO's username to access CFMM's PACS
        password: UWO's password to access CFMM's PACS

    output:list,[StudyInstanceUID1,StudyInstanceUID2,...]
    '''

    #check PACS server data completeness 
    cmd_query_NumberOfStudyRelatedInstances = 'findscu'+\
          ' --bind  DEFAULT' +\
          ' --connect {}'.format(connect)+\
          ' --tls-aes --user {} --user-pass {} '.format(pipes.quote(username),pipes.quote(password))+\
          ' {}'.format(matching_key) +\
          ' -r 00201208'+\
          ' |grep -i NumberOfStudyRelatedInstances |cut -d[ -f 2|cut -d] -f 1'

    
    try:
        pre = subprocess.check_output(cmd_query_NumberOfStudyRelatedInstances, shell=True)
    except subprocess.CalledProcessError as e:
        print 'findscu returned non-zero exit status'
        
    
    time_elapsed=0
    
    while time_elapsed<TIMEOUT_SEC:
        #wait SLEEP_SEC
        time.sleep(SLEEP_SEC)
        time_elapsed=time_elapsed+SLEEP_SEC

        #query again
        try:
            current = subprocess.check_output(cmd_query_NumberOfStudyRelatedInstances, shell=True)
        except subprocess.CalledProcessError as e:
            print 'findscu returned non-zero exit status'
    
        if pre == current:
            break
        else:
            pre=current
            print 'Wating: data uploading to PACS server.'
    
    #debug
    #print pre
    #print current    
          
    
    #findscu --bind DEFAULT --connect CFMM-Public@dicom.cfmm.robarts.ca:11112 -m StudyDescription='Khan*' -m StudyDate='20171116' --tls-aes --user username --user-pass password -r StudyInstanceUID |grep -i 0020,000D |cut -d '[' -f 2 | cut -d ']' -f 1
    cmd = 'findscu'+\
          ' --bind  DEFAULT' +\
          ' --connect {}'.format(connect)+\
          ' --tls-aes --user {} --user-pass {} '.format(pipes.quote(username),pipes.quote(password))+\
          ' {}'.format(matching_key) +\
          ' -r StudyInstanceUID'+\
          ' |grep -i 0020,000D |cut -d[ -f 2 | cut -d] -f 1'  #grep StudyInstanceUID

    #debug
    #print matching_key
    
    try:	
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=sys.stderr,shell=True)
        StudyInstanceUID_list, error = p.communicate()
        p.wait()
    except subprocess.CalledProcessError as e:
        print 'findscu returned non-zero exit status'
        return []
    
    return [x for x in StudyInstanceUID_list.splitlines() if x] #remove empty lines

        
def retrieve_by_key(connect,key_name,key_value,username,password,output_root_dir):
    '''
    retrive dicom file by key

    input:
        connnect: PACS server info, for instance, 'CFMM-Public@dicom.cfmm.robarts.ca:11112'
        key_name: specify matching key, for instance StudyInstanceUID
        key_value: matching key's value, for instance, 1.2.3.4.5.6.....
        username: UWO's username to access CFMM's PACS
        password: UWO's password to access CFMM's PACS
        output_root_dir: save retrieved dicom files to
    output:
        output_dir:os.path.join(output_root_dir,key_value)
    '''   
    output_dir=os.path.join(output_root_dir,clean_path(key_value))
    
    #debug
    #print output_dir

    if not os.path.exists(output_dir):
        #print output_dir
        os.makedirs(output_dir)
        
    #getscu --bind DEFAULT --connect CFMM-Public@dicom.cfmm.robarts.ca:11112 --tls-aes --user YOUR_UWO_USERNAME --user-pass YOUR_PASSWORD -m StudyInstanceUID=1.3.12.2.1107.5.2.34.18932.30000017052914152689000000013
    cmd = 'getscu' +\
        ' --bind  DEFAULT ' +\
        ' --connect {} '.format(connect) +\
        ' --tls-aes --user {} --user-pass {} '.format(pipes.quote(username),pipes.quote(password))+\
        ' -m {}={}'.format(key_name,key_value) +\
        ' --directory {}'.format(output_dir) +\
        '>/dev/null'

    #debug    
    #print cmd
    try:
        p = subprocess.Popen(cmd, stdout=sys.stdout,stderr=sys.stderr,shell=True)
        p.wait()
    except subprocess.CalledProcessError as e:
        print 'get returned non-zero exit status'
    
    
    return output_dir
    
def sort(dicom_dir,outupt_dir):
    '''
    sort dicom files into hierarchical dirs

    intput:
        dicom_dir: dir contains dicom files
        output_dir:save sorted hierarchical dirs to 
    output:
        StudyID_hashed_StudyInstanceUID_dir:full path of StudyID + '.' + hashcode(dataset.StudyInstanceUID), for instance, 1.AC168B21

    Algorithm:
        for each dicom file:
            parse
            mv(new name)
    Structure: same with CFMM's dcmrcvr.https://gitlab.com/cfmm/dcmrcvr
      bidsdump-dicom/					
        -Khan/ ->first part of StudyDescription: Palaniyappan^TOPSY. this is principal!
            -NeuroAnalytics ->second part of StudyDescription: Palaniyappan^TOPSY. this is project 
                -20171108 ->StudyDate
                    -2017_11_08_SNSX_C023 ->patientName
                       -1.AC168B21 -> dataset.StudyID + '.' + hashcode(dataset.StudyInstanceUID)
                            -0001->series number
                            -0002
                            -0003
                            -0004
                            -0005
                            -0006
                            -0007
                            ...
                    -2017_11_08_snSx_C024
                        -1.AC168B24
                            ...
                    -2017_11_08_snSx_C025
                        -1.AC168B3C
    '''
    pp=None

    for file in list_files_in_path(dicom_dir):
        dataset = pydicom.read_file(file)
        pp = dataset.StudyDescription.partition('^')
        patient = dataset.PatientName.partition('^')[0]

        path = os.path.join(outupt_dir, clean_path(pp[0]))
        if not os.path.exists(path):
            # Everyone can read the principal directory
            # This is required so individuals with access to a project,
            # but not principal can get to their projects
            #self._mkdir(path, permissions=stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO, gid=self.principal_gid)

            #print path 
            os.makedirs(path)

        for nextpath in [pp[2],
                        dataset.StudyDate,
                        patient,
                        '.'.join([dataset.StudyID or 'NA', hashcode(dataset.StudyInstanceUID)]),
                        '{series:04d}'.format(series=dataset.SeriesNumber)]:
            #print nextpath
            path = os.path.join(path, clean_path(nextpath))
            if os.path.exists(path):
               continue
            else:
                #self._mkdir(path, permissions=stat.S_IRWXU | stat.S_IRWXG | stat.S_IWOTH | stat.S_IXOTH)
                #print path 
                os.makedirs(path)

        filename = '{patient}.{modality}.{study}.{series:04d}.{image:04d}.{date}.{unique}.dcm'.format(
            patient=patient.upper(),
            modality=dataset.Modality,
            study=dataset.StudyDescription.upper(),
            series=dataset.SeriesNumber,
            image=dataset.InstanceNumber,
            date=dataset.StudyDate,
            unique=hashcode(dataset.SOPInstanceUID),
            )

        full_filename = os.path.join(path, clean_path(filename))
        shutil.move(file,full_filename)
        
    os.rmdir(dicom_dir) #Only works when the directory is empty, otherwise, OSError is raised

    if pp is None:
        return None
    else:
        StudyID_hashed_StudyInstanceUID_dir = os.path.join(outupt_dir,pp[0],pp[2],dataset.StudyDate, clean_path(patient),'.'.join([dataset.StudyID or 'NA', hashcode(dataset.StudyInstanceUID)]))
        return StudyID_hashed_StudyInstanceUID_dir
        
def tgz_dicom_dir(dicom_dir,tgz_dest_dir,PI_start_index,uid_string):
    '''
    tgz dir

    input:
        dicom_dir: dicom dir to tgz
        tgz_dest_dir: save tgz file to
        PI_index:PI index in '/' splitted path, 
            for instance,['', 'bidsdump-dcom', 'Palaniyappan', 'TOPSY', '20170210', 'patientName','1.2E853E5E']
    output:
        tgz_full_filename:

    '''
    if dicom_dir is None:
        return None

    dir_split=dicom_dir.split('/') 
    tgz_filename=clean_path("_".join(dir_split[PI_start_index:])+".tar")
    uid_filename=clean_path("_".join(dir_split[PI_start_index:])+".uid")
    tgz_full_filename=os.path.join(tgz_dest_dir,tgz_filename)
    tgz_cmd = 'tar cf {} {}'.format(tgz_full_filename,dicom_dir)
  
    with open(os.path.join(tgz_dest_dir,uid_filename), 'w') as myfile:
        myfile.write(uid_string)

    #debug
    #print tgz_cmd
    #subprocess.check_output(tgz_cmd, stderr=subprocess.STDOUT, shell=True)
    p = subprocess.Popen(tgz_cmd, stdout=sys.stdout,stderr=sys.stderr,shell=True)
    p.wait()

    return  tgz_full_filename
    
def tgz_by_studydate(studydate,dicom_dir,tgz_dest_dir):
    '''
    unused!
    '''
    #search depth 6, /dicom_dir/Palaniyappan/TOPSY/20170210/patientName/"StudyID+hashcode(StudyInstanceUID)"
    files_depth = glob.glob(os.path.join(dicom_dir,'*/*/*/*/*'))
    dirs = filter(lambda f: os.path.isdir(f), files_depth) 

    tgz_full_filename_list=[]
    for dir in dirs:
        dir_split=dir.split('/') #example result:['', 'bidsdump-dcom', 'Palaniyappan', 'TOPSY', '20170210', 'patientName','1.2E853E5E']
        date_string=dir_split[4] #index 4 is scan date
        date = datetime.strptime(date_string, "%Y%m%d").date()
        
        if date==studydate:
            #tgz
            tgz_filename="_".join(dir_split[2:])+".tgz"
            tgz_full_filename=os.path.join(tgz_dir,tgz_filename)
            tgz_full_filename_list.append(tgz_full_filename)
            tgz_cmd = 'tar czf {} {}'.format(tgz_full_filename,dir)
            os.system(tgz_cmd)
    return  tgz_full_filename_list

def main(uwo_username, 
             uwo_password, 
             connect, 
             PI_matching_key, 
             sorted_dest_dir, 
             keep_sorted_dest_dir_flag,
             tgz_dest_dir, 
             study_date,
             patient_name,
             list_downloaded):


    '''
    main workflow: query,retrieve,tgz

    intput
        uwo_username, 
        uwo_password, 
        connect, 
        PI_matching_key, 
        sorted_dest_dir,
        keep_sorted_dest_dir_flag,
        tgz_dest_dir, 
        study_date_list
    
    '''

    #get list of already downloaded uids
    if (list_downloaded != 0):
        with open(list_downloaded, 'r') as myfile:
            downloaded_uids=myfile.read().replace('\n', ' ')

    #find StudyInstanceUID by matching key
    StudyInstanceUID_list=[]
    #matching_key= "-m StudyDescription='{}' -m StudyDate='{}'".format(PI_matching_key,study_date)
    matching_key= "-m StudyDescription='{}' -m StudyDate='{}' -m PatientName='{}'".format(PI_matching_key,study_date,patient_name)
    StudyInstanceUID_list_one_study_date=find_StudyInstanceUID_by_matching_key(connect,matching_key,uwo_username,uwo_password)
    StudyInstanceUID_list.extend(StudyInstanceUID_list_one_study_date)

    if not StudyInstanceUID_list:
        sys.stderr.write('No data to retrieve!\n')
        sys.exit()
  
    #debug
    #print StudyInstanceUID_list

    #retrieve by StudyInstanceUID
    key_name='StudyInstanceUID' #dcm4che's must have key if getscu study level
    for index,key_value in enumerate(StudyInstanceUID_list):
        if key_value: #no null

            #check if key-value exists in downloaded list
            if (list_downloaded != 0):
                if key_value in downloaded_uids:
                    sys.stdout.writelines('#{} of {}: Skipping, existing StudyInstanceUID-{}\n'.format(int(index)+1,len(StudyInstanceUID_list),key_value))
                    sys.stdout.flush()
                    continue

            sys.stdout.writelines('#{} of {}: StudyInstanceUID-{}\n'.format(int(index)+1,len(StudyInstanceUID_list),key_value))
            sys.stdout.flush()

            sys.stdout.writelines('  retrieving...\n')
            sys.stdout.flush()
            dicom_dir = retrieve_by_key(connect,key_name,key_value,uwo_username,uwo_password,sorted_dest_dir)
            
            sys.stdout.writelines('  sorting...\n')
            sys.stdout.flush()
            StudyID_hashed_StudyInstanceUID_dir = sort(dicom_dir,sorted_dest_dir)

            sys.stdout.writelines('  tar-ing...\n')
            sys.stdout.flush()
            #StudyID_hashed_StudyInstanceUID_dir=/path/to/sorted_dest_dir/PI/project/StudyDate/patientname/studyID.hashcode(studyinstanceuid)
            #tgz filename='PI_project_studydate_patient_name/studyID.hashcode(studyinstanceuid)
            PI_index=len(sorted_dest_dir.split('/')) #this index is where PI starts
            tgz_full_filename = tgz_dicom_dir(StudyID_hashed_StudyInstanceUID_dir,tgz_dest_dir,PI_index,key_value)


            if not keep_sorted_dest_dir_flag:
                shutil.rmtree(StudyID_hashed_StudyInstanceUID_dir)
                shutil.rmtree(sorted_dest_dir)

if __name__=="__main__":
    if len(sys.argv)-1 < 9:
        print ("Usage: python " + os.path.basename(__file__)+ 
        " uwo_username \
          uwo_password \
          connect \
          PI_matching_key \
          sorted_dest_dir \
          keep_sorted_dicom_flag \
          tgz_dest_dir \
          scan_date \
          list_downloaded_uids")
        sys.exit()
    else:
        
        uwo_username=sys.argv[1]
        uwo_password=sys.argv[2]
        connect = sys.argv[3]
        PI_matching_key=sys.argv[4]
        sorted_dest_dir=sys.argv[5]
        keep_sorted_dicom_flag= (sys.argv[6]=='True')
        tgz_dest_dir=sys.argv[7]
        study_date=sys.argv[8]
        patient_name=sys.argv[9]
        if len(sys.argv)-1>9:
            list_downloaded=sys.argv[10]
        else:
            list_downloaded=0;

        main(uwo_username, 
             uwo_password, 
             connect, 
             PI_matching_key, 
             sorted_dest_dir, 
             keep_sorted_dicom_flag,
             tgz_dest_dir, 
             study_date,
	        patient_name,
             list_downloaded)
