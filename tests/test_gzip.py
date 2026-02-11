#!/usr/bin/env python3
"""
Tests for gzip compression functionality in DicomSorter.

These are unit tests that verify the gzip compression option works correctly.
"""

import datetime
import os
import tarfile

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


def create_test_dicom(output_path, study_uid=None):
    """
    Create a minimal DICOM file for testing.

    Args:
        output_path: Path where to save the DICOM file
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
class TestGzipCompression:
    """Tests for gzip compression functionality."""

    def test_tar_without_gzip_creates_tar_files(self, temp_output_dir):
        """Test that use_gzip=False creates regular .tar files."""
        input_dir = os.path.join(temp_output_dir, "input")
        output_dir = os.path.join(temp_output_dir, "output")
        os.makedirs(input_dir)
        os.makedirs(output_dir)

        # Use same StudyInstanceUID for all files to group them into one tar
        study_uid = generate_uid()

        # Create 3 DICOM files
        for i in range(3):
            dcm_path = os.path.join(input_dir, f"test_{i}.dcm")
            create_test_dicom(dcm_path, study_uid=study_uid)

        # Create DicomSorter with use_gzip=False (default)
        with dicom_sorter.DicomSorter(
            input_dir, sort_rules.sort_rule_CFMM, output_dir, skip_derived=False
        ) as sorter:
            tar_files = sorter.tar(5, use_gzip=False)

        # Should create tar file(s) with .tar extension
        assert tar_files is not None
        assert len(tar_files) >= 1
        
        # Check that files have .tar extension (not .tar.gz)
        for tar_file in tar_files:
            if not tar_file.endswith(".attached.tar"):
                assert tar_file.endswith(".tar")
                assert not tar_file.endswith(".tar.gz")

        # Verify files can be opened as regular tar
        for tar_file in tar_files:
            if tar_file.endswith(".tar"):
                with tarfile.open(tar_file, "r") as tar:
                    members = tar.getmembers()
                    assert len(members) > 0

    def test_tar_with_gzip_creates_tar_gz_files(self, temp_output_dir):
        """Test that use_gzip=True creates .tar.gz files."""
        input_dir = os.path.join(temp_output_dir, "input")
        output_dir = os.path.join(temp_output_dir, "output")
        os.makedirs(input_dir)
        os.makedirs(output_dir)

        # Use same StudyInstanceUID for all files to group them into one tar
        study_uid = generate_uid()

        # Create 3 DICOM files
        for i in range(3):
            dcm_path = os.path.join(input_dir, f"test_{i}.dcm")
            create_test_dicom(dcm_path, study_uid=study_uid)

        # Create DicomSorter with use_gzip=True
        with dicom_sorter.DicomSorter(
            input_dir, sort_rules.sort_rule_CFMM, output_dir, skip_derived=False
        ) as sorter:
            tar_files = sorter.tar(5, use_gzip=True)

        # Should create tar file(s) with .tar.gz extension
        assert tar_files is not None
        assert len(tar_files) >= 1
        
        # Check that files have .tar.gz extension
        for tar_file in tar_files:
            if not tar_file.endswith(".attached.tar.gz"):
                assert tar_file.endswith(".tar.gz")

        # Verify files can be opened as gzipped tar
        for tar_file in tar_files:
            if tar_file.endswith(".tar.gz"):
                with tarfile.open(tar_file, "r:gz") as tar:
                    members = tar.getmembers()
                    assert len(members) > 0

    def test_gzip_tar_contains_correct_files(self, temp_output_dir):
        """Test that gzipped tar files contain the correct number of DICOM files."""
        input_dir = os.path.join(temp_output_dir, "input")
        output_dir = os.path.join(temp_output_dir, "output")
        os.makedirs(input_dir)
        os.makedirs(output_dir)

        # Use same StudyInstanceUID for all files to group them
        study_uid = generate_uid()

        # Create 5 DICOM files
        num_files = 5
        for i in range(num_files):
            dcm_path = os.path.join(input_dir, f"test_{i}.dcm")
            create_test_dicom(dcm_path, study_uid=study_uid)

        # Create DicomSorter with use_gzip=True
        with dicom_sorter.DicomSorter(
            input_dir, sort_rules.sort_rule_CFMM, output_dir, skip_derived=False
        ) as sorter:
            tar_files = sorter.tar(5, use_gzip=True)

        # Count files in all tar archives
        total_files = 0
        for tar_file in tar_files:
            if tar_file.endswith(".tar.gz"):
                with tarfile.open(tar_file, "r:gz") as tar:
                    total_files += len(tar.getmembers())

        # Should have all 5 files
        assert total_files == num_files

    def test_gzip_tar_files_are_smaller(self, temp_output_dir):
        """Test that gzipped tar files are smaller than uncompressed ones."""
        input_dir = os.path.join(temp_output_dir, "input")
        output_dir_ungz = os.path.join(temp_output_dir, "output_ungz")
        output_dir_gz = os.path.join(temp_output_dir, "output_gz")
        os.makedirs(input_dir)
        os.makedirs(output_dir_ungz)
        os.makedirs(output_dir_gz)

        # Use same StudyInstanceUID for all files
        study_uid = generate_uid()

        # Create 10 DICOM files (more files = better compression ratio)
        for i in range(10):
            dcm_path = os.path.join(input_dir, f"test_{i}.dcm")
            create_test_dicom(dcm_path, study_uid=study_uid)

        # Create uncompressed tar
        with dicom_sorter.DicomSorter(
            input_dir, sort_rules.sort_rule_CFMM, output_dir_ungz, skip_derived=False
        ) as sorter:
            tar_files_ungz = sorter.tar(5, use_gzip=False)

        # Create compressed tar
        with dicom_sorter.DicomSorter(
            input_dir, sort_rules.sort_rule_CFMM, output_dir_gz, skip_derived=False
        ) as sorter:
            tar_files_gz = sorter.tar(5, use_gzip=True)

        # Get sizes of uncompressed tar files
        size_ungz = sum(
            os.path.getsize(f) for f in tar_files_ungz if f.endswith(".tar")
        )
        
        # Get sizes of compressed tar files
        size_gz = sum(
            os.path.getsize(f) for f in tar_files_gz if f.endswith(".tar.gz")
        )

        # Gzipped files should be smaller
        # Note: compression ratio may vary, but gzip should provide some compression
        assert size_gz < size_ungz, f"Gzipped tar ({size_gz} bytes) should be smaller than uncompressed tar ({size_ungz} bytes)"
