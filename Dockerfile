FROM ubuntu:bionic
LABEL author=yinglilu@gmail.com
LABEL maintainer=isolove@uwo.ca
LABEL version=0.0.2

# Copy files from repo
COPY *.py /apps/cfmm2tar/
COPY cfmm2tar /apps/cfmm2tar/
COPY *.sh /src/

#needed for keytool
RUN if [ ! -e /dev/fd ]; then ln -s /proc/self/fd /dev/fd; fi


RUN apt-get update && apt-get install -y --no-install-recommends apt-utils \
    sudo \
    git \
    wget \
    curl \
    zip \
    unzip \
    python2.7 \
    python-pip \
    rsync \
    openssh-client
RUN pip install --upgrade pip && pip install --upgrade setuptools

#for some unknown reason, need change the mode:
RUN chmod a+x /apps/cfmm2tar/*.py


#dicomunwrap, will install pydicom
RUN cd /apps && git clone https://gitlab.com/cfmm/DicomRaw && cd DicomRaw && pip install -r requirements.txt


#needed when install dcm4che
RUN apt-get install -y default-jre

#install dcm4che
RUN cd /src && bash install_dcm4che_ubuntu.sh /opt


#For retrieving physio dicom files. without this line, all the physio series will not be retrieved with getscu
RUN echo '1.3.12.2.1107.5.9.1:ImplicitVRLittleEndian;ExplicitVRLittleEndian' >>/opt/dcm4che-3.3.8/etc/getscu/store-tcs.properties

#allow the getscu client to download CFMM's 9.4T data.
RUN echo 'EnhancedMRImageStorage:ImplicitVRLittleEndian;ExplicitVRLittleEndian'>>/opt/dcm4che-3.3.8/etc/getscu/store-tcs.properties

# env vars:
ENV PATH=/apps/DicomRaw/bin:/opt/dcm4che-3.3.8/bin:/apps/cfmm2tar:$PATH
ENV _JAVA_OPTIONS="-Xmx2048m"


ENTRYPOINT ["/apps/cfmm2tar/cfmm2tar"]
