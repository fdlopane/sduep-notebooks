"""Check the notebooks that came out of the JupyterLite build.

Two things are verified, both of which have bitten this deployment before:

1. Every source line inside a cell keeps its trailing newline. Without it
   JupyterLite renders the whole cell as one merged line.
2. Notebooks that are meant to ship with saved cell outputs still have them.

Run as:  python tools/check_notebooks.py _output
"""

from __future__ import annotations

import json
import pathlib
import sys

# Notebooks that must arrive with their outputs intact, by file name.
MUST_KEEP_OUTPUTS = {"fifteen-zone-model-FAULTY.ipynb"}


def notebooks(root: pathlib.Path):
    for path in sorted(root.rglob("*.ipynb")):
        if "static" in path.parts or ".ipynb_checkpoints" in path.parts:
            continue
        yield path


def main() -> int:
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "_output")
    if not root.is_dir():
        print(f"ERROR: {root} is not a directory")
        return 1

    found = list(notebooks(root))
    if not found:
        print(f"ERROR: no notebooks found under {root}")
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
                problems.append(f"{path}: cell {index} stores source as a string, not a list")
                continue
            for line in source[:-1]:
                if not line.endswith("\n"):
                    broken_lines += 1

        cells_with_outputs = sum(1 for cell in cells if cell.get("outputs"))

        if broken_lines:
            problems.append(f"{path}: {broken_lines} source lines lost their trailing newline")

        if path.name in MUST_KEEP_OUTPUTS and cells_with_outputs == 0:
            problems.append(f"{path}: shipped outputs have been stripped")

        print(
            f"  {path.relative_to(root)}: "
            f"{len(cells)} cells, {cells_with_outputs} with saved outputs, "
            f"{broken_lines} newline problems"
        )

    print()
    if problems:
        for problem in problems:
            print(f"::error::{problem}")
        return 1

    print(f"All {len(found)} notebooks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
