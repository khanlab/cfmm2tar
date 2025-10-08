#!/usr/bin/env python3
"""
Trust store management for dcm4che tools.

This module handles downloading and caching the UWO Sectigo certificate
and creating a JKS trust store for use with dcm4che tools.

Author: GitHub Copilot
Date: 2024
"""

import logging
import os
import subprocess
import tempfile
from pathlib import Path


# URL for the UWO Sectigo certificate
SECTIGO_CERT_URL = (
    "https://pki.uwo.ca/sectigo/certificates/SectigoRSAOrganizationValidationSecureServerCA-int.pem"
)

# Default cache directory in user's home
DEFAULT_CACHE_DIR = os.path.expanduser("~/.cfmm2tar")

# Trust store filename
TRUSTSTORE_FILENAME = "mytruststore.jks"

# Trust store password
TRUSTSTORE_PASSWORD = "secret"

# Certificate alias in the trust store
CERT_ALIAS = "uwo-sectigo"

logger = logging.getLogger(__name__)


def get_truststore_path(cache_dir=None):
    """
    Get the path to the trust store file.

    Args:
        cache_dir: Optional cache directory path. If None, uses default.

    Returns:
        Path object pointing to the trust store file.
    """
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR

    return Path(cache_dir) / TRUSTSTORE_FILENAME


def ensure_truststore(cache_dir=None, force_refresh=False):
    """
    Ensure a valid trust store exists, creating it if necessary.

    This function:
    1. Checks if trust store already exists (unless force_refresh is True)
    2. Downloads the Sectigo certificate from UWO PKI
    3. Creates a JKS trust store using keytool
    4. Caches the trust store for future use

    Args:
        cache_dir: Optional cache directory path. If None, uses default.
        force_refresh: If True, recreates the trust store even if it exists.

    Returns:
        Path to the trust store file.

    Raises:
        RuntimeError: If trust store creation fails.
    """
    if cache_dir is None:
        cache_dir = DEFAULT_CACHE_DIR

    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    truststore_path = get_truststore_path(cache_dir)

    # Check if trust store already exists
    if truststore_path.exists() and not force_refresh:
        logger.info(f"Using cached trust store: {truststore_path}")
        return truststore_path

    logger.info("Creating trust store...")

    # Download the certificate to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as cert_file:
        cert_filename = cert_file.name

    try:
        # Download certificate using wget
        logger.info(f"Downloading certificate from {SECTIGO_CERT_URL}")
        download_cmd = ["wget", "-O", cert_filename, SECTIGO_CERT_URL]

        result = subprocess.run(
            download_cmd, capture_output=True, text=True, timeout=30, check=False
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to download certificate: {result.stderr or result.stdout}"
            )

        # Verify the certificate file was downloaded and is not empty
        if not os.path.exists(cert_filename) or os.path.getsize(cert_filename) == 0:
            raise RuntimeError("Downloaded certificate file is empty or does not exist")

        logger.info("Certificate downloaded successfully")

        # Remove existing trust store if it exists (for refresh)
        if truststore_path.exists():
            logger.info(f"Removing existing trust store: {truststore_path}")
            truststore_path.unlink()

        # Create JKS trust store using keytool
        logger.info(f"Creating JKS trust store: {truststore_path}")
        keytool_cmd = [
            "keytool",
            "-importcert",
            "-trustcacerts",
            "-alias",
            CERT_ALIAS,
            "-file",
            cert_filename,
            "-keystore",
            str(truststore_path),
            "-storepass",
            TRUSTSTORE_PASSWORD,
            "-noprompt",
        ]

        result = subprocess.run(
            keytool_cmd, capture_output=True, text=True, timeout=30, check=False
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to create trust store: {result.stderr or result.stdout}")

        if not truststore_path.exists():
            raise RuntimeError(f"Trust store was not created at {truststore_path}")

        logger.info(f"Trust store created successfully: {truststore_path}")

        return truststore_path

    finally:
        # Clean up temporary certificate file
        if os.path.exists(cert_filename):
            os.unlink(cert_filename)


def get_truststore_option(cache_dir=None, force_refresh=False):
    """
    Get the --trust-store command line option for dcm4che tools.

    Args:
        cache_dir: Optional cache directory path. If None, uses default.
        force_refresh: If True, recreates the trust store even if it exists.

    Returns:
        String containing the --trust-store option with path.

    Raises:
        RuntimeError: If trust store creation fails.
    """
    truststore_path = ensure_truststore(cache_dir=cache_dir, force_refresh=force_refresh)
    return f"--trust-store {truststore_path}"
