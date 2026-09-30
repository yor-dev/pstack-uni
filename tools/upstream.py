import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "maintenance/upstream.json"
PLATFORMS = ("claude", "codex")
CLAUDE_PLUGIN = "claude/.claude-plugin/plugin.json"


def check_generated():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/generate.py"), "--check"],
        capture_output=True, text=True,
    )
    if result.returncode:
        raise ValueError(result.stderr.strip() or result.stdout.strip()
                         or "Generated distribution files are stale")


def git(repo, *args, data=None, allowed=(0,)):
    result = subprocess.run(
        ["git", "-C", str(repo), *args], input=data, capture_output=True
    )
    if result.returncode not in allowed:
        raise ValueError(result.stderr.decode(errors="replace") or f"git {args} failed")
    return result.stdout


def source_tree(repo, ref, scopes):
    commit = git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    records = git(repo, "ls-tree", "-rz", commit, "--", *scopes).split(b"\0")
    entries = []
    for record in filter(None, records):
        meta, path = record.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        if kind != "blob" or mode not in ("100644", "100755"):
            raise ValueError(f"Unsupported source entry: {path!r} ({mode}, {kind})")
        entries.append((path.decode(), mode, oid))
    # Batch reads use immutable Git objects, never the checkout's working files.
    blobs = git(repo, "cat-file", "--batch", data="".join(
        f"{oid}\n" for _, _, oid in entries
    ).encode())
    tree, offset = {}, 0
    for path, mode, _ in entries:
        end = blobs.index(b"\n", offset)
        size = int(blobs[offset:end].split()[-1])
        tree[path] = (mode, blobs[end + 1:end + 1 + size])
        offset = end + size + 2
    return commit, tree


def disk_tree(root):
    tree = {}
    for platform in PLATFORMS:
        for path in sorted((root / platform).rglob("*")):
            if path.is_symlink():
                raise ValueError(f"Symlink requires explicit support: {path}")
            if path.is_file():
                mode = "100755" if path.stat().st_mode & 0o111 else "100644"
                tree[path.relative_to(root).as_posix()] = (mode, path.read_bytes())
    return tree


def validate(manifest, source, current):
    names = [row["source"] for row in manifest["files"]]
    if len(names) != len(set(names)) or set(names) != set(source):
        raise ValueError(f"Source inventory mismatch: {sorted(set(names) ^ set(source))}")
    version = json.loads(source["pstack/.cursor-plugin/plugin.json"][1])["version"]
    if version != manifest["version"]:
        raise ValueError(f"Version mismatch: source={version}, manifest={manifest['version']}")
    targets = []
    for row in manifest["files"]:
        for platform in PLATFORMS:
            paths = row["targets"][platform]
            if not paths and not row.get("excluded", {}).get(platform):
                raise ValueError(f"Missing exclusion reason: {row['source']} / {platform}")
            if any(not path.startswith(platform + "/") for path in paths):
                raise ValueError(f"Wrong destination platform: {row['source']}")
            targets.extend(paths)
    for addition in manifest["additions"]:
        if not addition["reason"]:
            raise ValueError("Missing local addition reason")
        targets.append(addition["target"])
    for path in targets:
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise ValueError(f"Invalid destination: {path}")
    if len(targets) != len(set(targets)) or set(targets) != set(current):
        raise ValueError(f"Destination inventory mismatch: {sorted(set(targets) ^ set(current))}")


def base_tree(manifest, source, platform):
    return {target: source[row["source"]]
            for row in manifest["files"]
            for target in row["targets"][platform]}


def write_tree(root, tree):
    for name, (mode, content) in tree.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        path.chmod(int(mode[-3:], 8))


