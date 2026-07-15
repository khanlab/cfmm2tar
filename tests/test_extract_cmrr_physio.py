#!/usr/bin/env python3
"""
Unit tests for extract_cmrr_physio.
"""

import os
import struct

import pytest

try:
    from pydicom.dataset import Dataset, FileDataset
    from pydicom.uid import ExplicitVRLittleEndian, generate_uid

    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False

from cfmm2tar.extract_cmrr_physio import extract_cmrr_physio


def _build_physio_private_data(log_entries, rows=2):
    """
    Build the binary payload stored in private tag (0x7FE1, 0x1010).

    Each log entry is a (filename, data) pair.  The layout per "part" is:
        bytes 0-3   : uint32 datalen
        bytes 4-7   : uint32 filenamelen
        bytes 8-...  : filename (UTF-8)
        bytes 1024-...: log data
    The total size of one part is ``rows * 1024`` bytes.

    Parameters
    ----------
    log_entries : list of (str, bytes)
        Each tuple is (log_filename, log_data).
    rows : int
        Value to store as AcquisitionNumber; controls part size (rows * 1024).
    """
    numFiles = len(log_entries)
    part_size = rows * 1024  # bytes per part

    buf = bytearray(part_size * numFiles)
    for idx, (name, data) in enumerate(log_entries):
        offset = idx * part_size
        name_b = name.encode("utf-8")
        struct.pack_into("<I", buf, offset + 0, len(data))
        struct.pack_into("<I", buf, offset + 4, len(name_b))
        buf[offset + 8 : offset + 8 + len(name_b)] = name_b
        buf[offset + 1024 : offset + 1024 + len(data)] = data

    return bytes(buf), rows


def _create_physio_dicom(path, private_data, rows):
    """
    Create a minimal CMRR-physio DICOM file at *path*.
    """
    file_meta = Dataset()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.ImplementationClassUID = generate_uid()

    ds = FileDataset(path, {}, file_meta=file_meta, preamble=b"\x00" * 128)

    ds.ImageType = ["ORIGINAL", "PRIMARY", "RAWDATA", "PHYSIO"]
    ds.AcquisitionNumber = rows

    # Private block: group 0x7FE1
    ds.add_new((0x7FE1, 0x0010), "LO", "SIEMENS CSA NON-IMAGE")
    ds.add_new((0x7FE1, 0x1010), "OB", private_data)

    ds.save_as(path, enforce_file_format=True)
    return path


@pytest.mark.skipif(not PYDICOM_AVAILABLE, reason="pydicom not installed")
@pytest.mark.unit
class TestExtractCmrrPhysio:
    def test_single_log_file_extracted(self, tmp_path):
        """A single physio log file is written to the output directory."""
        log_data = b"ECG data line 1\nECG data line 2\n"
        private_data, rows = _build_physio_private_data([("test_ECG.log", log_data)])

        dcm_path = str(tmp_path / "physio.dcm")
        _create_physio_dicom(dcm_path, private_data, rows)

        out_dir = str(tmp_path / "output")
        os.makedirs(out_dir)

        extract_cmrr_physio(dcm_path, out_dir)

        out_file = os.path.join(out_dir, "test_ECG.log")
        assert os.path.exists(out_file), "Expected output log file was not created"
        with open(out_file, "rb") as f:
            assert f.read() == log_data

    def test_multiple_log_files_extracted(self, tmp_path):
        """Multiple physio log files are all written to the output directory."""
        entries = [
            ("scan_ECG.log", b"ecg\n"),
            ("scan_RESP.log", b"resp\n"),
            ("scan_PULS.log", b"puls\n"),
        ]
        private_data, rows = _build_physio_private_data(entries, rows=4)

        dcm_path = str(tmp_path / "physio_multi.dcm")
        _create_physio_dicom(dcm_path, private_data, rows)

        out_dir = str(tmp_path / "output")
        os.makedirs(out_dir)

        extract_cmrr_physio(dcm_path, out_dir)

        for name, data in entries:
            out_file = os.path.join(out_dir, name)
            assert os.path.exists(out_file), f"Expected {name} was not created"
            with open(out_file, "rb") as f:
                assert f.read() == data

    def test_non_physio_dicom_produces_no_output(self, tmp_path):
        """A regular imaging DICOM should not produce any output files."""
        file_meta = Dataset()
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.4"
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.ImplementationClassUID = generate_uid()

        ds = FileDataset(
            str(tmp_path / "imaging.dcm"), {}, file_meta=file_meta, preamble=b"\x00" * 128
        )
        ds.ImageType = ["ORIGINAL", "PRIMARY", "M"]
        ds.AcquisitionNumber = 1
        dcm_path = str(tmp_path / "imaging.dcm")
        ds.save_as(dcm_path, enforce_file_format=True)

        out_dir = str(tmp_path / "output")
        os.makedirs(out_dir)

        extract_cmrr_physio(dcm_path, out_dir)

        assert os.listdir(out_dir) == [], "No files should be written for a non-physio DICOM"

    def test_missing_file_does_not_raise(self, tmp_path):
        """Passing a non-existent path should not raise; errors are logged internally."""
        out_dir = str(tmp_path / "output")
        os.makedirs(out_dir)
        # Should not raise
        extract_cmrr_physio(str(tmp_path / "nonexistent.dcm"), out_dir)

    def test_log_data_content_is_binary_safe(self, tmp_path):
        """Binary log data (arbitrary bytes) is preserved exactly."""
        log_data = bytes(range(256)) * 4  # 1024 arbitrary bytes
        private_data, rows = _build_physio_private_data([("binary.log", log_data)], rows=2)

        dcm_path = str(tmp_path / "physio_bin.dcm")
        _create_physio_dicom(dcm_path, private_data, rows)

        out_dir = str(tmp_path / "output")
        os.makedirs(out_dir)

        extract_cmrr_physio(dcm_path, out_dir)

        out_file = os.path.join(out_dir, "binary.log")
        assert os.path.exists(out_file)
        with open(out_file, "rb") as f:
            assert f.read() == log_data
