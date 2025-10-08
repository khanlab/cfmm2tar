# cfmm2tar

Download a tarballed DICOM dataset from the CFMM DICOM server

## Overview

`cfmm2tar` is a command-line tool for querying and downloading DICOM studies from the CFMM (Centre for Functional and Metabolic Mapping) DICOM server.

## Installation & Usage

### Installation with Pixi

`cfmm2tar` uses [pixi](https://pixi.sh) for dependency management, which automatically handles all dependencies including Python, dcm4che tools, and required libraries.

**Requirements:** 
- [Pixi](https://pixi.sh) package manager
- Git

**Installation:**

1. **Install pixi** (if not already installed):
   ```bash
   curl -fsSL https://pixi.sh/install.sh | bash
   ```
   
   Or on Windows:
   ```powershell
   iwr -useb https://pixi.sh/install.ps1 | iex
   ```

2. **Clone the repository:**
   ```bash
   git clone https://github.com/khanlab/cfmm2tar
   cd cfmm2tar
   ```

3. **Install dependencies:**
   ```bash
   pixi install
   ```

4. **Activate the environment:**
   ```bash
   # Option 1: Start a shell with the environment activated
   pixi shell
   
   # Option 2: Use pixi shell-hook for automatic activation
   eval "$(pixi shell-hook)"
   ```

**Usage:**
```bash
OUTPUT_DIR=/path/to/dir
mkdir -p ${OUTPUT_DIR}

# Show help
cfmm2tar --help

# Download studies for a specific Principal^Project on a specific date
cfmm2tar -p 'Khan^NeuroAnalytics' -d '20240101' ${OUTPUT_DIR}

# Download all studies on a specific date
cfmm2tar -d '20170530' ${OUTPUT_DIR}

# Download a specific study by StudyInstanceUID
cfmm2tar -u '1.2.840.113619.2.55.3.1234567890.123' ${OUTPUT_DIR}
```

You will be prompted for your UWO username and password. You can only download datasets to which you have read permissions.

**Running without activating the shell:**

You can also run commands directly using `pixi run`:
```bash
pixi run cfmm2tar -p 'Khan^Project' -d '20240101' ${OUTPUT_DIR}
```

## Why Pixi?

Using pixi provides several advantages:

- ✅ **All dependencies included**: Python, dcm4che tools, and all libraries are automatically managed
- ✅ **Cross-platform**: Works on Linux, macOS, and Windows
- ✅ **Reproducible environments**: Lock file ensures consistent dependency versions
- ✅ **No containers needed**: Direct installation on your system
- ✅ **Easy development**: Simple setup for both users and contributors
- ✅ **Fast**: Binary packages from conda-forge install quickly

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

These are automatically included when using pixi, as the Java runtime is installed as a dependency of dcm4che-tools.

**Note:** If trust store setup fails (e.g., network issues, missing tools), `cfmm2tar` will log a warning but continue to operate. However, TLS connections may fail without a valid trust store.

## Development and Testing

### Development Setup

For contributors and developers:

```bash
# Install pixi (if not already installed)
curl -fsSL https://pixi.sh/install.sh | bash

# Clone the repository
git clone https://github.com/khanlab/cfmm2tar
cd cfmm2tar

# Install dependencies (including dev dependencies)
pixi install

# Activate the development environment
pixi shell

# Set up pre-commit hooks (runs quality checks before each commit)
pre-commit install
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
# Activate the pixi environment
pixi shell

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

Alternatively, you can run tests using pixi directly without activating the shell:

```bash
# Run unit tests
pixi run pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsUnit -v

# Run all tests
pixi run pytest tests/ -v
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

### Continuous Integration

The project uses GitHub Actions for automated testing. The workflow:
1. Sets up the pixi environment
2. Runs unit tests on every push and pull request
3. Starts a containerized dcm4chee PACS server
4. Runs integration tests against the PACS server
5. Reports results

See [.github/workflows/test.yml](.github/workflows/test.yml) for the complete workflow.
