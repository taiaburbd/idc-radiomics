# idc-radiomics

**Query [NCI Imaging Data Commons](https://portal.imaging.datacommons.cancer.gov) (IDC) CT radiomics and [TotalSegmentator](https://github.com/wasserth/TotalSegmentator) segmentations from Python — no BigQuery, no Google Cloud account, no 1.35 GB download.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: readable API](https://img.shields.io/badge/API-chainable%20Cohort-informational)](#quick-start)

idc-radiomics is a small open-source library for **cancer imaging researchers**, **radiomics** workflows, and **IDC** users who want to explore **NLST** chest CT cohorts without standing up BigQuery. It streams the public [CloudSegmentatorResults](https://github.com/ImagingDataCommons/CloudSegmentatorResults) parquet release through **DuckDB** over HTTPS, so you filter millions of organ-level measurements in plain Python and jump straight to the IDC viewer for the scans you care about.

---

## Who this helps

| You want to… | idc-radiomics gives you… |
|---|---|
| Find NLST CTs with large livers, wide aortas, or odd-shaped spleens | Chainable filters on **28 radiomics features** per structure |
| Skip GCP setup and SQL joins across IDC BigQuery tables | One `pip install`, zero credentials |
| Share an exact patient/segment list in a paper or with a collaborator | A stable **`cohort_id`** hash from your filter chain |
| Open the underlying DICOM in the browser | **`viewer_urls()`** → public IDC viewer links |

**Not a fit (yet):** writing radiomics from raw DICOM, non-CT modalities, or collections beyond NLST in v0.1. See [Roadmap](#roadmap).

---

## Quick start

```bash
pip install idc-radiomics
```

```python
from idc_radiomics import Cohort

# Large livers on NLST CTs (~2 L in mm³). Volume is in mm³.
big_livers = (
    Cohort()
    .organ("liver")
    .feature("Volume from Voxel Summation", min=2_000_000)
)

print(big_livers.count())              # matching segments (CT × structure)
print(big_livers.cohort_id())          # cite this in papers / supplements

df = big_livers.to_df(limit=50)        # pandas DataFrame
for url in big_livers.viewer_urls(limit=5):
    print(url)                         # open CT in the IDC viewer
```

**First query note:** DuckDB indexes the remote parquet over HTTP. The first call on a machine can take tens of seconds; later calls on the same process reuse the connection and cache.

**Requirements:** Python 3.10+. Dependencies: `duckdb`, `pandas`, `pyarrow` only.

---

## Why not BigQuery?

IDC already exposes TotalSegmentator segmentations and per-segment radiomics for **125,000+** public NLST CT scans (~**9.5M** structure rows). The canonical path today is **Google BigQuery** plus multi-table joins (`segmentations`, `quantitative_measurements`, `dicom_all`). That works well if you live in GCP; many labs do not.

idc-radiomics reads the **same curated parquet** the IDC team publishes on GitHub ([release 0.0.1](https://github.com/ImagingDataCommons/CloudSegmentatorResults/releases/tag/0.0.1)). DuckDB’s **httpfs** extension fetches only the row groups your filter needs, so a typical cohort query moves megabytes, not the full **~1.35 GB** file.

---

## Install & develop

```bash
# PyPI (when published)
pip install idc-radiomics

# From source
git clone https://github.com/taiaburbd/idc-radiomics.git
cd idc-radiomics
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Unit tests (no network)
pytest -m "not network"

# Integration tests (live parquet over HTTPS)
pytest -m network
```

Run the bundled example from the repo root:

```bash
python examples/basic.py
```

---

## API at a glance

`Cohort` is a **lazy** filter: nothing runs until you call `to_df()`, `count()`, `viewer_urls()`, or `cohort_id()`.

| Method | What it does |
|---|---|
| `.organ("liver", "spleen", …)` | Match [TotalSegmentator](https://github.com/wasserth/TotalSegmentator) labels (~100 structures in the release) |
| `.feature(name, min=…, max=…)` | Filter on radiomics columns (names must match `idc_radiomics.FEATURES` exactly) |
| `.laterality("left")` / `"right"` | Paired structures |
| `.only_complete()` | Keep upstream QC-passed rows (`segmentation_completeness`) |
| `.patients("id1", "id2", …)` | Restrict to PatientIDs (e.g. from [idc-index](https://github.com/ImagingDataCommons/idc-index)) |
| `.organs()` | Discover structures and counts in the current release |

| Terminal call | Returns |
|---|---|
| `to_df(limit=1000)` | `pandas.DataFrame` — ID columns + any features used in `.feature()` |
| `count()` | Number of matching segments |
| `viewer_urls(limit=20)` | IDC viewer URLs for distinct studies/series |
| `cohort_id()` | Reproducible id, e.g. `idcrad:v1:a3f2bc9e0d44` |

List all **28 radiomics feature** names:

```python
from idc_radiomics import FEATURES
print(len(FEATURES))  # 28
```

Discover what’s in the dataset:

```python
Cohort().organs()
#    organ         n
# 0  liver     124_803
# 1  spleen    124_712
# ...
```

---

## What’s in each row?

For every NLST CT with a TotalSegmentator segmentation in release **0.0.1**:

| Field | Example | Notes |
|---|---|---|
| `PatientID`, `CT_SeriesInstanceUID`, `StudyInstanceUID` | DICOM UIDs | Join keys back into IDC |
| `totalsegSegmentLabel`, `bodyPart`, `laterality` | `kidney_left`, `kidney`, `left` | Structure identity |
| `segmentation_completeness` | `pass`, `fail` | Upstream heuristic QC |
| Radiomics (28 columns) | `Volume from Voxel Summation`, `Sphericity`, `Mean`, `Maximum 3D Diameter of a Mesh`, … | Full list: `FEATURES` |

---

## Example cohorts

Copy, tweak thresholds, cite `cohort_id()` in your methods section.

```python
from idc_radiomics import Cohort

# Possible aortic aneurysm screening signal (millimeters; validate clinically)
Cohort().organ("aorta").feature("Maximum 3D Diameter of a Mesh", min=40)

# Morphology outlier spleens
Cohort().organ("spleen").feature("Elongation", min=0.9)

# Left kidney only
Cohort().organ("kidney_left").laterality("left")

# Intersect with your own patient list
Cohort().patients("1.2.840.113654.2.55.123", "1.2.840.113654.2.55.456")
```

---

## Reproducible research

Every filter chain gets a short, stable hash:

```python
>>> Cohort().organ("liver").feature("Volume from Voxel Summation", min=2_000_000).cohort_id()
'idcrad:v1:ca5a3209d67f'
```

The id depends on your filter spec and the pinned release (`DATA_RELEASE = "0.0.1"` in `src/idc_radiomics/catalog.py`), not on your laptop or the clock. When the upstream bundle bumps, the same filters produce a **new** id — so comparisons across releases stay honest.

---

## How it works (short)

1. **Pinned artifact** — `qual_checks_and_quantitative_measurements.parquet` on [CloudSegmentatorResults 0.0.1](https://github.com/ImagingDataCommons/CloudSegmentatorResults/releases/tag/0.0.1).
2. **DuckDB + httpfs** — `read_parquet('https://…')` with HTTP range reads.
3. **Chainable SQL** — your `Cohort` builds a `WHERE` clause; predicates push into parquet where DuckDB can.
4. **Lazy DuckDB import** — filter building and `cohort_id()` work without DuckDB loaded (handy for CI and unit tests).

More rationale: [`DESIGN.md`](DESIGN.md).

---

## Citations & data provenance

**Upstream segmentation + radiomics table:**  
[ImagingDataCommons/CloudSegmentatorResults](https://github.com/ImagingDataCommons/CloudSegmentatorResults) release **0.0.1** — Thiriveedhi et al., *Cloud-based large-scale curation of medical imaging data using AI segmentation*, 2024 ([doi:10.21203/rs.3.rs-4351526/v1](https://doi.org/10.21203/rs.3.rs-4351526/v1)).

**IDC platform (please cite if you use this library in publication):**

> Fedorov A. et al., *National Cancer Institute Imaging Data Commons*, RadioGraphics 43(12), 2023. https://doi.org/10.1148/rg.230180

Upstream parquet licensing is separate from this repo — see the [CloudSegmentatorResults repository](https://github.com/ImagingDataCommons/CloudSegmentatorResults).

---

## Community & contributing

This project exists to **lower the bar** for IDC radiomics and TotalSegmentator exploration. Help is welcome.

- **Bug or wrong docs?** [Open an issue](https://github.com/taiaburbd/idc-radiomics/issues).
- **New cohort patterns or collection support?** PRs against `src/idc_radiomics/` + tests in `tests/`.
- **Questions about IDC data itself?** [IDC forum](https://discourse.canceridc.dev) and [portal docs](https://learn.canceridc.dev/).

**Troubleshooting**

| Symptom | Likely cause |
|---|---|
| First query slow | Remote parquet indexing over HTTPS; normal |
| `Unknown feature` | Use exact strings from `idc_radiomics.FEATURES` (spaces matter) |
| DuckDB `Illegal instruction` on old VMs | Install a DuckDB wheel built for your CPU, or build from source |
| Empty cohort | Loosen filters; check `.organs()` for label spelling |

---

## Roadmap

**Now (alpha):** NLST only, CloudSegmentatorResults **v0.0.1**, Python API.

**Next:** CPTAC + CMB from the Nov 2026 Zenodo bundle, optional MCP server, Streamlit demo tab.

---

## License

MIT for this library. See [LICENSE](LICENSE).

---

## Links

| Resource | URL |
|---|---|
| IDC portal | https://portal.imaging.datacommons.cancer.gov |
| CloudSegmentatorResults data | https://github.com/ImagingDataCommons/CloudSegmentatorResults |
| TotalSegmentator | https://github.com/wasserth/TotalSegmentator |
| This repo | https://github.com/taiaburbd/idc-radiomics |
