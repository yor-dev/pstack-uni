import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import upstream


def text(value, mode="100644"):
    return mode, value.encode()


class UpstreamTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "source"
        self.repo.mkdir()
        upstream.git(self.repo, "init", "-q")
        upstream.git(self.repo, "config", "user.name", "Test")
        upstream.git(self.repo, "config", "user.email", "test@example.invalid")
        upstream.git(self.repo, "config", "core.fileMode", "true")
        upstream.git(self.repo, "config", "core.autocrlf", "false")
        self.source = {
            "pstack/.cursor-plugin/plugin.json": text('{"version": "1.0.0"}\n'),
            "pstack/skill.md": text("first\n" + "middle\n" * 12 + "last\n"),
            "pstack/excluded.md": text("cloud routine\n"),
        }
        self.commit = self.commit_tree(self.source)
        self.manifest = {
            "commit": self.commit,
            "version": "1.0.0",
            "scopes": ["pstack"],
            "files": [
                {"source": name,
                 "targets": {platform: [f"{platform}/skill.md"] if name.endswith("/skill.md") else []
                             for platform in upstream.PLATFORMS},
                 "excluded": {platform: "Outside local distribution" for platform in upstream.PLATFORMS}}
                for name in self.source
            ],
            "additions": [],
        }
        self.current = {f"{platform}/skill.md": self.source["pstack/skill.md"]
                        for platform in upstream.PLATFORMS}

    def commit_tree(self, tree):
        for path in (self.repo / "pstack").rglob("*"):
            if path.is_file():
                path.unlink()
        upstream.write_tree(self.repo, tree)
        upstream.git(self.repo, "add", "-A")
        upstream.git(self.repo, "commit", "-qm", "Fixture")
        return upstream.git(self.repo, "rev-parse", "HEAD").decode().strip()

    def compare(self, new):
        commit = self.commit_tree(new)
        output = self.root / "comparison"
        with contextlib.redirect_stdout(io.StringIO()):
            upstream.compare(self.repo, self.manifest, self.source, self.current, commit, output)
        report = json.loads((output / "report.json").read_text())
        return report, upstream.disk_tree(output / "candidate")

    def add_plugin(self):
        source = "pstack/.cursor-plugin/plugin.json"
        self.source[source] = text(
            '{\n\t"version": "1.0.0",\n\t"name": "pstack",\n'
            '\t"description": "Original description"\n}\n'
        )
        self.manifest["commit"] = self.commit_tree(self.source)
        row = next(row for row in self.manifest["files"] if row["source"] == source)
        row["targets"]["claude"] = [upstream.CLAUDE_PLUGIN]
        self.current[upstream.CLAUDE_PLUGIN] = text(
            '{\n  "name": "pstack",\n  "description": "Original description",\n'
            '  "version": "2.0.0"\n}\n'
        )

    def test_source_uses_pinned_objects_despite_dirty_checkout(self):
        (self.repo / "pstack/skill.md").write_text("uncommitted replacement\n")
        (self.repo / "pstack/extra.md").write_text("untracked\n")
        (self.repo / "pstack/excluded.md").unlink()
        commit, source = upstream.source_tree(self.repo, self.commit, ["pstack"])
        self.assertEqual(commit, self.commit)
        self.assertEqual(source, self.source)

    def test_patch_reconstructs_binary_modes_and_local_addition(self):
        source = dict(self.source)
        source["pstack/skill.md"] = ("100644", b"original\0binary\xff")
        current = {f"{platform}/skill.md": ("100755", b"translated\0binary\xfe")
                   for platform in upstream.PLATFORMS}
        current["claude/native.json"] = text('{"native": true}\n')
        manifest = copy.deepcopy(self.manifest)
        manifest["additions"].append({"target": "claude/native.json", "reason": "Native metadata"})
        upstream.validate(manifest, source, current)
        patch_dir = self.root / "maintenance/patches"
        patch_dir.mkdir(parents=True)
        for platform in upstream.PLATFORMS:
            value = upstream.patch_for(upstream.base_tree(manifest, source, platform), {
                name: entry for name, entry in current.items() if name.startswith(platform + "/")
            })
            (patch_dir / f"{platform}.patch").write_bytes(value)
        with patch.object(upstream, "ROOT", self.root), contextlib.redirect_stdout(io.StringIO()):
            upstream.check_patches(manifest, source, current)
            stale = dict(current)
            stale["codex/skill.md"] = ("100644", current["codex/skill.md"][1])
            with self.assertRaisesRegex(ValueError, "patch is stale"):
                upstream.check_patches(manifest, source, stale)

    def test_inventory_rejects_unclassified_sources_and_destinations(self):
        upstream.validate(self.manifest, self.source, self.current)
        source = dict(self.source, **{"pstack/new.md": text("new\n")})
        with self.assertRaisesRegex(ValueError, "Source inventory mismatch"):
            upstream.validate(self.manifest, source, self.current)
        current = dict(self.current, **{"codex/unclassified.md": text("new\n")})
        with self.assertRaisesRegex(ValueError, "Destination inventory mismatch"):
            upstream.validate(self.manifest, self.source, current)

    def test_version_bump_needs_no_patch_update_but_metadata_changes_do(self):
        self.add_plugin()
        upstream.validate(self.manifest, self.source, self.current)
        patch_dir = self.root / "maintenance/patches"
        patch_dir.mkdir(parents=True)
        for platform in upstream.PLATFORMS:
            value = upstream.patch_for(upstream.base_tree(self.manifest, self.source, platform), {
                name: entry for name, entry in self.current.items() if name.startswith(platform + "/")
            })
            (patch_dir / f"{platform}.patch").write_bytes(value)
        saved = (patch_dir / "claude.patch").read_bytes()
        mode, content = self.current[upstream.CLAUDE_PLUGIN]
        self.current[upstream.CLAUDE_PLUGIN] = mode, content.replace(b"2.0.0", b"2.1.0")
        with patch.object(upstream, "ROOT", self.root), contextlib.redirect_stdout(io.StringIO()):
            upstream.check_patches(self.manifest, self.source, self.current)
            regenerated = upstream.patch_for(upstream.base_tree(self.manifest, self.source, "claude"), {
                name: entry for name, entry in self.current.items() if name.startswith("claude/")
            })
            self.assertEqual(regenerated, saved)
            self.assertNotIn(b'"version"', regenerated)
            changed = dict(self.current)
            changed[upstream.CLAUDE_PLUGIN] = mode, content.replace(b"Original", b"Changed")
            with self.assertRaisesRegex(ValueError, "patch is stale"):
                upstream.check_patches(self.manifest, self.source, changed)
            changed[upstream.CLAUDE_PLUGIN] = "100755", self.current[upstream.CLAUDE_PLUGIN][1]
            with self.assertRaisesRegex(ValueError, "patch is stale"):
                upstream.check_patches(self.manifest, self.source, changed)
            changed[upstream.CLAUDE_PLUGIN] = text('{"name": "pstack"}\n')
            with self.assertRaises(KeyError):
                upstream.check_patches(self.manifest, self.source, changed)

    def test_compare_keeps_distribution_version_after_upstream_version_bump(self):
        self.add_plugin()
        new = dict(self.source)
        source = "pstack/.cursor-plugin/plugin.json"
        new[source] = "100644", new[source][1].replace(b"1.0.0", b"1.1.0")
        report, candidate = self.compare(new)
        self.assertEqual(report["version"], "1.1.0")
        self.assertEqual(json.loads(candidate[upstream.CLAUDE_PLUGIN][1]),
                         json.loads(self.current[upstream.CLAUDE_PLUGIN][1]))

    def test_compare_merges_upstream_metadata_without_changing_distribution_version(self):
        self.add_plugin()
        new = dict(self.source)
        source = "pstack/.cursor-plugin/plugin.json"
        new[source] = "100644", new[source][1].replace(b"1.0.0", b"1.1.0").replace(b"Original", b"Updated")
        _, candidate = self.compare(new)
        metadata = json.loads(candidate[upstream.CLAUDE_PLUGIN][1])
        self.assertEqual(metadata["version"], "2.0.0")
        self.assertEqual(metadata["description"], "Updated description")

    def test_compare_merges_nonoverlapping_changes_for_every_target(self):
        original = self.source["pstack/skill.md"][1]
        local = ("100644", original.replace(b"first\n", b"translated first\n"))
        self.current["claude/skill.md"] = local
        self.current["claude/skill-low.md"] = local
        row = next(row for row in self.manifest["files"] if row["source"] == "pstack/skill.md")
        row["targets"]["claude"].append("claude/skill-low.md")
        new = dict(self.source)
        new["pstack/skill.md"] = ("100644", original.replace(b"last\n", b"updated last\n"))
        upstream.validate(self.manifest, self.source, self.current)
        report, candidate = self.compare(new)
        statuses = {item["target"]: item["status"] for item in report["changes"][0]["targets"]}
        for target in ("claude/skill.md", "claude/skill-low.md"):
            self.assertEqual(statuses[target], "merged-needs-review")
            self.assertEqual(candidate[target][1], original.replace(b"first\n", b"translated first\n")
                             .replace(b"last\n", b"updated last\n"))
        self.assertEqual(statuses["codex/skill.md"], "upstream-only")
        self.assertEqual(candidate["codex/skill.md"], new["pstack/skill.md"])
        self.assertEqual(self.current["claude/skill.md"], local)

    def test_compare_exposes_text_and_delete_modify_conflicts(self):
        original = self.source["pstack/skill.md"][1]
        local = ("100644", original.replace(b"first\n", b"translated first\n"))
        self.current["claude/skill.md"] = local
        new = dict(self.source)
        new["pstack/skill.md"] = ("100644", original.replace(b"first\n", b"upstream first\n"))
        report, candidate = self.compare(new)
        self.assertEqual(report["changes"][0]["targets"][0]["status"], "text-conflict")
        self.assertIn(b"<<<<<<< port", candidate["claude/skill.md"][1])
        self.assertIn(b"translated first", candidate["claude/skill.md"][1])
        self.assertIn(b"upstream first", candidate["claude/skill.md"][1])
        self.assertEqual(upstream.merge_candidate(self.source["pstack/skill.md"], local, None),
                         ("delete/modify-conflict", local))

    def test_compare_reports_additions_exclusions_and_deletions(self):
        self.current["claude/skill.md"] = text("local translation\n")
        new = dict(self.source)
        del new["pstack/skill.md"]
        new["pstack/new.md"] = text("new skill\n")
        new["pstack/excluded.md"] = text("changed cloud routine\n")
        report, candidate = self.compare(new)
        changes = {item["source"]: item for item in report["changes"]}
        self.assertEqual(changes["pstack/new.md"]["action"], "classify-new-source")
        self.assertEqual(changes["pstack/excluded.md"]["action"], "review-exclusion")
        self.assertEqual(changes["pstack/skill.md"]["kind"], "deleted")
        self.assertEqual(changes["pstack/skill.md"]["targets"][0]["status"], "delete/modify-conflict")
        self.assertEqual(candidate["claude/skill.md"], self.current["claude/skill.md"])
        self.assertNotIn("codex/skill.md", candidate)
        self.assertEqual(set(candidate), {"claude/skill.md"})
        self.assertIn(b"new skill", (self.root / "comparison/upstream.patch").read_bytes())


if __name__ == "__main__":
    unittest.main()
