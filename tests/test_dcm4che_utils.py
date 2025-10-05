"""
Integration tests for Dcm4cheUtils with containerized dcm4che PACS server.
"""

import pytest

from cfmm2tar import Dcm4cheUtils


@pytest.mark.integration
class TestDcm4cheUtilsIntegration:
    """Integration tests for Dcm4cheUtils class using containerized PACS."""

    def test_dcm4che_connection(self, dcm4che_server):
        """Test basic connection to dcm4che PACS server."""
        connect_string = f"DCM4CHEE@{dcm4che_server['host']}:{dcm4che_server['port']}"

        # Create Dcm4cheUtils instance
        dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
            connect=connect_string,
            username=dcm4che_server["username"],
            password=dcm4che_server["password"],
            dcm4che_path="",  # Use local dcm4che tools
            other_options="",
        )

        # Test that the object was created successfully
        assert dcm4che_utils is not None
        assert dcm4che_utils.connect == connect_string

    def test_get_all_pi_names(self, dcm4che_server):
        """Test getting all PI names (StudyDescriptions) from PACS."""
        connect_string = f"DCM4CHEE@{dcm4che_server['host']}:{dcm4che_server['port']}"

        dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
            connect=connect_string,
            username=dcm4che_server["username"],
            password=dcm4che_server["password"],
            dcm4che_path="",
            other_options="",
        )

        # This should return a list (empty or with data)
        pi_names = dcm4che_utils.get_all_pi_names()
        assert isinstance(pi_names, list)

    def test_get_study_by_matching_key(self, dcm4che_server):
        """Test querying studies with matching key."""
        connect_string = f"DCM4CHEE@{dcm4che_server['host']}:{dcm4che_server['port']}"

        dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
            connect=connect_string,
            username=dcm4che_server["username"],
            password=dcm4che_server["password"],
            dcm4che_path="",
            other_options="",
        )

        # Query for any studies (empty PACS should return empty list)
        matching_key = "-m StudyDescription='*' -m StudyDate='*'"
        study_uids = dcm4che_utils.get_StudyInstanceUID_by_matching_key(matching_key)

        # Should return a list (empty or with UIDs)
        assert isinstance(study_uids, list)

    def test_get_study_metadata(self, dcm4che_server):
        """Test getting study metadata."""
        connect_string = f"DCM4CHEE@{dcm4che_server['host']}:{dcm4che_server['port']}"

        dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
            connect=connect_string,
            username=dcm4che_server["username"],
            password=dcm4che_server["password"],
            dcm4che_path="",
            other_options="",
        )

        # Query for study metadata
        matching_key = "-m StudyDescription='*' -m StudyDate='*'"
        metadata = dcm4che_utils.get_study_metadata_by_matching_key(matching_key)

        # Should return a list of dictionaries
        assert isinstance(metadata, list)

        # If there are studies, check structure
        for study in metadata:
            assert isinstance(study, dict)
            # All studies should have these keys (may be empty strings)
            assert "StudyInstanceUID" in study
            assert "PatientName" in study
            assert "PatientID" in study
            assert "StudyDate" in study
            assert "StudyDescription" in study


@pytest.mark.unit
class TestDcm4cheUtilsUnit:
    """Unit tests for Dcm4cheUtils class that don't require a PACS server."""

    def test_init_with_credentials(self):
        """Test initialization with credentials."""
        dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
            dcm4che_path="",
            other_options="--tls-aes",
        )

        assert dcm4che_utils.connect == "TEST@localhost:11112"
        assert dcm4che_utils.username == "testuser"
        assert dcm4che_utils.password == "testpass"
        assert "--tls-aes" in dcm4che_utils._findscu_str

    def test_init_with_docker_path(self):
        """Test initialization with docker container path."""
        dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
            dcm4che_path="docker run --rm dcm4che/dcm4che-tools:5.24.1",
            other_options="",
        )

        assert "docker run --rm dcm4che/dcm4che-tools:5.24.1" in dcm4che_utils._findscu_str
        assert "docker run --rm dcm4che/dcm4che-tools:5.24.1" in dcm4che_utils._getscu_str
