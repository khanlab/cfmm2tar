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

You can query and export study metadata to a TSV file without downloading the actual DICOM files. Metadata is always saved to `study_metadata.tsv` in the output directory:

```bash
# Export metadata for all studies on a specific date
cfmm2tar -m -d '20240101' output_dir

# Export metadata for a specific Principal^Project
cfmm2tar -m -p 'Khan^NeuroAnalytics' -d '20240101-20240131' output_dir
```

This creates a TSV file at `output_dir/study_metadata.tsv` with columns:
- `StudyInstanceUID`: Unique identifier for the study
- `PatientName`: Patient name
- `PatientID`: Patient ID
- `StudyDate`: Date of the study
- `StudyDescription`: Study description (typically Principal^Project)

Note: When downloading studies (without `-m`), metadata is automatically saved to `study_metadata.tsv` in the output directory.

### Download from UID List

After reviewing the metadata file, you can download specific studies:

```bash
# Download all studies from the metadata file
cfmm2tar --from-metadata study_metadata.tsv output_dir

# Or create a filtered version of the metadata file and download only those
# (e.g., filter in Excel, grep, awk, or Python)
cfmm2tar --from-metadata study_metadata_filtered.tsv output_dir

# You can also use a simple text file with one UID per line
cfmm2tar --from-metadata uid_list.txt output_dir
```

### Workflow Example

1. **Query and export metadata** for review:
   ```bash
   cfmm2tar -m -p 'Khan^NeuroAnalytics' -d '20240101-20240131' output_dir
   ```
   This creates `output_dir/study_metadata.tsv`

2. **Review and filter** the `study_metadata.tsv` file (e.g., in Excel or with command-line tools)

3. **Download filtered studies**:
   ```bash
   cfmm2tar --from-metadata output_dir/study_metadata_filtered.tsv output_dir
   ```

This workflow is especially useful when:
- You want to review available studies before downloading
- Storage is limited and you need to select specific studies
- You're sharing the metadata with collaborators to decide what to download
- You need to filter studies based on multiple criteria

## Python API

In addition to the command-line interface, `cfmm2tar` provides a Python API for programmatic access. This is useful for integration into Python scripts, Jupyter notebooks, or workflow management tools like Snakemake.

### Installation for API Use

```bash
# Basic installation
pip install cfmm2tar

# With pandas support for DataFrame operations
pip install cfmm2tar[dataframe]
```

**Note:** The Python API requires dcm4che tools to be installed separately, or you can use the `--dcm4che-container` option (future feature) to point to a container with dcm4che.

### Credential Management

The API functions automatically handle credentials in the following order of precedence:

1. **Provided parameters**: `username` and `password` arguments (if supplied)
2. **Credentials file**: `~/.uwo_credentials` (line 1: username, line 2: password)
3. **Environment variables**: `UWO_USERNAME` and `UWO_PASSWORD`

This means you can use the API without explicitly passing credentials in most cases:

```python
from cfmm2tar import query_metadata

# Credentials automatically loaded from ~/.uwo_credentials or environment variables
studies = query_metadata(
    study_description="Khan^NeuroAnalytics",
    study_date="20240101-20240131"
)
```

Or provide credentials explicitly when needed:

```python
studies = query_metadata(
    username="your_username",
    password="your_password",
    study_description="Khan^NeuroAnalytics",
    study_date="20240101-20240131"
)
```

Or use environment variables in scripts or CI/CD:

```bash
export UWO_USERNAME="your_username"
export UWO_PASSWORD="your_password"
python your_script.py
```

### Query Metadata

Query study metadata and get results as a list of dictionaries or pandas DataFrame:

```python
from cfmm2tar import query_metadata

# Query metadata (credentials from ~/.uwo_credentials or env vars)
studies = query_metadata(
    study_description="Khan^NeuroAnalytics",
    study_date="20240101-20240131",
    patient_name="*",
    return_type="list"  # or "dataframe" for pandas DataFrame
)

print(f"Found {len(studies)} studies")
for study in studies:
    print(f"  {study['StudyDate']}: {study['StudyDescription']}")
```

