"""cfmm2tar - Download a tarballed DICOM dataset from the CFMM DICOM server."""

try:
    from ._version import __version__
except ImportError:
    # Fallback version if _version.py doesn't exist (e.g., in development)
    __version__ = "0.0.0+unknown"
