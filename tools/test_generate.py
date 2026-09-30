import unittest

from generate import render


class GenerateTests(unittest.TestCase):
    def test_client_blocks_keep_common_text_and_selected_branch(self):
        source = (b"common\n{{#claude}}\nClaude\n{{/claude}}\n"
                  b"{{#codex}}\nCodex\n{{/codex}}\nend\n")
        self.assertEqual(render(source, "claude"), b"common\nClaude\nend\n")
        self.assertEqual(render(source, "codex"), b"common\nCodex\nend\n")

    def test_malformed_blocks_fail(self):
        for source in (b"{{#claude}}\n", b"{{/codex}}\n",
                       b"{{#claude}}\n{{#codex}}\n{{/codex}}\n{{/claude}}\n"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                render(source, "claude")

    def test_unresolved_marker_fails(self):
        with self.assertRaisesRegex(ValueError, "Unresolved"):
            render(b"{{unknown}}\n", "claude")
