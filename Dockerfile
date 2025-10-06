FROM ubuntu:bionic


COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


#needed for keytool
RUN if [ ! -e /dev/fd ]; then ln -s /proc/self/fd /dev/fd; fi


RUN apt-get update && apt-get install -y --no-install-recommends apt-utils \
    sudo \
    git \
    wget \
    curl \
    zip \
    unzip \
    rsync \
    openssh-client


# dcm4che requires JRE
# enable TLSv1.1 for dcm4chee v2
RUN apt-get install -y default-jre && \
    find /etc -name java.security -exec sed -i 's/TLSv1.1, //g' {} \; 2>/dev/null || true



#install dcm4che
COPY install_dcm4che_ubuntu.sh /src/
ENV DCM4CHE_VERSION=5.24.1
RUN cd /src && bash install_dcm4che_ubuntu.sh /opt

#For retrieving physio dicom files. without this line, all the physio series will not be retrieved with getscu
RUN echo '1.3.12.2.1107.5.9.1:ImplicitVRLittleEndian;ExplicitVRLittleEndian' >>/opt/dcm4che/etc/getscu/store-tcs.properties

#allow the getscu client to download CFMM's 9.4T data.
RUN echo 'EnhancedMRImageStorage:ImplicitVRLittleEndian;ExplicitVRLittleEndian'>>/opt/dcm4che/etc/getscu/store-tcs.properties

# env vars:
ENV PATH=/apps/DicomRaw/bin:/opt/dcm4che/bin:$PATH
ENV _JAVA_OPTIONS="-Xmx2048m"

# dcm4chee v2 server
#ENV DICOM_CONNECTION=CFMM-Public@dicom.cfmm.uwo.ca:11112
#ENV OTHER_OPTIONS='--tls1-tls-cipher=TLS_RSA_WITH_AES_128_CBC_SHA'

# dcm4chee v5 server
ENV DICOM_CONNECTION=CFMM@dicom.cfmm.uwo.ca:11112
ENV OTHER_OPTIONS='--tls-aes'

# Copy the project into the image
ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN cd /app && uv pip install --system --break-system-packages -e .


ENTRYPOINT ["cfmm2tar"]
