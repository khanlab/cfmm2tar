#!/usr/bin/env python3
"""
Tests for the cfmm2tar Python API module.

These are unit tests that mock the underlying dcm4che functionality.
"""

import os
import tempfile
from unittest.mock import Mock, mock_open, patch

import pytest

from cfmm2tar import api


@pytest.fixture
def mock_credentials():
    """Fixture for test credentials."""
    return {"username": "test_user", "password": "test_pass"}


@pytest.fixture
def sample_study_metadata():
    """Fixture for sample study metadata."""
    return [
        {
            "StudyInstanceUID": "1.2.840.113619.2.55.3.1234567890.123",
            "PatientName": "Test^Patient1",
            "PatientID": "12345",
            "StudyDate": "20240101",
            "StudyDescription": "Khan^NeuroAnalytics",
        },
        {
            "StudyInstanceUID": "1.2.840.113619.2.55.3.9876543210.456",
            "PatientName": "Test^Patient2",
            "PatientID": "67890",
            "StudyDate": "20240102",
            "StudyDescription": "Khan^Project2",
        },
    ]


class TestGetCredentials:
    """Tests for _get_credentials helper function."""

    def test_provided_credentials(self):
        """Test that provided credentials take precedence."""
        username, password = api._get_credentials("user1", "pass1")
        assert username == "user1"
        assert password == "pass1"

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="file_user\nfile_pass\n")
    def test_credentials_from_file(self, mock_file, mock_exists):
        """Test reading credentials from ~/.uwo_credentials."""
        mock_exists.return_value = True
        username, password = api._get_credentials()
        assert username == "file_user"
        assert password == "file_pass"

    @patch("os.path.exists")
    @patch.dict(os.environ, {"UWO_USERNAME": "env_user", "UWO_PASSWORD": "env_pass"})
    def test_credentials_from_env(self, mock_exists):
        """Test reading credentials from environment variables."""
        mock_exists.return_value = False
        username, password = api._get_credentials()
        assert username == "env_user"
        assert password == "env_pass"

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="file_user\nfile_pass\n")
    def test_partial_override_username(self, mock_file, mock_exists):
        """Test that provided username overrides file username."""
        mock_exists.return_value = True
        username, password = api._get_credentials(username="override_user")
        assert username == "override_user"
        assert password == "file_pass"

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data="file_user\nfile_pass\n")
    def test_partial_override_password(self, mock_file, mock_exists):
        """Test that provided password overrides file password."""
        mock_exists.return_value = True
        username, password = api._get_credentials(password="override_pass")
        assert username == "file_user"
        assert password == "override_pass"

    @patch("os.path.exists")
    @patch.dict(os.environ, {}, clear=True)
    def test_no_credentials_raises_error(self, mock_exists):
        """Test that missing credentials raise ValueError."""
        mock_exists.return_value = False
        with pytest.raises(ValueError, match="Credentials not found"):
            api._get_credentials()


