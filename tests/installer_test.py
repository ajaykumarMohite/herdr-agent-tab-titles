import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import install_claude_code_hook as installer


class DiscoveredConfigDirsTest(unittest.TestCase):
    def setUp(self):
        self.home = pathlib.Path(tempfile.mkdtemp())
        patcher = mock.patch.object(pathlib.Path, "home", return_value=self.home)
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_config_dir(self, name, with_settings):
        directory = self.home / name
        directory.mkdir()
        if with_settings:
            (directory / "settings.json").write_text("{}")
        return directory

    def test_finds_the_default_and_the_suffixed_dirs(self):
        self.make_config_dir(".claude", with_settings=True)
        self.make_config_dir(".claude-work", with_settings=True)

        found = [directory.name for directory in installer.discovered_config_dirs()]

        self.assertEqual(found, [".claude", ".claude-work"])

    def test_ignores_a_directory_without_settings(self):
        self.make_config_dir(".claude", with_settings=True)
        self.make_config_dir(".claude-local", with_settings=False)

        found = [directory.name for directory in installer.discovered_config_dirs()]

        self.assertEqual(found, [".claude"])

    def test_finds_nothing_in_an_empty_home(self):
        self.assertEqual(installer.discovered_config_dirs(), [])


class RequestedConfigDirsTest(unittest.TestCase):
    def test_prefers_the_explicit_flag(self):
        requested = installer.requested_config_dirs(["--config-dir", "/tmp/elsewhere"])

        self.assertEqual(requested, [pathlib.Path("/tmp/elsewhere")])

    def test_falls_back_to_the_environment(self):
        with mock.patch.dict("os.environ", {"CLAUDE_CONFIG_DIR": "/tmp/from-env"}):
            requested = installer.requested_config_dirs([])

        self.assertEqual(requested, [pathlib.Path("/tmp/from-env")])

    def test_is_empty_without_either(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(installer.requested_config_dirs([]), [])


class RegisterTest(unittest.TestCase):
    def test_adds_both_events_once(self):
        settings = {}

        installer.register(settings, pathlib.Path("/tmp/shim.sh"))
        installer.register(settings, pathlib.Path("/tmp/shim.sh"))

        for event in installer.HOOKED_EVENTS:
            self.assertEqual(len(settings["hooks"][event]), 1)

    def test_keeps_hooks_that_are_already_there(self):
        settings = {"hooks": {"Stop": [{"matcher": "*", "hooks": [{"command": "true"}]}]}}

        installer.register(settings, pathlib.Path("/tmp/shim.sh"))

        self.assertEqual(len(settings["hooks"]["Stop"]), 2)
        self.assertIn("true", json.dumps(settings["hooks"]["Stop"][0]))


if __name__ == "__main__":
    unittest.main()
