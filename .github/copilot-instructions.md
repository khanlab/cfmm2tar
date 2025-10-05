# GitHub Copilot Instructions for cfmm2tar

## Project Overview
cfmm2tar is a Python tool for downloading DICOM datasets from the CFMM (Centre for Functional and Metabolic Mapping) DICOM server. It provides command-line utilities for querying, retrieving, and archiving medical imaging data.

## Key Architecture Components

### Core Modules
- **cfmm2tar/Dcm4cheUtils.py**: Wrapper around dcm4che tools for DICOM network operations (C-FIND, C-GET)
- **cfmm2tar/DicomSorter.py**: Organizes retrieved DICOM files by study, series, etc.
- **cfmm2tar/retrieve_cfmm_tar.py**: Main orchestration logic for querying and downloading studies
- **cfmm2tar/cli.py**: Command-line interface entry point

### Dependencies
- **dcm4che**: Java-based DICOM toolkit (external dependency, must be installed or containerized)
- **pydicom**: Python DICOM library for parsing and manipulating DICOM files
- **DicomRaw**: Additional DICOM utilities (included in Docker image)

## Code Style and Standards

### Python Version
- Target Python 3.11+
- Use modern Python features (type hints encouraged but not enforced)

### Code Quality
- Use `ruff` for linting and formatting (configured in pyproject.toml)
- Run `ruff check .` to lint code
- Run `ruff format .` to format code
- Pre-commit hooks are configured to run these automatically

### Testing
- Unit tests and integration tests in `tests/` directory
- Use pytest framework
- Integration tests require Docker and a containerized dcm4chee PACS server
- Mark tests appropriately: `@pytest.mark.unit` or `@pytest.mark.integration`

## Deployment Methods

### 1. Docker Container (Recommended for end users)
The Docker image includes all dependencies (Python, dcm4che, DicomRaw):
```bash
docker build -t cfmm2tar .
docker run -v /path/to/output:/data cfmm2tar [args]
```

### 2. Apptainer/Singularity Container
Similar to Docker but for HPC environments:
```bash
apptainer build cfmm2tar.sif docker://ghcr.io/khanlab/cfmm2tar
apptainer run cfmm2tar.sif [args]
```

### 3. PyPI Installation
For users who want to install as a Python package:
```bash
pip install cfmm2tar
```
Note: Requires either:
- dcm4che tools installed separately, OR
- Use `--dcm4che-container` flag to point to a container with dcm4che

## Important Conventions

### DICOM Network Operations
- Uses dcm4che command-line tools (`findscu`, `getscu`)
- Connection format: `AET@host:port` (e.g., `CFMM@dicom.cfmm.uwo.ca:11112`)
- Requires TLS for CFMM server (`--tls-aes` option)
- Authentication via username/password from `~/.uwo_credentials` or interactive prompt

### Study Identifiers
- **StudyInstanceUID**: Unique identifier for a DICOM study
- **StudyDescription**: Often formatted as `Principal^Project` at CFMM
- **PatientName**: Can include wildcards for searching
- **StudyDate**: Format YYYYMMDD, supports ranges (YYYYMMDD-YYYYMMDD)

### File Organization
- Downloaded DICOMs temporarily stored in intermediate directory
- Sorted by study, then series
- Compressed into tar files: `<PatientName>_<StudyDate>_<StudyDescription>.tar`

## Common Workflows

### Query Metadata Without Downloading
```python
# See cli.py metadata_file mode
# Queries PACS and exports study metadata to TSV
```

### Download Specific Studies
```python
# See cli.py uid_from_file mode
# Downloads studies by UID from a file
```

### Track Downloaded Studies
```python
# Use downloaded_uid_list file to avoid re-downloading
# File contains StudyInstanceUIDs, one per line
```

## Testing Guidelines

### Running Tests Locally
```bash
# Unit tests only (no PACS server needed)
pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsUnit -v

# Integration tests (requires Docker)
cd tests && docker compose up -d
pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsIntegration -v
cd tests && docker compose down -v
```

### Adding New Tests
1. Add to appropriate test class in `tests/test_dcm4che_utils.py`
2. Use fixtures from `tests/conftest.py` (dcm4che_server, temp_output_dir, etc.)
3. Mark tests with `@pytest.mark.unit` or `@pytest.mark.integration`

## Contributing

### Before Committing
1. Run pre-commit hooks: `pre-commit run --all-files`
2. Run tests: `pytest tests/`
3. Ensure code is formatted: `ruff format .`
4. Check for lint issues: `ruff check .`

### Pull Request Guidelines
- Keep changes minimal and focused
- Include tests for new functionality
- Update documentation if needed
- Ensure CI passes (GitHub Actions runs tests automatically)

## External Services

### CFMM DICOM Server
- Production server: `dicom.cfmm.uwo.ca:11112`
- Requires UWO credentials
- Uses TLS encryption
- Access controlled by study permissions

### Container Registries
- Docker Hub: `khanlab/cfmm2tar`
- GitHub Container Registry: `ghcr.io/khanlab/cfmm2tar`

## Useful Commands

```bash
# Build Docker image
docker build -t cfmm2tar .

# Run tests in container
docker run --rm cfmm2tar pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsUnit -v

# Install for development
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"  # or: uv pip install -e .

# Format code
ruff format .

# Lint code
ruff check .

# Run pre-commit hooks
pre-commit run --all-files
```

## Notes for AI Assistance

- When modifying DICOM operations, be aware of dcm4che command syntax
- Pay attention to subprocess calls and timeout handling
- Test with both container and local dcm4che installations
- Consider backward compatibility with existing tar file naming conventions
- Be mindful of credentials handling (never log passwords)
