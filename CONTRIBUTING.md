# Contributing to cfmm2tar

Thank you for your interest in contributing to cfmm2tar! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- [Pixi](https://pixi.sh) package manager
- Docker (for running integration tests)
- Git

### Setting Up Your Development Environment

1. **Install pixi** (if not already installed):
   ```bash
   curl -fsSL https://pixi.sh/install.sh | bash
   ```

2. **Clone the repository:**
   ```bash
   git clone https://github.com/khanlab/cfmm2tar
   cd cfmm2tar
   ```

3. **Install dependencies (including dev dependencies):**
   ```bash
   pixi install
   ```

4. **Activate the development environment:**
   ```bash
   pixi shell
   ```
   
   Or use shell-hook for automatic activation:
   ```bash
   eval "$(pixi shell-hook)"
   ```

5. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```
   
   This will automatically run code quality checks before each commit.

## Code Quality Standards

This project uses several tools to maintain code quality:

## Versioning

This project uses dynamic versioning based on git tags:

- Version numbers are automatically determined from git tags using `hatch-vcs`
- Tags should follow semantic versioning (e.g., `v2.1.0`, `v2.1.1`)
- When you build the package, the version is extracted from the most recent git tag
- During development (without a build), the version falls back to `0.0.0+unknown`

### Creating a Release

To create a new release:

1. Tag the commit with a version number:
   ```bash
   git tag v2.1.0
   git push origin v2.1.0
   ```

2. Create a GitHub release from the tag (or the workflow will create one automatically)

3. The CI/CD workflows will automatically:
   - Build the Python package with the version from the tag
   - Build the Docker container with the version label
   - Publish to container registries

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
# Activate the pixi environment
pixi shell

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

Alternatively, you can run tests using pixi directly:

```bash
# Run unit tests without activating the shell
pixi run pytest tests/test_dcm4che_utils.py::TestDcm4cheUtilsUnit -v

# Run all tests
pixi run pytest tests/ -v
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

The tool is primarily deployed using pixi for dependency management:
1. **Pixi-based installation**: All dependencies (Python, dcm4che tools, libraries) managed automatically
2. **Docker container**: Available for containerized environments (legacy support)
3. **Apptainer container**: For HPC environments (legacy support)

## Getting Help

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Be respectful and constructive in discussions

## License

By contributing to cfmm2tar, you agree that your contributions will be licensed under the MIT License.
