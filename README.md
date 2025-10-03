# cfmm2tar

Download a tarballed DICOM dataset from the CFMM DICOM server

## Features

- Query and download DICOM studies from CFMM DICOM server
- Create tarballed datasets organized by PI/Project
- Track downloaded studies to avoid re-downloading
- **List-only mode**: Query and save StudyInstanceUIDs without downloading (useful for planning large downloads)

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

### List-only mode

You can first query and save StudyInstanceUIDs to a file without downloading the data. The output is a TSV (tab-separated values) file with columns for StudyInstanceUID, PatientName, StudyDate, StudyDescription, PatientID, and StudyID. This is useful for:
- Planning large downloads
- Reviewing what studies are available before downloading
- Creating a download queue for later processing
- Filtering studies based on patient name, date, or other metadata

```bash
# Query and save study metadata to a TSV file
docker run -i -t --rm --volume ${OUTPUT_DIR}:/data cfmm2tar -l -U /data/uid_list.tsv -p 'Khan^Project' -d '20180803' /data
```

The output TSV file will look like:
```
StudyInstanceUID	PatientName	StudyDate	StudyDescription	PatientID	StudyID
1.2.3.4.5.6...	Patient^Name	20180803	Khan^Project	P001	S001
...
```

Later, use the UID file to download only the studies you need:

```bash
# Download studies from the UID list
docker run -i -t --rm --volume ${OUTPUT_DIR}:/data cfmm2tar -U /data/uid_list.tsv /data
```

The `-U` option tracks downloaded studies, so you can safely re-run the command and it will skip already downloaded studies.