# cfmm2tar

Download a tarballed DICOM dataset from the CFMM DICOM server

## Requirements

- Python 3.11+
- uv (for dependency management)

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

## Local Installation

### Using uv (recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e .
```

### Using pip

```bash
pip install -r requirements.txt
```

## Usage

### Basic Search and Download

Search and download DICOM studies based on search criteria:

```bash
# Download all studies for a specific Principal^Project on a specific date
cfmm2tar -p 'Khan^NeuroAnalytics' -d '20240101' output_dir

# Download studies for a specific patient
cfmm2tar -n '*subj01*' output_dir

# Download a specific study by StudyInstanceUID
cfmm2tar -u '1.2.840.113619.2.55.3.1234567890.123' output_dir
```

### Query Metadata Without Downloading

You can query and export study metadata to a TSV file without downloading the actual DICOM files:

```bash
# Export metadata for all studies on a specific date
cfmm2tar -M study_metadata.tsv -d '20240101'

# Export metadata for a specific Principal^Project
cfmm2tar -M study_metadata.tsv -p 'Khan^NeuroAnalytics' -d '20240101-20240131'
```

This creates a TSV file with columns:
- `StudyInstanceUID`: Unique identifier for the study
- `PatientName`: Patient name
- `PatientID`: Patient ID
- `StudyDate`: Date of the study
- `StudyDescription`: Study description (typically Principal^Project)

### Download from UID List

After reviewing the metadata file, you can download specific studies:

```bash
# Download all studies from the metadata file
cfmm2tar --uid-from-file study_metadata.tsv output_dir

# Or create a filtered version of the metadata file and download only those
# (e.g., filter in Excel, grep, awk, or Python)
cfmm2tar --uid-from-file study_metadata_filtered.tsv output_dir

# You can also use a simple text file with one UID per line
cfmm2tar --uid-from-file uid_list.txt output_dir
```

### Track Downloaded Studies

Track which studies have already been downloaded:

```bash
# Use a tracking file to avoid re-downloading
cfmm2tar -U ~/downloaded_uid_list.txt -p 'Khan^NeuroAnalytics' output_dir
```

### Workflow Example

1. **Query and export metadata** for review:
   ```bash
   cfmm2tar -M all_studies.tsv -p 'Khan^NeuroAnalytics' -d '20240101-20240131'
   ```

2. **Review and filter** the `all_studies.tsv` file (e.g., in Excel or with command-line tools)

3. **Download filtered studies**:
   ```bash
   cfmm2tar --uid-from-file all_studies_filtered.tsv output_dir
   ```

This workflow is especially useful when:
- You want to review available studies before downloading
- Storage is limited and you need to select specific studies
- You're sharing the metadata with collaborators to decide what to download
- You need to filter studies based on multiple criteria

## Development and Testing

### Running Tests

This project includes a comprehensive testing framework using a containerized dcm4che PACS instance.

```bash
# Install development dependencies
pip install -e .
pip install pytest pydicom numpy

# Install dcm4che tools (required for integration tests)
export DCM4CHE_VERSION=5.24.1
sudo bash install_dcm4che_ubuntu.sh /opt

# Run unit tests (no PACS server required)
pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsUnit -v

# Run integration tests (requires Docker)
cd tests
docker compose up -d
sleep 60  # Wait for PACS to be ready
cd ..
pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsIntegration -v

# Clean up
cd tests
docker compose down -v
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

### Continuous Integration

The project uses GitHub Actions for automated testing. The workflow:
1. Runs unit tests on every push and pull request
2. Starts a containerized dcm4chee PACS server
3. Runs integration tests against the PACS server
4. Reports results

See [.github/workflows/test.yml](.github/workflows/test.yml) for the complete workflow.
