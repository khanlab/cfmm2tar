"""
Unit tests for truststore module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cfmm2tar import truststore


@pytest.mark.unit
class TestTruststore:
    """Unit tests for truststore module."""

    def test_get_truststore_path_default(self):
        """Test getting default trust store path."""
        path = truststore.get_truststore_path()
        assert path == Path(truststore.DEFAULT_CACHE_DIR) / truststore.TRUSTSTORE_FILENAME
        assert str(path).endswith("mytruststore.jks")

    def test_get_truststore_path_custom(self):
        """Test getting custom trust store path."""
        custom_dir = "/custom/cache/dir"
        path = truststore.get_truststore_path(cache_dir=custom_dir)
        assert path == Path(custom_dir) / truststore.TRUSTSTORE_FILENAME

    def test_get_truststore_option_format(self):
        """Test that get_truststore_option returns correct format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock subprocess calls
            with patch("subprocess.run") as mock_run:
                # Mock successful wget
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = ""
                mock_run.return_value.stderr = ""

                # Create a fake cert file that will be read
                with patch("tempfile.NamedTemporaryFile") as mock_temp:
                    mock_temp.return_value.__enter__.return_value.name = os.path.join(
                        temp_dir, "cert.pem"
                    )
                    # Create the fake cert file
                    Path(mock_temp.return_value.__enter__.return_value.name).touch()

                    # Mock os.path.exists and os.path.getsize for cert verification
                    def mock_exists(path):
                        if "cert.pem" in path or "mytruststore.jks" in path:
                            return True
                        return os.path.exists(path)

                    def mock_getsize(path):
                        if "cert.pem" in path:
                            return 100  # Non-zero size
                        return os.path.getsize(path)

                    with patch("os.path.exists", side_effect=mock_exists):
                        with patch("os.path.getsize", side_effect=mock_getsize):
                            with patch("os.unlink"):
                                option = truststore.get_truststore_option(cache_dir=temp_dir)

                                # Should contain --trust-store followed by path
                                assert option.startswith("--trust-store ")
                                assert "mytruststore.jks" in option

    def test_ensure_truststore_uses_cache(self):
        """Test that ensure_truststore uses cached file if it exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            truststore_path = Path(temp_dir) / truststore.TRUSTSTORE_FILENAME
            # Create a fake existing truststore
            truststore_path.touch()

            # Should return immediately without calling wget or keytool
            with patch("subprocess.run") as mock_run:
                result = truststore.ensure_truststore(cache_dir=temp_dir, force_refresh=False)

                # subprocess should not be called since cache exists
                mock_run.assert_not_called()
                assert result == truststore_path

    def test_ensure_truststore_force_refresh(self):
        """Test that force_refresh recreates the truststore."""
        with tempfile.TemporaryDirectory() as temp_dir:
            truststore_path = Path(temp_dir) / truststore.TRUSTSTORE_FILENAME
            # Create a fake existing truststore
            truststore_path.touch()

            # Mock subprocess calls
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = ""
                mock_run.return_value.stderr = ""

                # Mock temp file creation
                with patch("tempfile.NamedTemporaryFile") as mock_temp:
                    fake_cert = os.path.join(temp_dir, "cert.pem")
                    mock_temp.return_value.__enter__.return_value.name = fake_cert
                    Path(fake_cert).touch()

                    # Mock file operations
                    def mock_exists(path):
                        if "cert.pem" in path or "mytruststore.jks" in path:
                            return True
                        return os.path.exists(path)

                    def mock_getsize(path):
                        if "cert.pem" in path:
                            return 100
                        return os.path.getsize(path)

                    with patch("os.path.exists", side_effect=mock_exists):
                        with patch("os.path.getsize", side_effect=mock_getsize):
                            with patch("os.unlink"):
                                result = truststore.ensure_truststore(
                                    cache_dir=temp_dir, force_refresh=True
                                )

                                # subprocess should be called (wget and keytool)
                                assert mock_run.call_count >= 2
                                assert result == truststore_path

    def test_ensure_truststore_download_failure(self):
        """Test handling of certificate download failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock failed wget
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stdout = ""
                mock_run.return_value.stderr = "Failed to download"

                with patch("tempfile.NamedTemporaryFile") as mock_temp:
                    fake_cert = os.path.join(temp_dir, "cert.pem")
                    mock_temp.return_value.__enter__.return_value.name = fake_cert

                    with patch("os.unlink"):
                        with pytest.raises(RuntimeError, match="Failed to download certificate"):
                            truststore.ensure_truststore(
                                cache_dir=temp_dir, force_refresh=True
                            )

    def test_ensure_truststore_keytool_failure(self):
        """Test handling of keytool failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock subprocess calls
            with patch("subprocess.run") as mock_run:
                # First call (wget) succeeds, second call (keytool) fails
                mock_run.side_effect = [
                    MagicMock(returncode=0, stdout="", stderr=""),
                    MagicMock(returncode=1, stdout="", stderr="Keytool error"),
                ]

                with patch("tempfile.NamedTemporaryFile") as mock_temp:
                    fake_cert = os.path.join(temp_dir, "cert.pem")
                    mock_temp.return_value.__enter__.return_value.name = fake_cert
                    Path(fake_cert).touch()

                    # Mock file operations
                    def mock_exists(path):
                        if "cert.pem" in path:
                            return True
                        if "mytruststore.jks" in path:
                            return False  # keytool failed to create it
                        return os.path.exists(path)

                    def mock_getsize(path):
                        if "cert.pem" in path:
                            return 100
                        return 0

                    with patch("os.path.exists", side_effect=mock_exists):
                        with patch("os.path.getsize", side_effect=mock_getsize):
                            with patch("os.unlink"):
                                with pytest.raises(RuntimeError, match="Failed to create trust store"):
                                    truststore.ensure_truststore(
                                        cache_dir=temp_dir, force_refresh=True
                                    )