class TestQueryMetadata:
    """Tests for query_metadata function."""

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.dcm4che_utils.Dcm4cheUtils")
    def test_query_metadata_list_return(
        self, mock_dcm4che, mock_get_creds, mock_credentials, sample_study_metadata
    ):
        """Test query_metadata with list return type."""
        # Setup mocks
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        mock_instance = Mock()
        mock_instance.get_study_metadata_by_matching_key.return_value = sample_study_metadata
        mock_dcm4che.return_value = mock_instance

        # Call function
        result = api.query_metadata(
            username=mock_credentials["username"],
            password=mock_credentials["password"],
            study_description="Khan^*",
            study_date="20240101-20240131",
            return_type="list",
        )

        # Assertions
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["StudyInstanceUID"] == "1.2.840.113619.2.55.3.1234567890.123"
        assert result[1]["PatientName"] == "Test^Patient2"

        # Verify mock was called correctly
        mock_dcm4che.assert_called_once()
        mock_instance.get_study_metadata_by_matching_key.assert_called_once()

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.dcm4che_utils.Dcm4cheUtils")
    def test_query_metadata_dataframe_return(
        self, mock_dcm4che, mock_get_creds, mock_credentials, sample_study_metadata
    ):
        """Test query_metadata with dataframe return type."""
        # Check if pandas is available
        pytest.importorskip("pandas")
        import pandas as pd

        # Setup mocks
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        mock_instance = Mock()
        mock_instance.get_study_metadata_by_matching_key.return_value = sample_study_metadata
        mock_dcm4che.return_value = mock_instance

        # Call function
        result = api.query_metadata(
            username=mock_credentials["username"],
            password=mock_credentials["password"],
            study_description="Khan^*",
            return_type="dataframe",
        )

        # Assertions
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert "StudyInstanceUID" in result.columns
        assert result.iloc[0]["PatientName"] == "Test^Patient1"

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.dcm4che_utils.Dcm4cheUtils")
    def test_query_metadata_invalid_return_type(
        self, mock_dcm4che, mock_get_creds, mock_credentials
    ):
        """Test query_metadata with invalid return type."""
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        with pytest.raises(ValueError, match="return_type must be 'list' or 'dataframe'"):
            api.query_metadata(
                username=mock_credentials["username"],
                password=mock_credentials["password"],
                return_type="invalid",
            )

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.dcm4che_utils.Dcm4cheUtils")
    def test_query_metadata_no_pandas(self, mock_dcm4che, mock_get_creds, mock_credentials):
        """Test query_metadata requesting dataframe when pandas not available."""
        # Setup mocks
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        mock_instance = Mock()
        mock_dcm4che.return_value = mock_instance

        # Mock pandas import failure
        with patch.dict("sys.modules", {"pandas": None}):
            with pytest.raises(ImportError, match="pandas is required"):
                api.query_metadata(
                    username=mock_credentials["username"],
                    password=mock_credentials["password"],
                    return_type="dataframe",
                )

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.dcm4che_utils.Dcm4cheUtils")
    def test_query_metadata_default_parameters(
        self, mock_dcm4che, mock_get_creds, mock_credentials, sample_study_metadata
    ):
        """Test query_metadata with default parameters."""
        # Setup mocks
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        mock_instance = Mock()
        mock_instance.get_study_metadata_by_matching_key.return_value = sample_study_metadata
        mock_dcm4che.return_value = mock_instance

        # Call function with minimal parameters
        api.query_metadata(
            username=mock_credentials["username"],
            password=mock_credentials["password"],
        )

        # Verify default matching key was constructed correctly
        call_args = mock_instance.get_study_metadata_by_matching_key.call_args[0][0]
        assert "-m StudyDescription='*'" in call_args
        assert "-m StudyDate='-'" in call_args
        assert "-m PatientName='*'" in call_args


