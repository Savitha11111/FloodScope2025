# test_model_inference.py

import pytest
import sys
from unittest import mock

# Import the function to test
from backend.model_inference import run_flood_detection

# Patch the config constants and subprocess for all tests in this module
@pytest.fixture(autouse=True)
def patch_config_and_subprocess(monkeypatch):
    # Patch config constants
    monkeypatch.setattr("backend.model_inference.PRITHVI_MODEL_PATH", "/fake/model/path")
    monkeypatch.setattr("backend.model_inference.PRITHVI_CONFIG_PATH", "/fake/config/path")
    monkeypatch.setattr("backend.model_inference.RESULTS_DIR", "/fake/results/dir")
    # Patch subprocess.run
    with mock.patch("backend.model_inference.subprocess.run") as mock_run:
        yield mock_run

class TestRunFloodDetection:
    # --- Happy Path Tests ---

    @pytest.mark.happy
    def test_single_image_path_runs_subprocess(self, patch_config_and_subprocess):
        """
        Test that run_flood_detection correctly constructs and calls subprocess.run
        with a single image path.
        """
        image_paths = ["/tmp/image1.tif"]
        run_flood_detection(image_paths)
        # Check subprocess.run was called once
        assert patch_config_and_subprocess.call_count == 1
        # Check the command string contains the image path and all config values
        called_args, called_kwargs = patch_config_and_subprocess.call_args
        command = called_args[0]
        assert "/tmp/image1.tif" in command
        assert "--config_path /fake/config/path" in command
        assert "--checkpoint /fake/model/path" in command
        assert "--output_dir /fake/results/dir" in command
        assert "--rgb_outputs" in command
        assert "--data_files /tmp/image1.tif" in command
        assert called_kwargs["shell"] is True
        assert called_kwargs["check"] is True

    @pytest.mark.happy
    def test_multiple_image_paths_are_joined(self, patch_config_and_subprocess):
        """
        Test that multiple image paths are joined with spaces in the command.
        """
        image_paths = ["/tmp/img1.tif", "/tmp/img2.tif", "/tmp/img3.tif"]
        run_flood_detection(image_paths)
        called_args, _ = patch_config_and_subprocess.call_args
        command = called_args[0]
        # All image paths should be present, space-separated
        assert "--data_files /tmp/img1.tif /tmp/img2.tif /tmp/img3.tif" in command

    @pytest.mark.happy
    def test_print_statements_are_executed(self, patch_config_and_subprocess, capsys):
        """
        Test that the expected print statements are output.
        """
        image_paths = ["/tmp/image1.tif"]
        run_flood_detection(image_paths)
        captured = capsys.readouterr()
        assert "🚀 Running Prithvi Model for Flood Detection..." in captured.out
        assert "✅ Flood Mask Saved in:" in captured.out
        assert "/fake/results/dir" in captured.out

    # --- Edge Case Tests ---

    @pytest.mark.edge
    def test_empty_image_paths_list(self, patch_config_and_subprocess):
        """
        Test that an empty image_paths list still calls subprocess with no data files.
        """
        image_paths = []
        run_flood_detection(image_paths)
        called_args, _ = patch_config_and_subprocess.call_args
        command = called_args[0]
        # --data_files should be present but empty
        assert "--data_files" in command
        # There should be no file after --data_files
        assert "--data_files" in command
        # The command should not have any .tif file after --data_files
        assert ".tif" not in command

    @pytest.mark.edge
    def test_image_paths_with_special_characters(self, patch_config_and_subprocess):
        """
        Test that image paths with spaces and special characters are handled.
        """
        image_paths = ["/tmp/stränge path/with space@file.tif"]
        run_flood_detection(image_paths)
        called_args, _ = patch_config_and_subprocess.call_args
        command = called_args[0]
        # The special path should appear as-is in the command string
        assert "/tmp/stränge path/with space@file.tif" in command

    @pytest.mark.edge
    def test_subprocess_raises_exception(self, monkeypatch):
        """
        Test that if subprocess.run raises CalledProcessError, it propagates.
        """
        def raise_error(*args, **kwargs):
            raise subprocess.CalledProcessError(1, "cmd")
        monkeypatch.setattr("backend.model_inference.subprocess.run", raise_error)
        image_paths = ["/tmp/image1.tif"]
        with pytest.raises(subprocess.CalledProcessError):
            run_flood_detection(image_paths)

    @pytest.mark.edge
    def test_non_string_image_paths(self, patch_config_and_subprocess):
        """
        Test that non-string elements in image_paths are converted to string in the command.
        """
        image_paths = [123, None, "/tmp/image3.tif"]
        # The function does not explicitly cast to str, so this will raise TypeError
        # when trying to join non-string types. We expect this error.
        with pytest.raises(TypeError):
            run_flood_detection(image_paths)