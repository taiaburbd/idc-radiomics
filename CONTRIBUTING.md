# Contributing to idc-radiomics

Thanks for your interest. This project exists to lower the setup bar for
NCI Imaging Data Commons (IDC) radiomics. Contributions that keep that bar
low — fewer dependencies, clearer docs, more collections, better tests —
are all welcome.

## How to report a bug

Open a [GitHub issue](https://github.com/taiaburbd/idc-radiomics/issues)
with:

- the `idc-radiomics` version (`python -c "import idc_radiomics; print(idc_radiomics.__version__)"`)
- a minimal `Cohort(...)` chain that reproduces the problem
- the full error traceback and whether it happened on the first query or a
  later one (first queries over `httpfs` are expected to be slow)

If the bug is in the upstream parquet (wrong feature value, missing organ),
please file it with
[CloudSegmentatorResults](https://github.com/ImagingDataCommons/CloudSegmentatorResults/issues)
instead — this library is a thin wrapper and will inherit the fix.

## How to request a feature

Open an issue and describe the cohort you were trying to build. Concrete
examples are more useful than abstract requests — "I want to filter by
laterality AND voxel spacing" tells us what the SQL needs to do.

## How to get help

- **Usage questions** — [GitHub Discussions](https://github.com/taiaburbd/idc-radiomics/discussions)
  (enable on first question) or the [IDC Discourse forum](https://discourse.canceridc.dev).
- **Questions about IDC data itself** — IDC Discourse is the right venue.
- **Private / security issues** — email taiaburbd@gmail.com.

## How to contribute code

1. Fork and clone the repo.
2. Create a feature branch: `git checkout -b feature/short-description`.
3. Install the dev extras:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   ```
4. Run the unit tests (no network needed):
   ```bash
   pytest -m "not network" -v
   ```
5. If your change touches SQL generation or the remote query path, also run
   integration tests:
   ```bash
   pytest -m network -v
   ```
6. Open a pull request against `main`. Please include:
   - what the change does and why
   - a test that would have failed before the change
   - a note if you changed any public API (methods on `Cohort`, exported
     names)

## Code style

- Python 3.10+ features are fine (`from __future__ import annotations` is
  used at the top of each module for forward refs).
- No new runtime dependencies without discussion — the "zero setup"
  promise depends on the current short list (`duckdb`, `pandas`,
  `pyarrow`).
- Keep public API surface small. Prefer adding filter methods to `Cohort`
  over adding free functions.
- Comments explain *why*, not *what*. Well-named identifiers already say
  *what*.

## Release process (maintainer notes)

See `CHANGELOG.md` for the version history. Releases are cut by:

1. Bumping `__version__` in `src/idc_radiomics/__init__.py` and the
   `version` field in `pyproject.toml`.
2. Updating `CHANGELOG.md` with the new section.
3. Tagging `vX.Y.Z` and pushing the tag — CI builds the sdist/wheel and
   publishes to PyPI via trusted publishing, and Zenodo mints a DOI if
   GitHub integration is enabled.

## Code of conduct

Be kind. Assume good faith. Keep discussions focused on the software and
the data. We follow the spirit of the
[Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/);
report unacceptable behavior to taiaburbd@gmail.com.
