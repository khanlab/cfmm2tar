#!/usr/bin/env python3
"""
Tests for skip_derived functionality in DicomSorter.

These are unit tests that verify the skip_derived filtering works correctly.
"""

import datetime
import os

try:
    import pytest

    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

    # Create dummy decorators if pytest not available
    class DummyMarker:
        def __call__(self, *args, **kwargs):
            if callable(args[0]):
                # Being used as decorator directly
                return args[0]

            # Being called with arguments, return decorator
            def decorator(func):
                return func

            return decorator

        def __getattr__(self, name):
            return DummyMarker()

    class pytest:
        mark = DummyMarker()

        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(func):
                return func

            return decorator

        @staticmethod
        def skipif(*args, **kwargs):
            def decorator(func):
                return func

            return decorator


try:
    from pydicom.dataset import Dataset, FileDataset
    from pydicom.uid import ImplicitVRLittleEndian, generate_uid

    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False

from cfmm2tar import dicom_sorter, sort_rules


def create_test_dicom(output_path, is_derived=False, study_uid=None):
    """
    Create a minimal DICOM file for testing.

    Args:
        output_path: Path where to save the DICOM file
        is_derived: If True, creates a DERIVED image; otherwise ORIGINAL
        study_uid: Optional StudyInstanceUID to use (for grouping files)

    Returns:
        The created dataset
    """
    file_meta = Dataset()
    file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"  # MR Image Storage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.ImplementationClassUID = generate_uid()

    ds = FileDataset(output_path, dataset={}, file_meta=file_meta, preamble=b"\0" * 128)

    # Add required DICOM tags
    ds.PatientName = "Test^Patient"
    ds.PatientID = "TEST001"
    ds.StudyInstanceUID = study_uid if study_uid else generate_uid()
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.StudyDate = datetime.datetime.now().strftime("%Y%m%d")
    ds.StudyTime = datetime.datetime.now().strftime("%H%M%S")
    ds.StudyDescription = "TestPI^TestProject"
    ds.SeriesNumber = "1"
    ds.InstanceNumber = "1"
    ds.Modality = "MR"
    ds.StudyID = "1"
    ds.ProtocolName = "TestProtocol"
    ds.SeriesDescription = "TestSeries"
    ds.ContentDate = ds.StudyDate

    # Set ImageType - either ORIGINAL or DERIVED
    if is_derived:
        ds.ImageType = ["DERIVED", "SECONDARY"]
    else:
        ds.ImageType = ["ORIGINAL", "PRIMARY"]

    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = 64
    ds.Columns = 64
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0

    # Create minimal pixel data (64x64 = 4096 pixels * 2 bytes = 8192 bytes)
    ds.PixelData = b"\x00" * 8192

    # Save the file
    ds.save_as(output_path)
    return ds


