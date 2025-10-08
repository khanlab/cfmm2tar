# PyPI Publishing Setup

**Note:** This project is no longer published to PyPI. It now uses [pixi](https://pixi.sh) for dependency management instead. This document is kept for historical reference.

---

This document describes how to set up PyPI publishing for the cfmm2tar package.

## Trusted Publishing (Recommended)

The project is configured to use PyPI's trusted publishing feature, which doesn't require storing secrets in GitHub.

### Steps to Enable Trusted Publishing

1. **Go to PyPI** (https://pypi.org/) and log in with maintainer credentials

2. **Navigate to your account settings** → **Publishing**

3. **Add a new pending publisher** with these details:
   - **PyPI Project Name**: `cfmm2tar`
   - **Owner**: `khanlab`
   - **Repository name**: `cfmm2tar`
   - **Workflow name**: `publish-pypi.yml`
   - **Environment name**: `pypi`

4. **Save** the configuration

5. **Create a release** on GitHub:
   ```bash
   git tag v0.0.4
   git push origin v0.0.4
   ```
   Then create a release from the tag in GitHub UI

6. The workflow will automatically build and publish to PyPI!

## Manual Publishing (Alternative)

If you prefer to publish manually:

```bash
# Install build tools
pip install build twine

# Build the distribution
python -m build

# Upload to PyPI (will prompt for credentials)
twine upload dist/*

# Or upload to TestPyPI first
twine upload --repository testpypi dist/*
```

## Version Management

The version is defined in `pyproject.toml`:

```toml
[project]
name = "cfmm2tar"
version = "0.0.3"  # Update this for new releases
```

### Version Bump Process

1. Update version in `pyproject.toml`
2. Commit the change
3. Create and push a git tag:
   ```bash
   git tag v0.0.4
   git push origin v0.0.4
   ```
4. Create a GitHub release from the tag
5. The publish workflow will trigger automatically

## Testing the Build

Test the package build locally before releasing:

```bash
# Install build tools
pip install build

# Build the distribution
python -m build

# Check the contents
tar -tzf dist/cfmm2tar-*.tar.gz | head -20
```

## Troubleshooting

### Build Fails
- Check that `pyproject.toml` is valid: `python -m build --check`
- Ensure all required files are included in `MANIFEST.in`

### Publishing Fails
- Verify PyPI trusted publishing is set up correctly
- Check that the workflow has correct environment name (`pypi`)
- Ensure the GitHub Actions workflow has `id-token: write` permission

### Package Not Installable
- Test installation from TestPyPI first:
  ```bash
  pip install --index-url https://test.pypi.org/simple/ cfmm2tar
  ```
- Check that dependencies are correctly specified in `pyproject.toml`

## Package Metadata

The package includes:
- **Name**: cfmm2tar
- **Description**: Download a tarballed DICOM dataset from the CFMM DICOM server
- **License**: MIT
- **Python Requirement**: >=3.11
- **Dependencies**: pydicom>=2.4.0
- **Keywords**: DICOM, medical imaging, PACS, data retrieval, neuroimaging

## Post-Publishing Checklist

After publishing a new version:

- [ ] Verify package appears on PyPI: https://pypi.org/project/cfmm2tar/
- [ ] Test installation: `pip install cfmm2tar`
- [ ] Test the CLI: `cfmm2tar --help`
- [ ] Update documentation if needed
- [ ] Announce the release (if significant changes)

## Resources

- [PyPI Trusted Publishing Documentation](https://docs.pypi.org/trusted-publishers/)
- [Python Packaging Guide](https://packaging.python.org/)
- [GitHub Actions for PyPI](https://github.com/marketplace/actions/pypi-publish)
