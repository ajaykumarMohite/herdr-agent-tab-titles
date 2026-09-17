import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from rename_tabs_from_agent_titles import (
    MAX_LABEL_LENGTH,
    describes_a_task,
    panes_to_rename,
    shortened,
    task_title_of,
)


class DescribesATaskTest(unittest.TestCase):
    def test_accepts_a_task_title(self):
        self.assertTrue(describes_a_task("PR 33780 review"))

    def test_rejects_a_shell_prompt_title(self):
        self.assertFalse(describes_a_task("ajaykumar@host:~/work/amber"))

    def test_rejects_a_path_title(self):
        self.assertFalse(describes_a_task("/home/ajaykumar/work"))
        self.assertFalse(describes_a_task("~/work/amber"))

    def test_rejects_a_bare_product_name(self):
        self.assertFalse(describes_a_task("Claude Code"))
        self.assertFalse(describes_a_task("codex"))

    def test_rejects_an_empty_title(self):
        self.assertFalse(describes_a_task(""))


class ShortenedTest(unittest.TestCase):
    def test_keeps_a_short_title_whole(self):
        self.assertEqual(shortened("Herdr config"), "Herdr config")

    def test_trims_on_a_word_boundary(self):
        self.assertEqual(shortened("Herdr config update"), "Herdr config")

    def test_clips_a_single_long_word(self):
        self.assertEqual(shortened("supercalifragilistic"), "supercalifragilist")

    def test_never_exceeds_the_limit(self):
        for title in ("a" * 50, "word " * 12, "RFC 8058 one-click unsubscribe"):
            self.assertLessEqual(len(shortened(title)), MAX_LABEL_LENGTH)


class TaskTitleOfTest(unittest.TestCase):
    def test_reads_the_stripped_title(self):
        self.assertEqual(
            task_title_of({"terminal_title_stripped": " Transport reuse "}),
            "Transport reuse",
        )

    def test_returns_empty_for_a_shell_pane(self):
        self.assertEqual(task_title_of({"terminal_title_stripped": "user@host:~"}), "")

    def test_returns_empty_when_the_field_is_missing(self):
        self.assertEqual(task_title_of({}), "")


class PanesToRenameTest(unittest.TestCase):
    def test_returns_nothing_without_arguments_or_event(self):
        self.assertEqual(panes_to_rename([]), [])


if __name__ == "__main__":
    unittest.main()