class TestDownloadStudies:
    """Tests for download_studies function."""

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.retrieve_cfmm_tar.main")
    def test_download_studies_basic(self, mock_retrieve, mock_get_creds, mock_credentials):
        """Test download_studies with basic parameters."""
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")

            # Call function
            result = api.download_studies(
                output_dir=output_dir,
                username=mock_credentials["username"],
                password=mock_credentials["password"],
                study_description="Khan^Test",
                study_date="20240101",
            )

            # Assertions
            assert result == output_dir
            assert os.path.exists(output_dir)
            mock_retrieve.assert_called_once()

            # Check that the call had correct parameters
            call_kwargs = mock_retrieve.call_args[1]
            assert call_kwargs["uwo_username"] == mock_credentials["username"]
            assert call_kwargs["PI_matching_key"] == "Khan^Test"
            assert call_kwargs["study_date"] == "20240101"

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.retrieve_cfmm_tar.main")
    def test_download_studies_with_uid(self, mock_retrieve, mock_get_creds, mock_credentials):
        """Test download_studies with specific StudyInstanceUID."""
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")
            test_uid = "1.2.840.113619.2.55.3.1234567890.123"

            # Call function
            api.download_studies(
                output_dir=output_dir,
                username=mock_credentials["username"],
                password=mock_credentials["password"],
                study_instance_uid=test_uid,
            )

            # Check that UID was passed correctly
            call_kwargs = mock_retrieve.call_args[1]
            assert call_kwargs["study_instance_uid"] == test_uid

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.retrieve_cfmm_tar.main")
    def test_download_studies_with_temp_dir(self, mock_retrieve, mock_get_creds, mock_credentials):
        """Test download_studies with custom temp directory."""
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")
            temp_dir = os.path.join(tmpdir, "temp")

            # Call function
            api.download_studies(
                output_dir=output_dir,
                username=mock_credentials["username"],
                password=mock_credentials["password"],
                temp_dir=temp_dir,
            )

            # Check that temp_dir was used
            call_kwargs = mock_retrieve.call_args[1]
            assert call_kwargs["retrieve_dest_dir"] == temp_dir
            assert os.path.exists(temp_dir)

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.retrieve_cfmm_tar.main")
    def test_download_studies_with_multiple_uids(
        self, mock_retrieve, mock_get_creds, mock_credentials
    ):
        """Test download_studies with multiple StudyInstanceUIDs."""
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")
            test_uids = [
                "1.2.840.113619.2.55.3.1234567890.123",
                "1.2.840.113619.2.55.3.9876543210.456",
                "1.2.840.113619.2.55.3.1111111111.789",
            ]

            # Call function with list of UIDs
            api.download_studies(
                output_dir=output_dir,
                username=mock_credentials["username"],
                password=mock_credentials["password"],
                study_instance_uid=test_uids,
            )

            # Should be called once for each UID
            assert mock_retrieve.call_count == 3

            # Check that each UID was passed correctly
            calls = mock_retrieve.call_args_list
            assert calls[0][1]["study_instance_uid"] == test_uids[0]
            assert calls[1][1]["study_instance_uid"] == test_uids[1]
            assert calls[2][1]["study_instance_uid"] == test_uids[2]

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.retrieve_cfmm_tar.main")
    def test_download_studies_with_two_uids(self, mock_retrieve, mock_get_creds, mock_credentials):
        """Test download_studies with exactly two StudyInstanceUIDs."""
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")
            test_uids = [
                "1.2.840.113619.2.55.3.1234567890.123",
                "1.2.840.113619.2.55.3.9876543210.456",
            ]

            # Call function with list of UIDs
            result = api.download_studies(
                output_dir=output_dir,
                username=mock_credentials["username"],
                password=mock_credentials["password"],
                study_instance_uid=test_uids,
            )

            # Should return output_dir
            assert result == output_dir

            # Should be called once for each UID
            assert mock_retrieve.call_count == 2

            # Check that UIDs were passed correctly
            calls = mock_retrieve.call_args_list
            assert calls[0][1]["study_instance_uid"] == test_uids[0]
            assert calls[1][1]["study_instance_uid"] == test_uids[1]

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.retrieve_cfmm_tar.main")
    def test_download_studies_empty_uid_list(self, mock_retrieve, mock_get_creds, mock_credentials):
        """Test download_studies with empty list of UIDs."""
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")

            # Call function with empty list
            api.download_studies(
                output_dir=output_dir,
                username=mock_credentials["username"],
                password=mock_credentials["password"],
                study_instance_uid=[],
            )

            # Should not be called for empty list
            assert mock_retrieve.call_count == 0


