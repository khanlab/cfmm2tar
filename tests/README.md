# Testing Framework

This directory contains the testing framework for cfmm2tar using a containerized dcm4che PACS instance.

## Overview

The testing framework provides:
- **Unit tests**: Tests that don't require a PACS server
- **Integration tests**: Tests that interact with a containerized dcm4chee PACS server
- **Docker Compose**: Configuration for spinning up a local dcm4chee PACS server
- **CI/CD**: GitHub Actions workflow for automated testing

## Requirements

- Docker and Docker Compose
- Python 3.11+
- pytest
- dcm4che tools (for integration tests)

## Running Tests Locally

### Install Dependencies

```bash
# Install Python dependencies
uv pip install -e ".[dev]"

# Or with pip
pip install -e .
pip install pytest pydicom numpy
```

### Install dcm4che Tools

For integration tests, you need dcm4che tools installed:

```bash
export DCM4CHE_VERSION=5.24.1
sudo bash install_dcm4che_ubuntu.sh /opt
```

### Run Unit Tests Only

Unit tests don't require a PACS server:

```bash
pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsUnit -v
```

### Run Integration Tests

Integration tests require a running dcm4chee PACS server:

```bash
# Start the PACS server
cd tests
docker compose up -d

# Wait for services to be ready (can take 1-2 minutes)
sleep 60

# Run integration tests
cd ..
pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsIntegration -v

# Stop the PACS server
cd tests
docker compose down -v
```

### Run All Tests

```bash
pytest tests/ -v
```

## Docker Compose Services

The `docker-compose.yml` file sets up:

1. **LDAP Server** (`ldap`): Authentication service
   - Port: 389
   
2. **PostgreSQL Database** (`db`): Storage for PACS metadata
   - Database: pacsdb
   - User: pacs / Password: pacs

3. **dcm4chee Archive** (`arc`): PACS server
   - Web UI: http://localhost:8080/dcm4chee-arc/ui2
   - DICOM port: 11112
   - AE Title: DCM4CHEE
   - Admin user: admin / Password: admin

## CI/CD

The GitHub Actions workflow (`.github/workflows/test.yml`) automatically:
1. Sets up the Python environment
2. Installs dependencies
3. Installs dcm4che tools
4. Runs unit tests
5. Starts the dcm4chee PACS server
6. Runs integration tests
7. Cleans up

## Test Structure

- `conftest.py`: Pytest fixtures and configuration
  - `dcm4che_server`: Fixture that starts/stops the PACS server
  - `temp_output_dir`: Fixture for temporary test directories
  - `sample_dicom_file`: Fixture for creating test DICOM files

- `test_dcm4che_utils.py`: Tests for the Dcm4cheUtils class
  - Unit tests: Test initialization and basic functionality
  - Integration tests: Test DICOM operations against a real PACS

## Adding New Tests

1. Add test functions to existing test files or create new test files
2. Use `@pytest.mark.unit` for unit tests
3. Use `@pytest.mark.integration` for integration tests
4. Use fixtures from `conftest.py` for common setup/teardown

Example:

```python
@pytest.mark.integration
def test_my_feature(dcm4che_server, temp_output_dir):
    # Your test code here
    pass
```

## Troubleshooting

### PACS Server Not Ready

If integration tests fail, the PACS server may need more time to start:
- Increase the sleep time in the test setup
- Check logs: `docker compose logs arc`

### Connection Refused

Ensure Docker services are running:
```bash
cd tests
docker compose ps
```

### Port Conflicts

If port 11112 is already in use, modify `docker-compose.yml` to use different ports.

## Cleaning Up

Remove all Docker volumes and containers:

```bash
cd tests
docker compose down -v
```