def plugin_entry(entry, version=None):
    if entry is None:
        return None
    mode, content = entry
    metadata = json.loads(content)
    del metadata["version"]
    if version is not None:
        metadata["version"] = version
    return mode, (json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def patch_tree(tree):
    # The distribution version is owned by plugin.json, not the upstream patches.
    return {name: plugin_entry(entry) if name == CLAUDE_PLUGIN else entry
            for name, entry in tree.items()}


def patch_for(base, current):
    base, current = patch_tree(base), patch_tree(current)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        git(root, "init", "-q")
        git(root, "config", "core.fileMode", "true")
        git(root, "config", "core.autocrlf", "false")
        write_tree(root, base)
        git(root, "add", "-f", ".")
        for name in base.keys() - current.keys():
            (root / name).unlink()
        write_tree(root, current)
        git(root, "add", "-N", "-f", ".")
        return git(root, "diff", "--binary", "--full-index", "--no-renames",
                   "--no-ext-diff", "--no-textconv")


def check_patches(manifest, source, current):
    for platform in PLATFORMS:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git(root, "init", "-q")
            git(root, "config", "core.autocrlf", "false")
            write_tree(root, patch_tree(base_tree(manifest, source, platform)))
            patch = (ROOT / "maintenance/patches" / f"{platform}.patch").read_bytes()
            if patch:
                git(root, "apply", "--binary", "--whitespace=nowarn", "-", data=patch)
            expected = patch_tree({p: v for p, v in current.items() if p.startswith(platform + "/")})
            actual = disk_tree(root)
            if actual != expected:
                changed = sorted(p for p in actual.keys() | expected.keys()
                                 if actual.get(p) != expected.get(p))
                raise ValueError(f"{platform} patch is stale: {changed}")
            print(f"{platform}: patch verifies {len(expected)} files and executable modes"
                  " (distribution version excluded)")


def merge_candidate(old, local, new):
    if local == old or local == new:
        return "upstream-only", new
    if new == old:
        return "port-only", local
    if new is None:
        return "delete/modify-conflict", local
    old_mode, old_data = old
    local_mode, local_data = local
    new_mode, new_data = new
    if any(b"\0" in data for data in (old_data, local_data, new_data)):
        return "binary-review", local
    with tempfile.TemporaryDirectory() as tmp:
        paths = [Path(tmp) / name for name in ("port", "old-upstream", "new-upstream")]
        for path, data in zip(paths, (local_data, old_data, new_data)):
            path.write_bytes(data)
        result = subprocess.run(
            ["git", "merge-file", "-p", "--diff3", "-L", "port", "-L", "old-upstream",
             "-L", "new-upstream", *map(str, paths)], capture_output=True
        )
        if result.returncode not in range(128):
            raise ValueError(result.stderr.decode(errors="replace"))
    mode = new_mode if local_mode == old_mode else local_mode
    return ("text-conflict" if result.returncode else "merged-needs-review"), (mode, result.stdout)


def compare(repo, manifest, old, current, ref, out):
    commit, new = source_tree(repo, ref, manifest["scopes"])
    out.mkdir(parents=True, exist_ok=False)
    candidates = dict(current)
    rows = {row["source"]: row for row in manifest["files"]}
    report = {"from": manifest["commit"], "to": commit,
              "version": json.loads(new["pstack/.cursor-plugin/plugin.json"][1])["version"],
              "changes": []}
    for name in sorted(old.keys() | new.keys()):
        if old.get(name) == new.get(name):
            continue
        change = {"source": name, "kind": "added" if name not in old else
                  "deleted" if name not in new else "modified", "targets": []}
        if name not in rows:
            change["action"] = "classify-new-source"
        else:
            for platform in PLATFORMS:
                for target in rows[name]["targets"][platform]:
                    entries = (old[name], current[target], new.get(name))
                    if target == CLAUDE_PLUGIN:
                        # Upstream releases must not change the distribution's version.
                        version = json.loads(current[target][1])["version"]
                        entries = tuple(plugin_entry(entry, version) for entry in entries)
                    status, value = merge_candidate(*entries)
                    change["targets"].append({"target": target, "status": status})
                    if value is None:
                        candidates.pop(target)
                    else:
                        candidates[target] = value
            if not change["targets"]:
                change["action"] = "review-exclusion"
        report["changes"].append(change)
    write_tree(out / "candidate", candidates)
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (out / "upstream.patch").write_bytes(git(
        repo, "diff", "--binary", "--no-ext-diff", "--no-textconv", "--no-renames",
        manifest["commit"], commit, "--", *manifest["scopes"]
    ))
    print(f"{len(report['changes'])} upstream changes; review {out / 'report.json'}")
    print("Candidate only: resolve conflicts, classify additions/deletions, and review translation before adoption.")


def main():
    parser = argparse.ArgumentParser(description="Maintain explicit pstack port patches.")
    parser.add_argument("command", choices=("refresh", "check", "compare"))
    parser.add_argument("--source", type=Path, required=True, help="Local cursor/plugins Git clone")
    parser.add_argument("--to", help="New upstream commit/ref, required for compare")
    parser.add_argument("--out", type=Path, help="New candidate directory, required for compare")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    commit, source = source_tree(args.source, manifest["commit"], manifest["scopes"])
    if commit != manifest["commit"]:
        raise ValueError("Manifest must pin the full commit ID")
    current = disk_tree(ROOT)
    validate(manifest, source, current)
    check_generated()
    if args.command == "refresh":
        patches = {platform: patch_for(base_tree(manifest, source, platform), {
            p: v for p, v in current.items() if p.startswith(platform + "/")
        }) for platform in PLATFORMS}
        for platform, patch in patches.items():
            (ROOT / "maintenance/patches" / f"{platform}.patch").write_bytes(patch)
        check_patches(manifest, source, current)
    elif args.command == "check":
        check_patches(manifest, source, current)
    else:
        if not args.to or not args.out:
            parser.error("compare requires --to and --out")
        check_patches(manifest, source, current)
        compare(args.source, manifest, source, current, args.to, args.out)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        raise SystemExit(str(error))
