import unittest
from types import SimpleNamespace

from pydantic import SecretStr

from Services.downloader import PlayDownloader


class GplaydlEnvironmentTests(unittest.TestCase):
    def make_downloader(self, api_key=None):
        downloader = object.__new__(PlayDownloader)
        downloader._settings = SimpleNamespace(gplaydl_api_key=api_key)
        return downloader

    def test_api_key_is_forwarded_to_child_process_environment(self):
        downloader = self.make_downloader(SecretStr("test-dispenser-key"))
        self.assertEqual(
            downloader._gplaydl_env(),
            {"GPLAYDL_API_KEY": "test-dispenser-key"},
        )

    def test_missing_api_key_keeps_inherited_environment(self):
        downloader = self.make_downloader()
        self.assertIsNone(downloader._gplaydl_env())

    def test_empty_api_key_is_not_forwarded(self):
        downloader = self.make_downloader(SecretStr("  "))
        self.assertIsNone(downloader._gplaydl_env())


if __name__ == "__main__":
    unittest.main()
