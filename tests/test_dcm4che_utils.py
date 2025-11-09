"""
Integration tests for Dcm4cheUtils with containerized dcm4che PACS server.
"""

from unittest.mock import patch

import pytest

from cfmm2tar import dcm4che_utils as dcm4che_utils_module


@pytest.mark.integration
class TestDcm4cheUtilsIntegration:
    """Integration tests for Dcm4cheUtils class using containerized PACS."""

    def test_dcm4che_connection(self, dcm4che_server):
        """Test basic connection to dcm4che PACS server."""
        connect_string = f"DCM4CHEE@{dcm4che_server['host']}:{dcm4che_server['port']}"

        # Create Dcm4cheUtils instance
        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect=connect_string,
            username=dcm4che_server["username"],
            password=dcm4che_server["password"],
            other_options="",
        )

        # Test that the object was created successfully
        assert dcm4che_utils is not None
        assert dcm4che_utils.connect == connect_string

    def test_get_all_pi_names(self, dcm4che_server):
        """Test getting all PI names (StudyDescriptions) from PACS."""
        connect_string = f"DCM4CHEE@{dcm4che_server['host']}:{dcm4che_server['port']}"

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect=connect_string,
            username=dcm4che_server["username"],
            password=dcm4che_server["password"],
            other_options="",
        )

        # This should return a list (empty or with data)
        pi_names = dcm4che_utils.get_all_pi_names()
        assert isinstance(pi_names, list)

    def test_get_study_by_matching_key(self, dcm4che_server):
        """Test querying studies with matching key."""
        connect_string = f"DCM4CHEE@{dcm4che_server['host']}:{dcm4che_server['port']}"

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect=connect_string,
            username=dcm4che_server["username"],
            password=dcm4che_server["password"],
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

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect=connect_string,
            username=dcm4che_server["username"],
            password=dcm4che_server["password"],
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

    @pytest.fixture(autouse=True)
    def mock_truststore(self):
        """Automatically mock truststore for all unit tests."""
        with patch("cfmm2tar.dcm4che_utils.truststore.get_truststore_option") as mock:
            mock.return_value = "--trust-store /path/to/truststore.jks"
            yield mock

    def test_init_with_credentials(self):
        """Test initialization with credentials."""
        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
            other_options="--tls-aes",
        )

        assert dcm4che_utils.connect == "TEST@localhost:11112"
        assert dcm4che_utils.username == "testuser"
        assert dcm4che_utils.password == "testpass"
        assert "--tls-aes" in dcm4che_utils._findscu_str
        assert "--trust-store" in dcm4che_utils._findscu_str

    def test_xml_parsing_study_uids(self):
        """Test parsing StudyInstanceUIDs from XML output."""
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">1.2.3.4.5.6.7.8.9</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        mock_root = ET.fromstring(mock_xml)

        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output", return_value=mock_root
        ):
            result = dcm4che_utils.get_StudyInstanceUID_by_matching_key("-m StudyDate='*'")
            assert len(result) == 1
            assert result[0] == "1.2.3.4.5.6.7.8.9"

    def test_xml_parsing_multiple_study_uids(self):
        """Test parsing multiple StudyInstanceUIDs from XML output."""
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response with multiple studies
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">1.2.3.4.5.6.7.8.9</Value>
  </DicomAttribute>
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">9.8.7.6.5.4.3.2.1</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        mock_root = ET.fromstring(mock_xml)

        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output", return_value=mock_root
        ):
            result = dcm4che_utils.get_StudyInstanceUID_by_matching_key("-m StudyDate='*'")
            assert len(result) == 2
            assert "1.2.3.4.5.6.7.8.9" in result
            assert "9.8.7.6.5.4.3.2.1" in result

    def test_xml_parsing_pi_names(self):
        """Test parsing PI names from StudyDescription XML output."""
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response with StudyDescriptions
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
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
        mock_root = ET.fromstring(mock_xml)

        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output", return_value=mock_root
        ):
            result = dcm4che_utils.get_all_pi_names()
            # Result should be sorted list of unique PI names as bytes
            assert len(result) == 2
            assert b"Khan" in result
            assert b"Smith" in result

    def test_xml_parsing_study_metadata(self):
        """Test parsing complete study metadata from XML output."""
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response with complete study metadata
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
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
        mock_root = ET.fromstring(mock_xml)

        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output_per_study", return_value=[mock_root]
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
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response with NumberOfStudyRelatedInstances
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="00201208" vr="IS">
    <Value number="1">100</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        mock_root = ET.fromstring(mock_xml)

        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output", return_value=mock_root
        ):
            result = dcm4che_utils._get_NumberOfStudyRelatedInstances("-m StudyDate='*'")
            assert result == "100"

    def test_xml_parsing_empty_response(self):
        """Test handling of empty XML response."""
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock empty XML response
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
</NativeDicomModel>
"""
        mock_root = ET.fromstring(mock_xml)

        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output", return_value=mock_root
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

    def test_xml_parsing_zero_study_metadata(self):
        """Test parsing study metadata with zero matching studies."""
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock empty list for no studies
        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output_per_study", return_value=[]
        ):
            result = dcm4che_utils.get_study_metadata_by_matching_key("-m StudyDate='*'")
            assert len(result) == 0

    def test_xml_parsing_one_study_metadata(self):
        """Test parsing study metadata with exactly one matching study."""
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">1.1.1.1.1</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100010" vr="PN">
    <Value number="1">Patient^One</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100020" vr="LO">
    <Value number="1">ID001</Value>
  </DicomAttribute>
  <DicomAttribute tag="00080020" vr="DA">
    <Value number="1">20240101</Value>
  </DicomAttribute>
  <DicomAttribute tag="00081030" vr="LO">
    <Value number="1">Khan^Project1</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        mock_root = ET.fromstring(mock_xml)

        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output_per_study", return_value=[mock_root]
        ):
            result = dcm4che_utils.get_study_metadata_by_matching_key("-m StudyDate='*'")
            assert len(result) == 1
            study = result[0]
            assert study["StudyInstanceUID"] == "1.1.1.1.1"
            assert study["PatientName"] == "Patient^One"
            assert study["PatientID"] == "ID001"
            assert study["StudyDate"] == "20240101"
            assert study["StudyDescription"] == "Khan^Project1"

    def test_xml_parsing_two_study_metadata(self):
        """Test parsing study metadata with exactly two matching studies."""
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response with two studies - each as a separate root
        study1_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">1.1.1.1.1</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100010" vr="PN">
    <Value number="1">Patient^One</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100020" vr="LO">
    <Value number="1">ID001</Value>
  </DicomAttribute>
  <DicomAttribute tag="00080020" vr="DA">
    <Value number="1">20240101</Value>
  </DicomAttribute>
  <DicomAttribute tag="00081030" vr="LO">
    <Value number="1">Khan^Project1</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        study2_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">2.2.2.2.2</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100010" vr="PN">
    <Value number="1">Patient^Two</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100020" vr="LO">
    <Value number="1">ID002</Value>
  </DicomAttribute>
  <DicomAttribute tag="00080020" vr="DA">
    <Value number="1">20240102</Value>
  </DicomAttribute>
  <DicomAttribute tag="00081030" vr="LO">
    <Value number="1">Khan^Project2</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        mock_roots = [ET.fromstring(study1_xml), ET.fromstring(study2_xml)]

        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output_per_study", return_value=mock_roots
        ):
            result = dcm4che_utils.get_study_metadata_by_matching_key("-m StudyDate='*'")
            assert len(result) == 2

            # Check first study
            assert result[0]["StudyInstanceUID"] == "1.1.1.1.1"
            assert result[0]["PatientName"] == "Patient^One"
            assert result[0]["PatientID"] == "ID001"
            assert result[0]["StudyDate"] == "20240101"
            assert result[0]["StudyDescription"] == "Khan^Project1"

            # Check second study
            assert result[1]["StudyInstanceUID"] == "2.2.2.2.2"
            assert result[1]["PatientName"] == "Patient^Two"
            assert result[1]["PatientID"] == "ID002"
            assert result[1]["StudyDate"] == "20240102"
            assert result[1]["StudyDescription"] == "Khan^Project2"

    def test_xml_parsing_three_study_metadata(self):
        """Test parsing study metadata with exactly three matching studies."""
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response with three studies - each as a separate root
        study1_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">1.1.1.1.1</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100010" vr="PN">
    <Value number="1">Patient^One</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        study2_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">2.2.2.2.2</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100010" vr="PN">
    <Value number="1">Patient^Two</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        study3_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">3.3.3.3.3</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100010" vr="PN">
    <Value number="1">Patient^Three</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        mock_roots = [
            ET.fromstring(study1_xml),
            ET.fromstring(study2_xml),
            ET.fromstring(study3_xml),
        ]

        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output_per_study", return_value=mock_roots
        ):
            result = dcm4che_utils.get_study_metadata_by_matching_key("-m StudyDate='*'")
            assert len(result) == 3

            # Check all three studies
            assert result[0]["StudyInstanceUID"] == "1.1.1.1.1"
            assert result[0]["PatientName"] == "Patient^One"
            assert result[1]["StudyInstanceUID"] == "2.2.2.2.2"
            assert result[1]["PatientName"] == "Patient^Two"
            assert result[2]["StudyInstanceUID"] == "3.3.3.3.3"
            assert result[2]["PatientName"] == "Patient^Three"

    def test_metadata_tsv_output(self):
        """Test that metadata can be written to TSV and all fields are preserved."""
        import csv
        import io
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Create mock data for 3 studies to test the reported bug
        study1_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">1.1.1.1.1</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100010" vr="PN">
    <Value number="1">Patient^One</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100020" vr="LO">
    <Value number="1">ID001</Value>
  </DicomAttribute>
  <DicomAttribute tag="00080020" vr="DA">
    <Value number="1">20240101</Value>
  </DicomAttribute>
  <DicomAttribute tag="00081030" vr="LO">
    <Value number="1">Khan^Project1</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        study2_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">2.2.2.2.2</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100010" vr="PN">
    <Value number="1">Patient^Two</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100020" vr="LO">
    <Value number="1">ID002</Value>
  </DicomAttribute>
  <DicomAttribute tag="00080020" vr="DA">
    <Value number="1">20240102</Value>
  </DicomAttribute>
  <DicomAttribute tag="00081030" vr="LO">
    <Value number="1">Khan^Project2</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        study3_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">3.3.3.3.3</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100010" vr="PN">
    <Value number="1">Patient^Three</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100020" vr="LO">
    <Value number="1">ID003</Value>
  </DicomAttribute>
  <DicomAttribute tag="00080020" vr="DA">
    <Value number="1">20240103</Value>
  </DicomAttribute>
  <DicomAttribute tag="00081030" vr="LO">
    <Value number="1">Khan^Project3</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        mock_roots = [
            ET.fromstring(study1_xml),
            ET.fromstring(study2_xml),
            ET.fromstring(study3_xml),
        ]

        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output_per_study", return_value=mock_roots
        ):
            studies = dcm4che_utils.get_study_metadata_by_matching_key("-m StudyDate='*'")

            # Write to TSV (simulating what cli.py does)
            output = io.StringIO()
            fieldnames = [
                "StudyInstanceUID",
                "PatientName",
                "PatientID",
                "StudyDate",
                "StudyDescription",
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            for study in studies:
                writer.writerow(study)

            # Read back the TSV and validate all fields are present
            output.seek(0)
            reader = csv.DictReader(output, delimiter="\t")
            rows = list(reader)

            # Verify we have 3 rows
            assert len(rows) == 3, f"Expected 3 rows, got {len(rows)}"

            # Verify each row has all fields populated (not empty)
            for i, row in enumerate(rows):
                row_num = i + 1
                assert row["StudyInstanceUID"], f"Row {row_num}: StudyInstanceUID is empty"
                assert row["PatientName"], f"Row {row_num}: PatientName is empty"
                assert row["PatientID"], f"Row {row_num}: PatientID is empty"
                assert row["StudyDate"], f"Row {row_num}: StudyDate is empty"
                assert row["StudyDescription"], f"Row {row_num}: StudyDescription is empty"

            # Verify specific values for each row
            assert rows[0]["StudyInstanceUID"] == "1.1.1.1.1"
            assert rows[0]["PatientName"] == "Patient^One"
            assert rows[0]["PatientID"] == "ID001"

            assert rows[1]["StudyInstanceUID"] == "2.2.2.2.2"
            assert rows[1]["PatientName"] == "Patient^Two"
            assert rows[1]["PatientID"] == "ID002"

            assert rows[2]["StudyInstanceUID"] == "3.3.3.3.3"
            assert rows[2]["PatientName"] == "Patient^Three"
            assert rows[2]["PatientID"] == "ID003"

    def test_additional_tags_single_tag(self):
        """Test querying metadata with a single additional DICOM tag."""
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response with default tags and PatientBirthDate (00100030)
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">1.2.3.4.5.6.7.8.9</Value>
  </DicomAttribute>
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
  <DicomAttribute tag="00100030" vr="DA">
    <Value number="1">19900515</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        mock_root = ET.fromstring(mock_xml)

        # Query with additional tag
        additional_tags = {"00100030": "PatientBirthDate"}
        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output_per_study", return_value=[mock_root]
        ):
            result = dcm4che_utils.get_study_metadata_by_matching_key(
                "-m StudyDate='*'", additional_tags
            )
            assert len(result) == 1
            study = result[0]
            # Check default fields
            assert study["StudyInstanceUID"] == "1.2.3.4.5.6.7.8.9"
            assert study["PatientName"] == "Test^Patient"
            assert study["PatientID"] == "TEST001"
            assert study["StudyDate"] == "20240101"
            assert study["StudyDescription"] == "Khan^TestProject"
            # Check additional field
            assert study["PatientBirthDate"] == "19900515"

    def test_additional_tags_multiple_tags(self):
        """Test querying metadata with multiple additional DICOM tags."""
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response with default tags plus PatientBirthDate and PatientSex
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">1.2.3.4.5.6.7.8.9</Value>
  </DicomAttribute>
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
  <DicomAttribute tag="00100030" vr="DA">
    <Value number="1">19900515</Value>
  </DicomAttribute>
  <DicomAttribute tag="00100040" vr="CS">
    <Value number="1">M</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        mock_root = ET.fromstring(mock_xml)

        # Query with multiple additional tags
        additional_tags = {"00100030": "PatientBirthDate", "00100040": "PatientSex"}
        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output_per_study", return_value=[mock_root]
        ):
            result = dcm4che_utils.get_study_metadata_by_matching_key(
                "-m StudyDate='*'", additional_tags
            )
            assert len(result) == 1
            study = result[0]
            # Check default fields
            assert study["StudyInstanceUID"] == "1.2.3.4.5.6.7.8.9"
            assert study["PatientName"] == "Test^Patient"
            # Check additional fields
            assert study["PatientBirthDate"] == "19900515"
            assert study["PatientSex"] == "M"

    def test_additional_tags_missing_tag(self):
        """Test that missing additional tags are filled with empty strings."""
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response without the additional tag PatientBirthDate
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">1.2.3.4.5.6.7.8.9</Value>
  </DicomAttribute>
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
</NativeDicomModel>
"""
        mock_root = ET.fromstring(mock_xml)

        # Query with additional tag that's not in the XML
        additional_tags = {"00100030": "PatientBirthDate"}
        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output_per_study", return_value=[mock_root]
        ):
            result = dcm4che_utils.get_study_metadata_by_matching_key(
                "-m StudyDate='*'", additional_tags
            )
            assert len(result) == 1
            study = result[0]
            # Check that the missing additional field is set to empty string
            assert "PatientBirthDate" in study
            assert study["PatientBirthDate"] == ""

    def test_additional_tags_case_normalization(self):
        """Test that additional tags are normalized to uppercase."""
        import xml.etree.ElementTree as ET
        from unittest.mock import patch

        dcm4che_utils = dcm4che_utils_module.Dcm4cheUtils(
            connect="TEST@localhost:11112",
            username="testuser",
            password="testpass",
        )

        # Mock XML response with PatientBirthDate
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NativeDicomModel xml:space="preserve">
  <DicomAttribute tag="0020000D" vr="UI">
    <Value number="1">1.2.3.4.5.6.7.8.9</Value>
  </DicomAttribute>
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
  <DicomAttribute tag="00100030" vr="DA">
    <Value number="1">19900515</Value>
  </DicomAttribute>
</NativeDicomModel>
"""
        mock_root = ET.fromstring(mock_xml)

        # Query with lowercase and mixed-case tags - they should be normalized
        additional_tags = {"0010 0030": "PatientBirthDate"}  # With spaces
        with patch.object(
            dcm4che_utils, "_execute_findscu_with_xml_output_per_study", return_value=[mock_root]
        ):
            result = dcm4che_utils.get_study_metadata_by_matching_key(
                "-m StudyDate='*'", additional_tags
            )
            assert len(result) == 1
            study = result[0]
            # Check that the additional field was extracted correctly
            assert study["PatientBirthDate"] == "19900515"
