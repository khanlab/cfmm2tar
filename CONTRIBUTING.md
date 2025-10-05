# Contributing to cfmm2tar

Thank you for your interest in contributing to cfmm2tar! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Docker (for running integration tests)
- Git

### Setting Up Your Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/khanlab/cfmm2tar
   cd cfmm2tar
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   ```

3. **Install development dependencies:**
   ```bash
   pip install ruff pre-commit pytest pydicom numpy
   ```

4. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```
   
   This will automatically run code quality checks before each commit.

5. **Install dcm4che tools (for integration tests):**
   ```bash
   export DCM4CHE_VERSION=5.24.1
   sudo bash install_dcm4che_ubuntu.sh /opt
   ```

## Code Quality Standards

This project uses several tools to maintain code quality:

### Linting and Formatting

We use [ruff](https://github.com/astral-sh/ruff) for both linting and formatting:

```bash
# Format code
ruff format .

# Check for lint issues
ruff check .

# Auto-fix issues where possible
ruff check --fix .
```

### Pre-commit Hooks

Pre-commit hooks automatically run quality checks before each commit. To run them manually:

```bash
pre-commit run --all-files
```

The hooks include:
- `ruff` for linting and formatting
- Trailing whitespace removal
- End-of-file fixer
- YAML/TOML validation
- Large file checker
- Merge conflict checker

## Testing

### Running Tests

The project includes both unit tests and integration tests:

```bash
# Run unit tests only (no PACS server required)
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

### Writing Tests

- Place unit tests in `tests/` directory
- Use `@pytest.mark.unit` for unit tests
- Use `@pytest.mark.integration` for integration tests
- Use fixtures from `tests/conftest.py`

Example:
```python
import pytest

@pytest.mark.unit
def test_something():
    # Your test code here
    pass

@pytest.mark.integration
def test_with_pacs(dcm4che_server, temp_output_dir):
    # Integration test code here
    pass
```

## Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clear, concise commit messages
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks:**
   ```bash
   ruff format .
   ruff check .
   pytest tests/
   ```

4. **Push your branch and create a pull request:**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Wait for CI checks:**
   - GitHub Actions will automatically run tests
   - Quality checks will verify code formatting
   - All checks must pass before merging

## Code Style Guidelines

### Python Style

- Follow PEP 8 guidelines (enforced by ruff)
- Use type hints where appropriate
- Write docstrings for public functions and classes
- Keep functions focused and reasonably sized

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add feature", "Fix bug")
- Reference issue numbers when applicable

### Documentation

- Update README.md for user-facing changes
- Update docstrings for code changes
- Add examples for new features

## Architecture Overview

### Key Components

- **cfmm2tar/cli.py**: Command-line interface
- **cfmm2tar/Dcm4cheUtils.py**: Wrapper for dcm4che tools (DICOM network operations)
- **cfmm2tar/DicomSorter.py**: DICOM file organization and archiving
- **cfmm2tar/retrieve_cfmm_tar.py**: Main orchestration logic

### DICOM Operations

The tool uses dcm4che command-line utilities:
- `findscu`: Query PACS for studies
- `getscu`: Retrieve DICOM files

### Deployment Methods

The tool supports three deployment methods:
1. **Docker container**: All dependencies included
2. **Apptainer container**: For HPC environments
3. **PyPI installation**: Requires separate dcm4che setup

## Getting Help

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Be respectful and constructive in discussions

## License

By contributing to cfmm2tar, you agree that your contributions will be licensed under the MIT License.