@pytest.mark.unit
@pytest.mark.skipif(not PYDICOM_AVAILABLE, reason="pydicom not available")
class TestSkipDerived:
    """Tests for skip_derived functionality."""

    def test_is_derived_image_with_derived(self, temp_output_dir):
        """Test that _is_derived_image correctly identifies DERIVED images."""
        # Create a DERIVED DICOM file
        dcm_path = os.path.join(temp_output_dir, "derived.dcm")
        create_test_dicom(dcm_path, is_derived=True)

        # Create a DicomSorter instance
        sorter = dicom_sorter.DicomSorter(
            temp_output_dir,
            sort_rules.sort_rule_CFMM,
            temp_output_dir,
            skip_derived=False,  # skip_derived value doesn't matter for this test
        )

        # Test the method
        assert sorter._is_derived_image(dcm_path) is True

    def test_is_derived_image_with_original(self, temp_output_dir):
        """Test that _is_derived_image correctly identifies ORIGINAL images."""
        # Create an ORIGINAL DICOM file
        dcm_path = os.path.join(temp_output_dir, "original.dcm")
        create_test_dicom(dcm_path, is_derived=False)

        # Create a DicomSorter instance
        sorter = dicom_sorter.DicomSorter(
            temp_output_dir, sort_rules.sort_rule_CFMM, temp_output_dir, skip_derived=False
        )

        # Test the method
        assert sorter._is_derived_image(dcm_path) is False

    def test_skip_derived_false_includes_all(self, temp_output_dir):
        """Test that skip_derived=False includes both ORIGINAL and DERIVED images."""
        input_dir = os.path.join(temp_output_dir, "input")
        output_dir = os.path.join(temp_output_dir, "output")
        os.makedirs(input_dir)
        os.makedirs(output_dir)

        # Use same StudyInstanceUID for all files to group them into one tar
        study_uid = generate_uid()

        # Create 3 ORIGINAL images
        for i in range(3):
            dcm_path = os.path.join(input_dir, f"original_{i}.dcm")
            create_test_dicom(dcm_path, is_derived=False, study_uid=study_uid)

        # Create 2 DERIVED images
        for i in range(2):
            dcm_path = os.path.join(input_dir, f"derived_{i}.dcm")
            create_test_dicom(dcm_path, is_derived=True, study_uid=study_uid)

        # Create DicomSorter with skip_derived=False
        with dicom_sorter.DicomSorter(
            input_dir, sort_rules.sort_rule_CFMM, output_dir, skip_derived=False
        ) as sorter:
            tar_files = sorter.tar(5)

        # Should create tar file(s) containing all 5 files
        assert tar_files is not None
        assert len(tar_files) >= 1

        # Count total files in all tars
        import tarfile

        total_files = 0
        for tar_file in tar_files:
            if tar_file.endswith(".tar"):
                with tarfile.open(tar_file, "r") as tar:
                    total_files += len(tar.getmembers())

        assert total_files == 5

    def test_skip_derived_true_excludes_derived(self, temp_output_dir):
        """Test that skip_derived=True excludes DERIVED images."""
        input_dir = os.path.join(temp_output_dir, "input")
        output_dir = os.path.join(temp_output_dir, "output")
        os.makedirs(input_dir)
        os.makedirs(output_dir)

        # Use same StudyInstanceUID for all files to group them
        study_uid = generate_uid()

        # Create 3 ORIGINAL images
        for i in range(3):
            dcm_path = os.path.join(input_dir, f"original_{i}.dcm")
            create_test_dicom(dcm_path, is_derived=False, study_uid=study_uid)

        # Create 2 DERIVED images
        for i in range(2):
            dcm_path = os.path.join(input_dir, f"derived_{i}.dcm")
            create_test_dicom(dcm_path, is_derived=True, study_uid=study_uid)

        # Create DicomSorter with skip_derived=True
        with dicom_sorter.DicomSorter(
            input_dir, sort_rules.sort_rule_CFMM, output_dir, skip_derived=True
        ) as sorter:
            tar_files = sorter.tar(5)

        # Should create tar file(s) containing only 3 ORIGINAL files
        assert tar_files is not None
        assert len(tar_files) >= 1

        # Count total files in all tars
        import tarfile

        total_files = 0
        for tar_file in tar_files:
            if tar_file.endswith(".tar"):
                with tarfile.open(tar_file, "r") as tar:
                    total_files += len(tar.getmembers())

        assert total_files == 3

    def test_skip_derived_with_only_derived_creates_no_tar(self, temp_output_dir):
        """Test that skip_derived=True with only DERIVED images creates no tar files."""
        input_dir = os.path.join(temp_output_dir, "input")
        output_dir = os.path.join(temp_output_dir, "output")
        os.makedirs(input_dir)
        os.makedirs(output_dir)

        # Create only DERIVED images
        study_uid = generate_uid()
        for i in range(3):
            dcm_path = os.path.join(input_dir, f"derived_{i}.dcm")
            create_test_dicom(dcm_path, is_derived=True, study_uid=study_uid)

        # Create DicomSorter with skip_derived=True
        with dicom_sorter.DicomSorter(
            input_dir, sort_rules.sort_rule_CFMM, output_dir, skip_derived=True
        ) as sorter:
            tar_files = sorter.tar(5)

        # Should return None or empty list since all files are skipped
        assert tar_files is None or len(tar_files) == 0
