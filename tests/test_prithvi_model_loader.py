import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.prithvi_transformers import model_loader
from llm import config as llm_config


class TestPrithviModelLoader(unittest.TestCase):
    def test_loads_from_local_directory_when_available(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch.dict(os.environ, {"PRITHVI_MODEL_PATH": tmpdir}, clear=False), \
                    mock.patch.object(llm_config, "PRITHVI_MODEL_PATH", tmpdir), \
                    mock.patch("models.prithvi_transformers.model_loader.AutoConfig.from_pretrained") as mock_config, \
                    mock.patch("models.prithvi_transformers.model_loader.AutoModel.from_pretrained") as mock_model, \
                    mock.patch("models.prithvi_transformers.model_loader.AutoProcessor.from_pretrained") as mock_processor:

                mock_config.return_value = mock.sentinel.config

                mock_model.side_effect = lambda path, *args, **kwargs: self._assert_path_and_return(
                    path, tmpdir, mock.sentinel.model
                )
                mock_processor.side_effect = lambda path, *args, **kwargs: self._assert_path_and_return(
                    path, tmpdir, mock.sentinel.processor
                )

                model, processor = model_loader.load_prithvi_model()

                self.assertIs(model, mock.sentinel.model)
                self.assertIs(processor, mock.sentinel.processor)

                mock_config.assert_called_once()
                self.assertEqual(mock_config.call_args.args[0], tmpdir)

    def _assert_path_and_return(self, received_path, expected_path, return_value):
        self.assertEqual(received_path, expected_path)
        return return_value


if __name__ == "__main__":
    unittest.main()
