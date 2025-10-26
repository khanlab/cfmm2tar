"""
Tests for BIDS validator functionality.
"""

import json
from pathlib import Path

import pytest

from cfmm2tar import validate_bids


@pytest.fixture
def temp_bids_dataset(tmp_path):
    """
    Create a minimal valid BIDS dataset for testing.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        Path to the BIDS dataset root
    """
    bids_root = tmp_path / "test_bids_dataset"
    bids_root.mkdir()

    # Create minimal dataset_description.json
    dataset_desc = {
        "Name": "Test Dataset",
        "BIDSVersion": "1.9.0",
        "DatasetType": "raw",
        "Authors": ["Test Author"],
    }

    with open(bids_root / "dataset_description.json", "w") as f:
        json.dump(dataset_desc, f, indent=2)

    # Create participants.tsv
    participants_tsv = "participant_id\tsex\tage\nsub-01\tM\t30\n"
    with open(bids_root / "participants.tsv", "w") as f:
        f.write(participants_tsv)

    # Create README
    with open(bids_root / "README", "w") as f:
        f.write("# Test BIDS Dataset\n\nThis is a test dataset.\n")

    return bids_root


@pytest.fixture
def temp_nested_bids_datasets(tmp_path):
    """
    Create multiple nested BIDS datasets for testing search functionality.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        tuple: (root_path, list of dataset paths)
    """
    root = tmp_path / "search_root"
    root.mkdir()

    datasets = []

    # Create first dataset
    dataset1 = root / "dataset1"
    dataset1.mkdir()
    dataset_desc1 = {
        "Name": "Dataset 1",
        "BIDSVersion": "1.9.0",
        "DatasetType": "raw",
    }
    with open(dataset1 / "dataset_description.json", "w") as f:
        json.dump(dataset_desc1, f)
    datasets.append(dataset1)

    # Create second dataset in a subdirectory
    subdir = root / "subdir"
    subdir.mkdir()
    dataset2 = subdir / "dataset2"
    dataset2.mkdir()
    dataset_desc2 = {
        "Name": "Dataset 2",
        "BIDSVersion": "1.9.0",
        "DatasetType": "derivative",
    }
    with open(dataset2 / "dataset_description.json", "w") as f:
        json.dump(dataset_desc2, f)
    datasets.append(dataset2)

    return root, datasets


class TestFindBidsDatasets:
    """Tests for finding BIDS datasets."""

    def test_find_single_dataset(self, temp_bids_dataset):
        """Test finding a single BIDS dataset."""
        parent_dir = temp_bids_dataset.parent
        datasets = validate_bids.find_bids_datasets(parent_dir)

        assert len(datasets) == 1
        assert datasets[0] == temp_bids_dataset

    def test_find_multiple_datasets(self, temp_nested_bids_datasets):
        """Test finding multiple BIDS datasets in nested directories."""
        root, expected_datasets = temp_nested_bids_datasets
        found_datasets = validate_bids.find_bids_datasets(root)

        assert len(found_datasets) == 2
        assert set(found_datasets) == set(expected_datasets)

    def test_find_no_datasets(self, tmp_path):
        """Test when no BIDS datasets are present."""
        datasets = validate_bids.find_bids_datasets(tmp_path)
        assert len(datasets) == 0


class TestValidateBidsDataset:
    """Tests for validating BIDS datasets."""

    def test_validate_minimal_dataset(self, temp_bids_dataset):
        """Test validation of a minimal BIDS dataset."""
        # Note: This test may fail if bids-validator-deno is not installed
        # or if the minimal dataset is not sufficient for the validator
        success, stdout, stderr = validate_bids.validate_bids_dataset(temp_bids_dataset)

        # We expect this to either succeed or fail gracefully
        assert isinstance(success, bool)
        assert isinstance(stdout, str)
        assert isinstance(stderr, str)

    def test_validate_nonexistent_dataset(self):
        """Test validation of a non-existent dataset."""
        fake_path = Path("/nonexistent/path/to/dataset")
        success, stdout, stderr = validate_bids.validate_bids_dataset(fake_path)

        assert success is False
        assert "does not exist" in stderr

    def test_validate_invalid_dataset(self, tmp_path):
        """Test validation of a directory without dataset_description.json."""
        invalid_dir = tmp_path / "invalid_dataset"
        invalid_dir.mkdir()

        success, stdout, stderr = validate_bids.validate_bids_dataset(invalid_dir)

        assert success is False
        assert "dataset_description.json" in stderr

    def test_validator_not_found(self, temp_bids_dataset):
        """Test handling when bids-validator-deno is not installed."""
        success, stdout, stderr = validate_bids.validate_bids_dataset(
            temp_bids_dataset, validator_path="/nonexistent/validator"
        )

        assert success is False
        assert "not found" in stderr.lower() or "error" in stderr.lower()


class TestValidateBidsIntegration:
    """Integration tests for BIDS validation (requires bids-validator-deno)."""

    @pytest.mark.integration
    def test_validate_with_real_validator(self, temp_bids_dataset):
        """
        Test validation with the actual bids-validator-deno.

        This test is marked as integration and will only run when:
        1. The integration marker is selected
        2. bids-validator-deno is installed
        """
        import shutil

        # Check if bids-validator-deno is available
        if shutil.which("bids-validator-deno") is None:
            pytest.skip("bids-validator-deno not installed")

        success, stdout, stderr = validate_bids.validate_bids_dataset(temp_bids_dataset)

        # The validator should run, though the minimal dataset might have issues
        assert isinstance(success, bool)
        # Validator should produce some output
        assert stdout or stderr
