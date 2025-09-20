import os
import unittest
import subprocess
import shutil

@unittest.skip("Backend CLI integration requires external services and real Sentinel data")
class TestBackendFloodDetection(unittest.TestCase):
    def setUp(self):
        # Setup test parameters
        self.location = "Bengaluru"
        self.latitude = ""
        self.longitude = ""
        self.base_date = "2025-01-01"
        self.sensor_choices = ['1', '2', '3']  # Automatic, Sentinel-2, Sentinel-1
        self.output_dir = "data/results"
        # Clean output directory before tests
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def run_main_backend(self, sensor_choice, location=None, latitude=None, longitude=None, base_date=None):
        # Prepare the input sequence for the script
        loc = location if location is not None else self.location
        lat = latitude if latitude is not None else self.latitude
        lon = longitude if longitude is not None else self.longitude
        date = base_date if base_date is not None else self.base_date
        inputs = f"{loc}\n{lat}\n{lon}\n{date}\n{sensor_choice}\n"
        # Run the backend main script with inputs
        process = subprocess.Popen(
            ["python3", "backend/main_backend.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        try:
            stdout, stderr = process.communicate(input=inputs, timeout=300)  # 5 minutes timeout
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            raise RuntimeError("Test timed out while running backend/main_backend.py")
        return process.returncode, stdout, stderr

    def test_flood_detection_workflow(self):
        for sensor_choice in self.sensor_choices:
            with self.subTest(sensor_choice=sensor_choice):
                retcode, stdout, stderr = self.run_main_backend(sensor_choice)
                self.assertEqual(retcode, 0, f"Process failed for sensor {sensor_choice} with error: {stderr}")
                # Check output files created
                files_created = os.listdir(self.output_dir)
                self.assertTrue(len(files_created) > 0, f"No output files created for sensor {sensor_choice}")
                # Additional checks can be added here to verify output correctness
                # For example, check specific file names or contents if expected outputs are known

    def test_invalid_location(self):
        retcode, stdout, stderr = self.run_main_backend('1', location="InvalidLocationXYZ")
        self.assertNotEqual(retcode, 0)
        self.assertIn("Could not find location", stdout)

    def test_invalid_date_format(self):
        with self.assertRaises(ValueError):
            # Directly test datetime parsing in main_backend.py would require refactoring
            # So here we simulate by calling run_main_backend with invalid date and catching error
            self.run_main_backend('1', base_date="invalid-date")

    def test_invalid_sensor_choice(self):
        retcode, stdout, stderr = self.run_main_backend('9')
        self.assertNotEqual(retcode, 0)
        self.assertIn("Invalid sensor choice", stdout)

    def test_cloud_coverage_fallback(self):
        # This test assumes the check_cloud_coverage function can be mocked or overridden
        # Since it's not currently designed for dependency injection, this test is a placeholder
        pass

if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
