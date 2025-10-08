# cfmm2tar

Download a tarballed DICOM dataset from the CFMM DICOM server

## Overview

`cfmm2tar` is a command-line tool for querying and downloading DICOM studies from the CFMM (Centre for Functional and Metabolic Mapping) DICOM server. It provides three flexible deployment options to suit different environments and use cases.

## Installation & Usage

There are **three ways** to run `cfmm2tar`, each with different requirements:

### Option 1: Docker Container (Recommended - All-in-One)

This is the easiest method as it includes **all dependencies** (Python, dcm4che tools, and DicomRaw utilities) in a single container.

**Requirements:** Docker or Podman

**Installation:**
```bash
# Pull from GitHub Container Registry
docker pull ghcr.io/khanlab/cfmm2tar:latest

# Or build locally
git clone https://github.com/khanlab/cfmm2tar
cd cfmm2tar
docker build -t cfmm2tar .
```

**Usage:**
```bash
OUTPUT_DIR=/path/to/dir
mkdir -p ${OUTPUT_DIR}

# Show help
docker run --rm cfmm2tar --help

# Download studies
docker run -i -t --rm --volume ${OUTPUT_DIR}:/data cfmm2tar -p 'Everling^Marmoset' -d '20180803' /data
```

You will be prompted for your UWO username and password. You can only download datasets to which you have read permissions.

### Option 2: Apptainer/Singularity Container (For HPC Environments)

Similar to Docker but designed for HPC clusters where Docker may not be available.

**Requirements:** Apptainer (formerly Singularity)

**Installation:**
```bash
# Build from Docker image
apptainer build cfmm2tar.sif docker://ghcr.io/khanlab/cfmm2tar:latest

# Or build from definition file
apptainer build cfmm2tar.sif Singularity
```

**Usage:**
```bash
OUTPUT_DIR=/path/to/dir
mkdir -p ${OUTPUT_DIR}

# Show help
apptainer run cfmm2tar.sif --help

# Download studies
apptainer run --bind ${OUTPUT_DIR}:/data cfmm2tar.sif -p 'Khan^Project' -d '20240101' /data
```

### Option 3: PyPI Installation (For Python Environments)

Install `cfmm2tar` as a Python package. **Note:** This method requires additional setup for dcm4che tools.

**Requirements:** 
- Python 3.11+
- **Either** dcm4che tools installed locally **OR** a container with dcm4che tools

**Installation:**
```bash
# From PyPI (when published)
pip install cfmm2tar

# Or install from source
git clone https://github.com/khanlab/cfmm2tar
cd cfmm2tar
pip install -e .
```

**Setup dcm4che tools:**

You have two options:

#### Option 3a: Install dcm4che locally
```bash
export DCM4CHE_VERSION=5.24.1
sudo bash install_dcm4che_ubuntu.sh /opt
export PATH=/opt/dcm4che-${DCM4CHE_VERSION}/bin:$PATH
```

#### Option 3b: Use a dcm4che container
```bash
# Pull a container with dcm4che tools
apptainer pull docker://ghcr.io/khanlab/cfmm2tar:latest

# Set environment variable
export DCM4CHE_CONTAINER=/path/to/cfmm2tar.sif
```

**Usage:**
```bash
OUTPUT_DIR=/path/to/dir
mkdir -p ${OUTPUT_DIR}

# If dcm4che tools are in PATH (Option 3a)
cfmm2tar -p 'Khan^Project' -d '20240101' ${OUTPUT_DIR}

# If using a dcm4che container (Option 3b)
cfmm2tar --dcm4che-container /path/to/cfmm2tar.sif -p 'Khan^Project' -d '20240101' ${OUTPUT_DIR}

# Or set environment variable
export DCM4CHE_CONTAINER=/path/to/cfmm2tar.sif
cfmm2tar -p 'Khan^Project' -d '20240101' ${OUTPUT_DIR}
```

## Comparison of Methods

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Docker Container** | ✅ All dependencies included<br>✅ Consistent environment<br>✅ Easy to use | ❌ Requires Docker | End users, workstations |
| **Apptainer Container** | ✅ All dependencies included<br>✅ Works on HPC clusters<br>✅ No root required | ❌ Need to build/pull container | HPC environments |
| **PyPI Install** | ✅ Integrates with Python environment<br>✅ Easy to script | ❌ Requires separate dcm4che setup<br>❌ More complex setup | Python developers, scripting |

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

## TLS Certificate Management

When connecting to the CFMM DICOM server, `cfmm2tar` requires a valid TLS certificate trust store for secure communication. The tool automatically handles certificate management for you.

### Automatic Trust Store Setup

`cfmm2tar` automatically:
1. Downloads the UWO Sectigo certificate from the institutional PKI server
2. Creates a JKS (Java KeyStore) trust store file using `keytool`
3. Caches the trust store in `~/.cfmm2tar/mytruststore.jks` for future use
4. Adds the `--trust-store` option to all dcm4che commands

This happens transparently on first use - no manual setup required!

### Refreshing the Trust Store

If the certificate expires or you need to refresh the cached trust store:

```bash
# Force refresh the trust store
cfmm2tar --refresh-trust-store -p 'Khan^NeuroAnalytics' output_dir

# The trust store will be automatically refreshed before downloading
```

### Manual Trust Store Management

For advanced users or troubleshooting:

```python
from cfmm2tar import truststore

# Get the default trust store path
path = truststore.get_truststore_path()
print(f"Trust store location: {path}")

# Force creation/refresh of trust store
truststore.ensure_truststore(force_refresh=True)
```

### Requirements

The automatic trust store setup requires:
- `wget` (for downloading the certificate)
- `keytool` (part of Java JRE/JDK)

These are included in the Docker and Apptainer containers. For PyPI installations, ensure these tools are available in your environment.

**Note:** If trust store setup fails (e.g., network issues, missing tools), `cfmm2tar` will log a warning but continue to operate. However, TLS connections may fail without a valid trust store.

## Development and Testing

### Development Setup

For contributors and developers:

```bash
# Clone the repository
git clone https://github.com/khanlab/cfmm2tar
cd cfmm2tar

# Install in development mode with dev dependencies
pip install -e .
pip install ruff pre-commit pytest pydicom numpy

# Set up pre-commit hooks (runs quality checks before each commit)
pre-commit install

# Install dcm4che tools (required for integration tests)
export DCM4CHE_VERSION=5.24.1
sudo bash install_dcm4che_ubuntu.sh /opt
```

### Code Quality and Formatting

This project uses `ruff` for linting and formatting:

```bash
# Format code
ruff format .

# Check for lint issues
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Run pre-commit hooks manually
pre-commit run --all-files
```

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
