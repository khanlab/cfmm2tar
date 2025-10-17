"""cfmm2tar - Download a tarballed DICOM dataset from the CFMM DICOM server."""

try:
    from ._version import __version__
except ImportError:
    # Fallback version if _version.py doesn't exist (e.g., in development)
    __version__ = "0.0.0+unknown"

# Expose API functions for programmatic use
from .api import (
    download_studies,
    download_studies_from_metadata,
    query_metadata,
)

__all__ = [
    "__version__",
    "query_metadata",
    "download_studies",
    "download_studies_from_metadata",
]
