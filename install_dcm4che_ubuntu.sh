#!/bin/bash

if [ "$#" -lt 1 ];then
	echo "Usage: $0 <install folder (absolute path)>"
	echo "For sudoer recommend: $0 /opt"
	echo "For normal user recommend: $0 $HOME/app"
	exit 0
fi

echo -n "installing dcm4che..." #-n without newline

DEST=$1
mkdir -p $DEST

VERSION=dcm4che-3.3.8
D_DIR=$DEST/$VERSION
if [ -d $D_DIR ]; then
	rm -rf $D_DIR
fi

wget https://iweb.dl.sourceforge.net/project/dcm4che/dcm4che3/3.3.8/$VERSION-bin.zip
unzip $VERSION-bin.zip -d $DEST
rm $VERSION-bin.zip


if [ -e $HOME/.profile ]; then #ubuntu
	PROFILE=$HOME/.profile
elif [ -e $HOME/.bash_profile ]; then #centos
	PROFILE=$HOME/.bash_profile
else
	echo "Add PATH manualy: PATH=$D_DIR/bin"
	exit 0
fi

#check if PATH already exist in $PROFILE
if grep -xq "export PATH=$D_DIR/bin:\$PATH" $PROFILE #return 0 if exist
then 
	echo "PATH=$D_DIR/bin" in the PATH already.
else
	echo "" >>$PROFILE
    echo "#dcm4che" >>$PROFILE
	echo "export PATH=$D_DIR/bin:\$PATH" >> $PROFILE    
fi

#test installation
#source $PROFILE
#getscu -h >/dev/null
#if [ $? -eq 0 ]; then
#	echo "SUCCESS"
#	echo "To update PATH of current terminal: source $PFORFILE"
#	echo "To update PATH of all terminal: re-login"
#else
#    echo "FAIL."
#fi

# this is a bash script
ISSUER_CA_URL=https://pki.uwo.ca/sectigo/certificates/SectigoRSAOrganizationValidationSecureServerCA-int.pem
for f in $(find ${D_DIR}/etc -name cacerts.jks)
do
  keytool -noprompt -importcert -trustcacerts -alias issuer -file <(wget -O - -o /dev/null ${ISSUER_CA_URL}) -keystore $f -storepass secret
done

ln -s ${D_DIR} /opt/dcm4che

#use this command to test.
#by StudyInstanceUID
#getscu --bind DEFAULT --connect CFMM-Public@dicom.cfmm.robarts.ca:11112 --tls-aes --user YOUR_UWO_USERNAME --user-pass YOUR_PASSWORD, -m StudyInstanceUID=1.3.12.2.1107.5.2.34.18932.30000017052914152689000000013

#by PatientID
#getscu  -L PATIENT -M PatientRoot --bind DEFAULT --connect CFMM-Public@dicom.cfmm.robarts.ca:11112 --tls-aes --user YOUR_UWO_USERNAME --user-pass YOUR_PASSWORD, -m 00100020=17.05.29-15:47:03-DST-1.3.12.2.1107.5.2.34.18932

