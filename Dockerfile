FROM ubuntu:bionic
LABEL author=yinglilu@gmail.com
LABEL maintainer=isolove@uwo.ca
LABEL version=0.0.1i


RUN apt-get update && apt-get install -y    git \
                                            curl \
                                            zip \
                                            wget \
                                            default-jre \
                                            python-pip \
                                            sudo

# Install the app
COPY . /opt/cfmm2tar

# Install dcm4che
RUN bash /opt/cfmm2tar/install_dcm4che_ubuntu.sh /opt



#For retrieving physio dicom files. without this line, all the physio series will not be retrieved with getscu
RUN echo '1.3.12.2.1107.5.9.1:ImplicitVRLittleEndian;ExplicitVRLittleEndian' >>/opt/dcm4che/etc/getscu/store-tcs.properties

#allow the getscu client to download CFMM's 9.4T data.
RUN echo 'EnhancedMRImageStorage:ImplicitVRLittleEndian;ExplicitVRLittleEndian'>>/opt/dcm4che/etc/getscu/store-tcs.properties

# Install DicomRaw
WORKDIR /opt
RUN git clone https://gitlab.com/cfmm/dicomraw
WORKDIR dicomraw
RUN sudo pip install -r requirements.txt

ENV PATH=/opt/dcm4che/bin:/opt/cfmm2tar:/opt/dicomraw/bin:${PATH}
ENV _JAVA_OPTIONS="-Xmx2048m"

ENTRYPOINT ["/opt/cfmm2tar/cfmm2tar"]
