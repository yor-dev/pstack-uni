import argparse
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "shared"
EFFORTS = ("low", "medium", "high", "xhigh", "max")
DESTINATIONS = {
    "claude": ROOT / "claude/skills",
    "codex": ROOT / "codex/.agents/skills",
}
MANAGED_ROOTS = (*DESTINATIONS.values(), ROOT / "claude/agents")


def render(source, client):
    output = []
    active = None
    for line in source.splitlines(keepends=True):
        if line in (b"{{#claude}}\n", b"{{#codex}}\n"):
            if active is not None:
                raise ValueError("Nested client block")
            active = line[3:-3].decode()
        elif line in (b"{{/claude}}\n", b"{{/codex}}\n"):
            if active != line[3:-3].decode():
                raise ValueError("Unmatched client block")
            active = None
        elif active is None or active == client:
            output.append(line)
    if active is not None:
        raise ValueError("Unclosed client block")
    result = b"".join(output)
    if b"{{" in result or b"}}" in result:
        raise ValueError("Unresolved template marker")
    return result


def source_files(directory):
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Source must be a regular file: {path}")
        if path.is_file():
            yield path


def expected_files():
    expected = {}
    for client, destination in DESTINATIONS.items():
        for base in (SHARED / "skills", SHARED / "clients" / client / "skills"):
            if not base.exists():
                continue
            for path in source_files(base):
                target = destination / path.relative_to(base)
                if target in expected:
                    raise ValueError(f"Duplicate generated path: {target}")
                expected[target] = (render(path.read_bytes(), client), stat.S_IMODE(path.stat().st_mode))

    templates = SHARED / "clients/claude/agents"
    agent_destination = ROOT / "claude/agents"
    for role in ("poteto-agent", "comment-sicko"):
        template = (templates / f"{role}.md").read_bytes()
        for effort in (None, *EFFORTS):
            name = role if effort is None else f"{role}-{effort}"
            fields = b"" if effort is None else f"model: inherit\neffort: {effort}\n".encode()
            data = template.replace(b"{{agent_name}}", name.encode()).replace(b"{{effort_fields}}", fields)
            expected[agent_destination / f"{name}.md"] = (data, 0o644)

    template = (templates / "general-purpose.md").read_bytes()
    for effort in EFFORTS:
        data = template.replace(b"{{agent_name}}", f"general-purpose-{effort}".encode())
        data = data.replace(b"{{effort}}", effort.encode())
        expected[agent_destination / f"general-purpose-{effort}.md"] = (data, 0o644)

    for path, (data, _) in expected.items():
        if b"{{" in data or b"}}" in data:
            raise ValueError(f"Unresolved template marker: {path}")
    return expected


def main():
    parser = argparse.ArgumentParser(description="Generate Claude and Codex skills from shared sources")
    parser.add_argument("--check", action="store_true", help="verify generated files without writing")
    args = parser.parse_args()
    expected = expected_files()
    actual = {path for root in MANAGED_ROOTS for path in root.rglob("*") if path.is_file() or path.is_symlink()}
    extras = actual - expected.keys()
    if extras:
        raise ValueError("Unexpected generated files:\n" + "\n".join(str(path.relative_to(ROOT)) for path in sorted(extras)))

    stale = []
    for path, (data, mode) in expected.items():
        if path.is_symlink() or not path.is_file() or path.read_bytes() != data or stat.S_IMODE(path.stat().st_mode) != mode:
            stale.append(path)
            if not args.check:
                if path.is_symlink():
                    raise ValueError(f"Generated path is a symlink: {path}")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                path.chmod(mode)
    if args.check and stale:
        raise ValueError("Stale generated files:\n" + "\n".join(str(path.relative_to(ROOT)) for path in sorted(stale)))
    print(f"{'Checked' if args.check else 'Generated'} {len(expected)} files")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
