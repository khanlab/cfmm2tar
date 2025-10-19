#!/usr/bin/env python3
"""
Example demonstrating the skip_derived functionality in cfmm2tar.

This example shows how to use the --skip-derived option both via CLI and API.
"""

# ==============================================================================
# CLI Usage
# ==============================================================================

# Example 1: Download studies with skip-derived flag
# This will skip DICOM files that have ImageType containing "DERIVED"
"""
cfmm2tar --skip-derived -p 'Khan^NeuroAnalytics' -d '20240101' /path/to/output
"""

# Example 2: Query metadata first, then download with skip-derived
"""
# First, query and save metadata
cfmm2tar -m -p 'Khan^NeuroAnalytics' -d '20240101' /path/to/output

# Then download using the metadata file, skipping derived images
cfmm2tar --skip-derived --from-metadata /path/to/output/study_metadata.tsv /path/to/output
"""

# ==============================================================================
# Python API Usage
# ==============================================================================

# Example 3: Using the Python API with skip_derived=True
"""
from cfmm2tar.api import download_studies

# Download studies, skipping derived images
output = download_studies(
    output_dir="/path/to/output",
    study_description="Khan^NeuroAnalytics",
    study_date="20240101",
    skip_derived=True  # This is the key parameter
)
print(f"Downloaded to: {output}")
"""

# Example 4: Download from metadata with skip_derived
"""
from cfmm2tar.api import download_studies_from_metadata

# Download specific studies from metadata, skipping derived images
output = download_studies_from_metadata(
    output_dir="/path/to/output",
    metadata="study_metadata.tsv",
    skip_derived=True
)
print(f"Downloaded to: {output}")
"""

# ==============================================================================
# What gets skipped?
# ==============================================================================

"""
The skip_derived option filters out DICOM files where the ImageType tag contains
"DERIVED". This typically includes:

- Reformatted images (MPR, MIP, etc.)
- Screen captures
- Derived/calculated images
- Post-processed images

Only ORIGINAL/PRIMARY images will be included in the tar file when skip_derived=True.

Example ImageType values:
- ORIGINAL\\PRIMARY          -> Included (not derived)
- DERIVED\\SECONDARY         -> Skipped (derived)
- DERIVED\\PRIMARY\\MPR      -> Skipped (derived)
- ORIGINAL\\PRIMARY\\SCOUT   -> Included (not derived, even if scout)
"""

print(__doc__)