class TestDownloadStudiesFromMetadata:
    """Tests for download_studies_from_metadata function."""

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.retrieve_cfmm_tar.main")
    def test_download_from_metadata_list(
        self, mock_retrieve, mock_get_creds, mock_credentials, sample_study_metadata
    ):
        """Test download_studies_from_metadata with list of dicts."""
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")

            # Call function
            result = api.download_studies_from_metadata(
                output_dir=output_dir,
                metadata=sample_study_metadata,
                username=mock_credentials["username"],
                password=mock_credentials["password"],
            )

            # Assertions
            assert result == output_dir
            assert mock_retrieve.call_count == 2  # Two studies

            # Check that UIDs were used correctly
            calls = mock_retrieve.call_args_list
            assert calls[0][1]["study_instance_uid"] == "1.2.840.113619.2.55.3.1234567890.123"
            assert calls[1][1]["study_instance_uid"] == "1.2.840.113619.2.55.3.9876543210.456"

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.retrieve_cfmm_tar.main")
    def test_download_from_metadata_file(self, mock_retrieve, mock_get_creds, mock_credentials):
        """Test download_studies_from_metadata with TSV file."""
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")
            metadata_file = os.path.join(tmpdir, "metadata.tsv")

            # Create TSV file
            with open(metadata_file, "w") as f:
                f.write("StudyInstanceUID\tPatientName\n")
                f.write("1.2.3.4\tPatient1\n")
                f.write("5.6.7.8\tPatient2\n")

            # Call function
            api.download_studies_from_metadata(
                output_dir=output_dir,
                metadata=metadata_file,
                username=mock_credentials["username"],
                password=mock_credentials["password"],
            )

            # Assertions
            assert mock_retrieve.call_count == 2
            calls = mock_retrieve.call_args_list
            assert calls[0][1]["study_instance_uid"] == "1.2.3.4"
            assert calls[1][1]["study_instance_uid"] == "5.6.7.8"

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.retrieve_cfmm_tar.main")
    def test_download_from_metadata_dataframe(
        self, mock_retrieve, mock_get_creds, mock_credentials
    ):
        """Test download_studies_from_metadata with DataFrame."""
        pytest.importorskip("pandas")
        import pandas as pd

        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")

            # Create DataFrame
            df = pd.DataFrame(
                {
                    "StudyInstanceUID": ["1.2.3.4", "5.6.7.8"],
                    "PatientName": ["Patient1", "Patient2"],
                }
            )

            # Call function
            api.download_studies_from_metadata(
                output_dir=output_dir,
                metadata=df,
                username=mock_credentials["username"],
                password=mock_credentials["password"],
            )

            # Assertions
            assert mock_retrieve.call_count == 2

    @patch("cfmm2tar.api._get_credentials")
    def test_download_from_metadata_invalid_list(self, mock_get_creds, mock_credentials):
        """Test download_studies_from_metadata with invalid list."""
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")

            # List without StudyInstanceUID keys
            invalid_metadata = [{"PatientName": "Test"}, {"PatientName": "Test2"}]

            with pytest.raises(ValueError, match="must be a dict with 'StudyInstanceUID' key"):
                api.download_studies_from_metadata(
                    output_dir=output_dir,
                    metadata=invalid_metadata,
                    username=mock_credentials["username"],
                    password=mock_credentials["password"],
                )

    @patch("cfmm2tar.api._get_credentials")
    def test_download_from_metadata_no_uids(self, mock_get_creds, mock_credentials):
        """Test download_studies_from_metadata with no UIDs."""
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")

            # Empty list
            with pytest.raises(ValueError, match="No StudyInstanceUIDs found"):
                api.download_studies_from_metadata(
                    output_dir=output_dir,
                    metadata=[],
                    username=mock_credentials["username"],
                    password=mock_credentials["password"],
                )

    @patch("cfmm2tar.api._get_credentials")
    def test_download_from_metadata_invalid_type(self, mock_get_creds, mock_credentials):
        """Test download_studies_from_metadata with invalid type."""
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")

            with pytest.raises(ValueError, match="must be a file path"):
                api.download_studies_from_metadata(
                    output_dir=output_dir,
                    metadata=12345,  # Invalid type
                    username=mock_credentials["username"],
                    password=mock_credentials["password"],
                )


class TestAPIIntegration:
    """Integration-style tests for the API (still mocked)."""

    @patch("cfmm2tar.api._get_credentials")
    @patch("cfmm2tar.api.dcm4che_utils.Dcm4cheUtils")
    @patch("cfmm2tar.api.retrieve_cfmm_tar.main")
    def test_query_then_download_workflow(
        self, mock_retrieve, mock_dcm4che, mock_get_creds, mock_credentials, sample_study_metadata
    ):
        """Test the typical workflow: query metadata, then download."""
        # Setup mocks
        mock_get_creds.return_value = (
            mock_credentials["username"],
            mock_credentials["password"],
        )
        mock_instance = Mock()
        mock_instance.get_study_metadata_by_matching_key.return_value = sample_study_metadata
        mock_dcm4che.return_value = mock_instance

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, "output")

            # Step 1: Query metadata
            studies = api.query_metadata(
                username=mock_credentials["username"],
                password=mock_credentials["password"],
                study_description="Khan^*",
                study_date="20240101-20240131",
            )

            assert len(studies) == 2

            # Step 2: Download using metadata
            api.download_studies_from_metadata(
                output_dir=output_dir,
                metadata=studies,
                username=mock_credentials["username"],
                password=mock_credentials["password"],
            )

            # Verify downloads were called
            assert mock_retrieve.call_count == 2