With pandas DataFrame:

```python
import pandas as pd
from cfmm2tar import query_metadata

# Query metadata and get as DataFrame
df = query_metadata(
    study_description="Khan^*",
    study_date="20240101-",
    return_type="dataframe"
)

# Filter and analyze
recent_studies = df[df['StudyDate'] > '20240601']
print(recent_studies[['StudyDate', 'PatientName', 'StudyDescription']])
```

### Download Studies

Download studies programmatically:

```python
from cfmm2tar import download_studies

# Download studies matching criteria (credentials from ~/.uwo_credentials or env vars)
output_dir = download_studies(
    output_dir="/path/to/output",
    study_description="Khan^NeuroAnalytics",
    study_date="20240101",
    patient_name="*subj01*"
)

print(f"Studies downloaded to: {output_dir}")
```

Download a specific study by UID:

```python
from cfmm2tar import download_studies

download_studies(
    output_dir="/path/to/output",
    study_instance_uid="1.2.840.113619.2.55.3.1234567890.123"
)
```

### Download from Metadata

Download studies using metadata from various sources:

```python
from cfmm2tar import download_studies_from_metadata

# From a list of study metadata dicts (credentials from ~/.uwo_credentials or env vars)
studies = [
    {'StudyInstanceUID': '1.2.3.4', 'PatientName': 'Patient1'},
    {'StudyInstanceUID': '5.6.7.8', 'PatientName': 'Patient2'}
]
download_studies_from_metadata(
    output_dir="/path/to/output",
    metadata=studies
)

# From a TSV file
download_studies_from_metadata(
    output_dir="/path/to/output",
    metadata="study_metadata.tsv"
)

# From a pandas DataFrame
import pandas as pd
df = pd.read_csv("study_metadata.tsv", sep="\t")
filtered_df = df[df['StudyDate'] > '20240101']
download_studies_from_metadata(
    output_dir="/path/to/output",
    metadata=filtered_df
)
```

### Complete Workflow Example

Here's a complete workflow that queries metadata, filters studies, and downloads selected ones:

```python
from cfmm2tar import query_metadata, download_studies_from_metadata
import pandas as pd

# Step 1: Query all available studies (credentials from ~/.uwo_credentials or env vars)
studies_df = query_metadata(
    study_description="Khan^*",
    study_date="20240101-20240131",
    return_type="dataframe"
)

print(f"Found {len(studies_df)} total studies")

# Step 2: Filter studies based on criteria
# For example, only studies with specific patient names
filtered_df = studies_df[
    studies_df['PatientName'].str.contains('subj0[1-3]', regex=True)
]

print(f"Filtered to {len(filtered_df)} studies")

# Step 3: Download the filtered studies
download_studies_from_metadata(
    output_dir="/path/to/output",
    metadata=filtered_df
)

print("Download complete!")
```

### Use in Snakemake

The Python API works seamlessly with Snakemake workflows:

```python
# Snakefile
from cfmm2tar import query_metadata, download_studies_from_metadata

# Query metadata in a rule
rule query_studies:
    output:
        "metadata/study_list.tsv"
    run:
        # Credentials automatically loaded from env vars or ~/.uwo_credentials
        studies = query_metadata(
            study_description=config["project"],
            study_date=config["date_range"],
            return_type="dataframe"
        )
        studies.to_csv(output[0], sep="\t", index=False)

# Download studies in another rule
rule download_studies:
    input:
        "metadata/study_list.tsv"
    output:
        directory("data/dicoms")
    run:
        download_studies_from_metadata(
            output_dir=output[0],
            metadata=input[0]
        )
```

### API Reference

#### `query_metadata()`

Query study metadata from the DICOM server.

