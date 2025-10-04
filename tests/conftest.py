"""
Pytest configuration and fixtures for cfmm2tar tests.
"""
import pytest
import time
import subprocess
import os
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(scope="session")
def dcm4che_server():
    """
    Start a dcm4chee PACS server using docker-compose for testing.
    
    This fixture starts the server at session scope and tears it down after all tests.
    """
    compose_file = Path(__file__).parent / "docker-compose.yml"
    
    # Start the docker-compose services
    print("\nStarting dcm4chee PACS server...")
    subprocess.run(
        ["docker-compose", "-f", str(compose_file), "up", "-d"],
        check=True,
        capture_output=True
    )
    
    # Wait for services to be ready (dcm4chee can take some time to start)
    print("Waiting for dcm4chee to be ready...")
    max_wait = 120  # 2 minutes max wait
    wait_interval = 5
    elapsed = 0
    
    while elapsed < max_wait:
        try:
            # Check if the DICOM port is accepting connections
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "exec", "-T", "arc", 
                 "nc", "-z", "localhost", "11112"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                print("dcm4chee is ready!")
                break
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
        
        time.sleep(wait_interval)
        elapsed += wait_interval
    else:
        print("Warning: dcm4chee may not be fully ready yet")
    
    # Additional wait to ensure all services are stable
    time.sleep(10)
    
    yield {
        "host": "localhost",
        "port": 11112,
        "aet": "DCM4CHEE",
        "username": "admin",
        "password": "admin"
    }
    
    # Teardown: stop docker-compose services
    print("\nStopping dcm4chee PACS server...")
    subprocess.run(
        ["docker-compose", "-f", str(compose_file), "down", "-v"],
        check=True,
        capture_output=True
    )


@pytest.fixture
def temp_output_dir():
    """
    Create a temporary directory for test outputs.
    """
    temp_dir = tempfile.mkdtemp(prefix="cfmm2tar_test_")
    yield temp_dir
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_dicom_file(temp_output_dir):
    """
    Create a minimal DICOM file for testing.
    
    This creates a basic DICOM file that can be used for upload to the test PACS.
    """
    try:
        from pydicom.dataset import Dataset, FileDataset
        from pydicom.uid import generate_uid, ImplicitVRLittleEndian
        import datetime
        
        # Create a minimal DICOM dataset
        file_meta = Dataset()
        file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.4'  # MR Image Storage
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.ImplementationClassUID = generate_uid()
        
        ds = FileDataset(
            filename="test.dcm",
            dataset={},
            file_meta=file_meta,
            preamble=b"\0" * 128
        )
        
        # Add required DICOM tags
        ds.PatientName = "Test^Patient"
        ds.PatientID = "TEST001"
        ds.StudyInstanceUID = generate_uid()
        ds.SeriesInstanceUID = generate_uid()
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
        ds.StudyDate = datetime.datetime.now().strftime('%Y%m%d')
        ds.StudyTime = datetime.datetime.now().strftime('%H%M%S')
        ds.StudyDescription = "Test^Study"
        ds.SeriesNumber = "1"
        ds.InstanceNumber = "1"
        ds.Modality = "MR"
        ds.ImageType = ["ORIGINAL", "PRIMARY"]
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.Rows = 64
        ds.Columns = 64
        ds.BitsAllocated = 16
        ds.BitsStored = 16
        ds.HighBit = 15
        ds.PixelRepresentation = 0
        
        # Create minimal pixel data
        import numpy as np
        ds.PixelData = np.zeros((64, 64), dtype=np.uint16).tobytes()
        
        # Save the file
        output_path = os.path.join(temp_output_dir, "test_dicom.dcm")
        ds.save_as(output_path, write_like_original=False)
        
        return {
            "path": output_path,
            "study_uid": ds.StudyInstanceUID,
            "patient_name": ds.PatientName,
            "patient_id": ds.PatientID,
            "study_date": ds.StudyDate,
            "study_description": ds.StudyDescription
        }
    except ImportError:
        pytest.skip("pydicom not available for creating test DICOM files")
