FROM ubuntu:24.04
ARG VERSION=unknown
LABEL author=yinglilu@gmail.com
LABEL maintainer=isolove@uwo.ca
LABEL version=${VERSION}

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
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# dcm4che requires JRE
# enable TLSv1.1 for dcm4chee v2
RUN apt-get install -y default-jre && \
    find /etc -name java.security -exec sed -i 's/TLSv1.1, //g' {} \; 2>/dev/null || true

# Copy Python package structure
COPY cfmm2tar /apps/cfmm2tar_src/cfmm2tar
COPY pyproject.toml /apps/cfmm2tar_src/
COPY README.md /apps/cfmm2tar_src/

# Install Python dependencies using uv
RUN cd /apps/cfmm2tar_src && uv pip install --system --break-system-packages -e .

#dicomunwrap, will install pydicom
RUN cd /apps && git clone https://gitlab.com/cfmm/DicomRaw && cd DicomRaw && uv pip install --system --break-system-packages -r requirements.txt

COPY *.sh /src/

#install dcm4che
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
#ENV OTHER_OPTIONS='--tls11 --tls-cipher=TLS_RSA_WITH_AES_128_CBC_SHA'

# dcm4chee v5 server
ENV DICOM_CONNECTION=CFMM@dicom.cfmm.uwo.ca:11112
ENV OTHER_OPTIONS='--tls-aes'


ENTRYPOINT ["cfmm2tar"]