**Parameters:**
- `username` (str, optional): UWO username for authentication (see credential precedence below)
- `password` (str, optional): UWO password for authentication (see credential precedence below)
- `study_description` (str): Study description search string (default: "*")
- `study_date` (str): Date search string (default: "-")
- `patient_name` (str): PatientName search string (default: "*")
- `dicom_server` (str): DICOM server connection string (default: "CFMM@dicom.cfmm.uwo.ca:11112")
- `dcm4che_options` (str): Additional dcm4che options (default: "")
- `force_refresh_trust_store` (bool): Force refresh trust store (default: False)
- `return_type` (str): "list" or "dataframe" (default: "list")

**Credential Precedence:**
1. Provided `username`/`password` parameters
2. `~/.uwo_credentials` file (line 1: username, line 2: password)
3. `UWO_USERNAME` and `UWO_PASSWORD` environment variables

**Returns:**
- List of dicts or pandas DataFrame with study metadata

#### `download_studies()`

Download DICOM studies and create tar archives.

**Parameters:**
- `output_dir` (str): Output directory for tar archives
- `username` (str, optional): UWO username for authentication (see credential precedence)
- `password` (str, optional): UWO password for authentication (see credential precedence)
- `study_description` (str): Study description search string (default: "*")
- `study_date` (str): Date search string (default: "-")
- `patient_name` (str): PatientName search string (default: "*")
- `study_instance_uid` (str): Specific StudyInstanceUID (default: "*")
- `temp_dir` (str, optional): Temporary directory for intermediate files
- `dicom_server` (str): DICOM server connection string (default: "CFMM@dicom.cfmm.uwo.ca:11112")
- `dcm4che_options` (str): Additional dcm4che options (default: "")
- `force_refresh_trust_store` (bool): Force refresh trust store (default: False)
- `keep_sorted_dicom` (bool): Keep sorted DICOM files (default: False)

**Returns:**
- Path to output directory

#### `download_studies_from_metadata()`

Download studies using UIDs from metadata source.

**Parameters:**
- `output_dir` (str): Output directory for tar archives
- `metadata` (str, list, or DataFrame): Metadata source (file path, list of dicts, or DataFrame)
- `username` (str, optional): UWO username for authentication (see credential precedence)
- `password` (str, optional): UWO password for authentication (see credential precedence)
- `temp_dir` (str, optional): Temporary directory for intermediate files
- `dicom_server` (str): DICOM server connection string (default: "CFMM@dicom.cfmm.uwo.ca:11112")
- `dcm4che_options` (str): Additional dcm4che options (default: "")
- `force_refresh_trust_store` (bool): Force refresh trust store (default: False)
- `keep_sorted_dicom` (bool): Keep sorted DICOM files (default: False)

**Returns:**
- Path to output directory

### Examples

For complete working examples, see the `examples/` directory:

- **`examples/api_usage.py`**: Interactive examples demonstrating various API usage patterns
- **`examples/Snakefile_example`**: Example Snakemake workflow integrating cfmm2tar
- **`examples/README.md`**: Detailed documentation for the examples

Run the interactive examples:
```bash
python examples/api_usage.py
```

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

# Run unit tests with coverage
pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsUnit -v --cov=cfmm2tar --cov-report=term-missing

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

# Run all tests with coverage
pixi run pytest tests/ -v --cov=cfmm2tar --cov-report=term-missing --cov-report=html
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

### Test Coverage

The project uses `pytest-cov` for code coverage analysis:

```bash
# Run tests with coverage report
pytest tests/ --cov=cfmm2tar --cov-report=term-missing --cov-report=html

# View coverage report in browser
# Open htmlcov/index.html in your browser

# Generate XML coverage report (for CI/CD integration)
pytest tests/ --cov=cfmm2tar --cov-report=xml
```

Coverage reports are automatically generated in CI/CD and uploaded as artifacts.

### Continuous Integration

The project uses GitHub Actions for automated testing. The workflow:
1. Sets up the pixi environment
2. Runs unit tests with code coverage on every push and pull request
3. Starts a containerized dcm4chee PACS server
4. Runs integration tests against the PACS server with coverage
5. Uploads coverage reports as artifacts
6. Displays coverage summary in the workflow

See [.github/workflows/test.yml](.github/workflows/test.yml) for the complete workflow.
