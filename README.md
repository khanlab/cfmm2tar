# cfmm2tar

Download a tarballed DICOM dataset from the CFMM DICOM server

## Docker image

1. Install Docker

2. Clone this repo and build the image:

```bash
git clone https://github.com/khanlab/cfmm2tar
cd cfmm2tar
docker build -t cfmm2tar .
```

3. Run the containerized `cfmm2tar`:

```bash
OUTPUT_DIR=/path/to/dir
mkdir ${OUTPUT_DIR}
docker run -i -t --rm --volume ${OUTPUT_DIR}:/data cfmm2tar
```

This will display help on using `cfmm2tar`

Search and download a specific dataset, e.g.

```bash
docker run -i -t --rm --volume ${OUTPUT_DIR}:/data cfmm2tar -p 'Everling^Marmoset' -d '20180803' /data
```

(You will be asked for your UWO username and password, and will only be able to find and download datasets to which you have read permissions).