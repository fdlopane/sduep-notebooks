# SDUEP notebooks

The JupyterLite deployment for the Spatial Development, Urban Economics and
Planning modules. Learners open one URL, the notebooks and data are already in
the file tree, and nothing is installed on their machine.

Live site: `https://<your-github-username>.github.io/<this-repo-name>/`

Push to `main` and the GitHub Actions workflow rebuilds and redeploys the whole
site. There is nothing else to run.

## Layout

```
content/                          everything here becomes the learner file tree
    access-check/
        environment-check.ipynb
        data/
            zones_15.csv
    tyne-and-wear/
        fifteen-zone-model.ipynb
        fifteen-zone-model-FAULTY.ipynb
        data/
            excel/
                zones_15.csv
                flows_15.csv
                trip_ends_15.csv
                cost_matrix_15.csv
                opportunities_15.csv
requirements.txt                  the three pins that define the environment
jupyter-lite.json                 site configuration, copied into the build
tools/check_notebooks.py          build-time integrity check
.github/workflows/deploy.yml      build and deploy
```

One folder per exercise, each self-contained with its own `data/` directory.
Duplicating a CSV across two exercise folders is deliberate: it costs a few
kilobytes and it means a learner can break one exercise without touching
another. Paths inside a notebook stay relative to that notebook's folder.

## Adding a new exercise

1. Create `content/<topic-name>/` with the notebook and a `data/` folder inside it.
2. Commit to `main`.
3. The workflow rebuilds. Nothing else needs re-running.

Name the folder by topic, never by module or lesson number.

## The three pins, and when to move them

| Pin | What it controls | When to move it |
| --- | --- | --- |
| `jupyterlite-core==0.8.1` | The site builder and the JupyterLab-derived interface learners see | Between cohorts only. A change here can move menus and buttons that screenshots and video lectures point at. |
| `jupyterlite-pyodide-kernel==0.8.2` | The kernel extension and its shim wheels | Only together with `jupyterlite-core`, and only within the matching minor line (`0.8.x` pairs with `0.8.x`). |
| `PYODIDE_VERSION: "314.0.1"` in `deploy.yml` | The Python interpreter and the versions of pandas, numpy, scipy and matplotlib that learners actually run | Only after re-running every notebook and confirming the saved outputs in `fifteen-zone-model-FAULTY.ipynb` still match. Pyodide `314.x` means Python 3.14. |

The Pyodide version must be the one the kernel release was built against, not
simply the newest available. `jupyterlite-pyodide-kernel` 0.8.1 moved to Pyodide
314.0.1 and 0.8.2 did not change it; 0.8.3 moved to 314.0.4 and 0.8.4 to
314.0.5. Check the kernel changelog before changing either.

Compatibility tables:
- https://pypi.org/project/jupyterlite-pyodide-kernel/
- https://jupyterlite-pyodide-kernel.readthedocs.io/en/stable/changelog.html

## If the site is too large

The workflow fails the build above 950 MB, because published GitHub Pages sites
may be no larger than 1 GB. The bundled Pyodide distribution is almost all of
the weight. If the build fails on size, the fix is to delete the package files
that this course never imports from `_output/static/pyodide/` before the upload
step, leaving `pyodide-lock.json` alone. Keep pandas, numpy, scipy, matplotlib
and their dependencies. Anything removed will return a 404 rather than falling
back to a CDN, which is the intended behaviour here.

## If Pyodide is still being fetched from a CDN

The build asserts that `_output/static/pyodide/pyodide.js` exists and that the
generated `pyodideUrl` is not an external address. If that assertion passes but
the browser network tab still shows requests to `cdn.jsdelivr.net`, replace
`jupyter-lite.json` with:

```json
{
  "jupyter-lite-schema-version": 0,
  "jupyter-config-data": {
    "litePluginSettings": {
      "@jupyterlite/pyodide-kernel-extension:kernel": {
        "pyodideUrl": "./static/pyodide/pyodide.js"
      }
    }
  }
}
```

and rebuild. Reference:
https://jupyterlite.readthedocs.io/en/stable/howto/pyodide/pyodide.html

## Building locally

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt
curl -fL -o pyodide.tar.bz2 https://github.com/pyodide/pyodide/releases/download/314.0.1/pyodide-314.0.1.tar.bz2
.venv/bin/jupyter lite build --contents content --pyodide pyodide.tar.bz2 --output-dir _output
.venv/bin/python -m http.server 8000 --directory _output
```

Then open `http://localhost:8000/lab/index.html`. Opening `_output` as a
`file://` path will not work; the site needs to be served over HTTP.
