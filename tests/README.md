# Testing Framework

This directory contains the testing framework for cfmm2tar using a containerized dcm4che PACS instance.

## Overview

The testing framework provides:
- **Unit tests**: Tests that don't require a PACS server
- **Integration tests**: Tests that interact with a containerized dcm4chee PACS server
- **Docker Compose**: Configuration for spinning up a local dcm4chee PACS server
- **CI/CD**: GitHub Actions workflow for automated testing

## Requirements

- Docker and Docker Compose (for integration tests)
- Pixi (for dependency management)

## Running Tests Locally

### Install Dependencies

```bash
# Install pixi (if not already installed)
curl -fsSL https://pixi.sh/install.sh | bash

# Clone the repository and install dependencies
git clone https://github.com/khanlab/cfmm2tar
cd cfmm2tar
pixi install

# Activate the environment
pixi shell
```

### Run Unit Tests Only

Unit tests don't require a PACS server:

```bash
pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsUnit -v

# With coverage
pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsUnit -v --cov=cfmm2tar --cov-report=term-missing
```

Or without activating the shell:

```bash
pixi run pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsUnit -v

# With coverage
pixi run pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsUnit -v --cov=cfmm2tar --cov-report=term-missing
```

### Run Integration Tests

Integration tests require a running dcm4chee PACS server:

```bash
# Start the PACS server
cd tests
docker compose up -d

# Wait for services to be ready (can take 1-2 minutes)
sleep 60

# Run integration tests (from project root)
cd ..
pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsIntegration -v

# Or using pixi run
pixi run pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsIntegration -v

# Stop the PACS server
cd tests
docker compose down -v
```

### Run All Tests

```bash
# From within pixi shell
pytest tests/ -v

# Or using pixi run
pixi run pytest tests/ -v

# With coverage
pytest tests/ -v --cov=cfmm2tar --cov-report=term-missing --cov-report=html
```

### Generate Coverage Reports

The project uses `pytest-cov` for code coverage analysis:

```bash
# Run tests with coverage (terminal report)
pytest tests/ --cov=cfmm2tar --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=cfmm2tar --cov-report=html
# Open htmlcov/index.html in your browser

# Generate XML coverage report (for CI/CD)
pytest tests/ --cov=cfmm2tar --cov-report=xml

# Run only unit tests with coverage
pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsUnit --cov=cfmm2tar --cov-report=term-missing
```

Coverage reports help identify:
- Which code paths are tested
- Which lines need additional test coverage
- Overall project test coverage percentage

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
1. Sets up the pixi environment
2. Installs dependencies using pixi
3. Runs unit tests with code coverage
4. Starts the dcm4chee PACS server
5. Runs integration tests with coverage
6. Uploads coverage reports as artifacts
7. Displays coverage summary in workflow output
8. Cleans up

Coverage reports are available as downloadable artifacts from the GitHub Actions workflow runs.

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
