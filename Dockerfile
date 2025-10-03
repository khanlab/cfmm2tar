FROM ubuntu:22.04
LABEL author=yinglilu@gmail.com
LABEL maintainer=isolove@uwo.ca
LABEL version=0.0.3

#needed for keytool
RUN if [ ! -e /dev/fd ]; then ln -s /proc/self/fd /dev/fd; fi


RUN apt-get update && apt-get install -y --no-install-recommends apt-utils \
    sudo \
    git \
    wget \
    curl \
    zip \
    unzip \
    python3 \
    python3-pip \
    rsync \
    openssh-client

# Install uv for dependency management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# dcm4che requires JRE
# enable TLSv1.1 for dcm4chee v2
RUN apt-get install -y default-jre && sed -i 's/TLSv1.1, //g' /etc/java-11-openjdk/security/java.security

# Copy files from repo
COPY *.py /apps/cfmm2tar/

#for some unknown reason, need change the mode:
RUN chmod a+x /apps/cfmm2tar/*.py

# Copy pyproject.toml for dependency installation
COPY pyproject.toml /apps/cfmm2tar/

# Install Python dependencies using uv
RUN cd /apps/cfmm2tar && uv pip install --system -e .

#dicomunwrap, will install pydicom
RUN cd /apps && git clone https://gitlab.com/cfmm/DicomRaw && cd DicomRaw && uv pip install --system -r requirements.txt

COPY *.sh /src/

#install dcm4che
ENV DCM4CHE_VERSION=5.24.1
RUN cd /src && bash install_dcm4che_ubuntu.sh /opt

#For retrieving physio dicom files. without this line, all the physio series will not be retrieved with getscu
RUN echo '1.3.12.2.1107.5.9.1:ImplicitVRLittleEndian;ExplicitVRLittleEndian' >>/opt/dcm4che/etc/getscu/store-tcs.properties

#allow the getscu client to download CFMM's 9.4T data.
RUN echo 'EnhancedMRImageStorage:ImplicitVRLittleEndian;ExplicitVRLittleEndian'>>/opt/dcm4che/etc/getscu/store-tcs.properties

COPY cfmm2tar /apps/cfmm2tar/

# env vars:
ENV PATH=/apps/DicomRaw/bin:/opt/dcm4che/bin:/apps/cfmm2tar:$PATH
ENV _JAVA_OPTIONS="-Xmx2048m"

# dcm4chee v2 server
#ENV DICOM_CONNECTION=CFMM-Public@dicom.cfmm.uwo.ca:11112
#ENV OTHER_OPTIONS='--tls11 --tls-cipher=TLS_RSA_WITH_AES_128_CBC_SHA'

# dcm4chee v5 server
ENV DICOM_CONNECTION=CFMM@dicom.cfmm.uwo.ca:11112
ENV OTHER_OPTIONS='--tls-aes'


ENTRYPOINT ["/apps/cfmm2tar/cfmm2tar"]
