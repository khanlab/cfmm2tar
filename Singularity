Bootstrap: docker
From: ubuntu:xenial
#########


%setup
#########
mkdir -p $SINGULARITY_ROOTFS/src
cp -Rv . $SINGULARITY_ROOTFS/src


#########
%post
#########

#needed for keytool
if [ ! -e /dev/fd ]
then
ln -s /proc/self/fd /dev/fd
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update && apt-get install -y --no-install-recommends apt-utils \
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

pip install -U pip setuptools

cd /src

#install pydicom
mkdir /opt/pydicom
cd /opt/pydicom
git clone https://www.github.com/pydicom/pydicom.git
cd pydicom
git checkout ebf6a79602348d003a1d1324c66626f9f2b05432
python setup.py install


#needed when install dcm4che
apt-get install -y default-jre


#install dcm4che
cd /src
bash install_dcm4che_ubuntu.sh /opt


#########
%environment

#export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

#anaconda2
export PATH=/opt/anaconda2/bin/:$PATH

#dcm4che
export PATH=/opt/dcm4che-3.3.8/bin:$PATH

#python scripts
export PATH=/src:$PATH
export _JAVA_OPTIONS="-Xmx4048m"

%runscript
exec cfmm2tar $@
