"""Check the course notebooks that came out of the JupyterLite build.

Two things are verified, both of which have bitten this deployment before:

1. Every source line inside a cell keeps its trailing newline. Without it
   JupyterLite renders the whole cell as one merged line.
2. Notebooks that are meant to ship with saved cell outputs still have them.

JupyterLite writes its own `jupyter-lite.ipynb` configuration stubs into the
application folders (lab/, tree/, repl/ and so on). Those are configuration
files that happen to carry the .ipynb extension, and they are skipped.

Run as:  python tools/check_notebooks.py _output
"""

from __future__ import annotations

import json
import pathlib
import sys

# Notebooks that must arrive with their outputs intact, by file name.
MUST_KEEP_OUTPUTS = {"fifteen-zone-model-FAULTY.ipynb"}

# Course notebooks that must be present in every build.
EXPECTED = {
    "environment-check.ipynb",
    "fifteen-zone-model.ipynb",
    "fifteen-zone-model-FAULTY.ipynb",
}

# JupyterLite's own configuration stubs, not notebooks.
IGNORED_NAMES = {"jupyter-lite.ipynb"}
IGNORED_PARTS = {"static", ".ipynb_checkpoints", "extensions", "build"}


def search_root(output: pathlib.Path) -> pathlib.Path:
    """Content copied in with --contents lands under _output/files."""
    files = output / "files"
    return files if files.is_dir() else output


def notebooks(root: pathlib.Path):
    for path in sorted(root.rglob("*.ipynb")):
        if path.name in IGNORED_NAMES:
            continue
        if IGNORED_PARTS.intersection(path.parts):
            continue
        yield path


def main() -> int:
    output = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "_output")
    if not output.is_dir():
        print(f"ERROR: {output} is not a directory")
        return 1

    root = search_root(output)
    print(f"Looking for course notebooks under: {root}")
    print()

    found = list(notebooks(root))
    if not found:
        print(f"::error::no course notebooks found under {root}")
        return 1

    problems = []

    for path in found:
        try:
            notebook = json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:  # noqa: BLE001
            problems.append(f"{path}: could not be parsed as JSON ({error})")
            continue

        cells = notebook.get("cells", [])
        broken_lines = 0
        for index, cell in enumerate(cells):
            source = cell.get("source", [])
            if isinstance(source, str):
                problems.append(
                    f"{path}: cell {index} stores source as a string, not a list"
                )
                continue
            for line in source[:-1]:
                if not line.endswith("\n"):
                    broken_lines += 1

        cells_with_outputs = sum(1 for cell in cells if cell.get("outputs"))

        if broken_lines:
            problems.append(
                f"{path}: {broken_lines} source lines lost their trailing newline"
            )

        if path.name in MUST_KEEP_OUTPUTS and cells_with_outputs == 0:
            problems.append(f"{path}: shipped outputs have been stripped")

        print(
            f"  {path.relative_to(root)}: "
            f"{len(cells)} cells, {cells_with_outputs} with saved outputs, "
            f"{broken_lines} newline problems"
        )

    missing = EXPECTED - {path.name for path in found}
    for name in sorted(missing):
        problems.append(f"expected notebook not present in the build: {name}")

    print()
    if problems:
        for problem in problems:
            print(f"::error::{problem}")
        return 1

    print(f"All {len(found)} course notebooks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
