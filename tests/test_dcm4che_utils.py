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

    def test_xml_parsing_study_uids(self):
        """Test parsing StudyInstanceUIDs from XML output."""
        from unittest.mock import Mock, patch

        dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response
        mock_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">1.2.3.4.5.6.7.8.9</Value>
  </DicomAttribute>
</NativeDicomModel>
"""

        with patch.object(
            dcm4che_utils, "_get_stdout_stderr_returncode", return_value=(mock_xml, b"", 0)
        ):
            result = dcm4che_utils.get_StudyInstanceUID_by_matching_key("-m StudyDate='*'")
            assert len(result) == 1
            assert result[0] == "1.2.3.4.5.6.7.8.9"

    def test_xml_parsing_multiple_study_uids(self):
        """Test parsing multiple StudyInstanceUIDs from XML output."""
        from unittest.mock import Mock, patch

        dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response with multiple studies
        mock_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">1.2.3.4.5.6.7.8.9</Value>
  </DicomAttribute>
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">9.8.7.6.5.4.3.2.1</Value>
  </DicomAttribute>
</NativeDicomModel>
"""

        with patch.object(
            dcm4che_utils, "_get_stdout_stderr_returncode", return_value=(mock_xml, b"", 0)
        ):
            result = dcm4che_utils.get_StudyInstanceUID_by_matching_key("-m StudyDate='*'")
            assert len(result) == 2
            assert "1.2.3.4.5.6.7.8.9" in result
            assert "9.8.7.6.5.4.3.2.1" in result

    def test_xml_parsing_pi_names(self):
        """Test parsing PI names from StudyDescription XML output."""
        from unittest.mock import Mock, patch

        dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response with StudyDescriptions
        mock_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="00081030" vr="LO">
    <Value number="1">Khan^Project1</Value>
  </DicomAttribute>
  <DicomAttribute tag="00081030" vr="LO">
    <Value number="1">Khan^Project2</Value>
  </DicomAttribute>
  <DicomAttribute tag="00081030" vr="LO">
    <Value number="1">Smith^ProjectA</Value>
  </DicomAttribute>
</NativeDicomModel>
"""

        with patch.object(
            dcm4che_utils, "_get_stdout_stderr_returncode", return_value=(mock_xml, b"", 0)
        ):
            result = dcm4che_utils.get_all_pi_names()
            # Result should be sorted list of unique PI names as bytes
            assert len(result) == 2
            assert b"Khan" in result
            assert b"Smith" in result

    def test_xml_parsing_study_metadata(self):
        """Test parsing complete study metadata from XML output."""
        from unittest.mock import Mock, patch

        dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response with complete study metadata
        mock_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="00100010" vr="PN">
    <Value number="1">Test^Patient</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100020" vr="LO">
    <Value number="1">TEST001</Value>
  </DicomAttribute>
  <DicomAttribute tag="00080020" vr="DA">
    <Value number="1">20240101</Value>
  </DicomAttribute>
  <DicomAttribute tag="00081030" vr="LO">
    <Value number="1">Khan^TestProject</Value>
  </DicomAttribute>
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">1.2.3.4.5.6.7.8.9</Value>
  </DicomAttribute>
</NativeDicomModel>
"""

        with patch.object(
            dcm4che_utils, "_get_stdout_stderr_returncode", return_value=(mock_xml, b"", 0)
        ):
            result = dcm4che_utils.get_study_metadata_by_matching_key("-m StudyDate='*'")
            assert len(result) == 1
            study = result[0]
            assert study["StudyInstanceUID"] == "1.2.3.4.5.6.7.8.9"
            assert study["PatientName"] == "Test^Patient"
            assert study["PatientID"] == "TEST001"
            assert study["StudyDate"] == "20240101"
            assert study["StudyDescription"] == "Khan^TestProject"

    def test_xml_parsing_number_of_instances(self):
        """Test parsing NumberOfStudyRelatedInstances from XML output."""
        from unittest.mock import Mock, patch

        dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response with NumberOfStudyRelatedInstances
        mock_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="00201208" vr="IS">
    <Value number="1">100</Value>
  </DicomAttribute>
</NativeDicomModel>
"""

        with patch.object(
            dcm4che_utils, "_get_stdout_stderr_returncode", return_value=(mock_xml, b"", 0)
        ):
            result = dcm4che_utils._get_NumberOfStudyRelatedInstances("-m StudyDate='*'")
            assert result == "100"

    def test_xml_parsing_empty_response(self):
        """Test handling of empty XML response."""
        from unittest.mock import Mock, patch

        dcm4che_utils = Dcm4cheUtils.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock empty XML response
        mock_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
</NativeDicomModel>
"""

        with patch.object(
            dcm4che_utils, "_get_stdout_stderr_returncode", return_value=(mock_xml, b"", 0)
        ):
            # Test with empty results for each method
            uids = dcm4che_utils.get_StudyInstanceUID_by_matching_key("-m StudyDate='*'")
            assert len(uids) == 0

            pi_names = dcm4che_utils.get_all_pi_names()
            assert len(pi_names) == 0

            metadata = dcm4che_utils.get_study_metadata_by_matching_key("-m StudyDate='*'")
            assert len(metadata) == 0

            instances = dcm4che_utils._get_NumberOfStudyRelatedInstances("-m StudyDate='*'")
            assert instances == ""

