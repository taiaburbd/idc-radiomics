# idc-radiomics

**Zero-setup access to [TotalSegmentator][ts] anatomy segmentations and radiomics features for [NCI Imaging Data Commons][idc] CT scans — without BigQuery or a Google Cloud account.**

The IDC team ships ~9.5 million organ segmentations and 28 radiomics features per segment for 125,000+ public NLST CT scans. Until now, the only way to query them was BigQuery SQL with a Google Cloud login. This library streams the same data directly from the public GitHub release via DuckDB, so you can build cohorts in three lines of Python.

```python
from idc_radiomics import Cohort

big_livers = (
    Cohort()
    .organ("liver")
    .feature("Volume from Voxel Summation", min=2_000_000)  # mm³ (≈ 2 L)
    .only_complete()
)

print(big_livers.count())           # how many CTs match
df = big_livers.to_df(limit=50)     # pandas DataFrame
for url in big_livers.viewer_urls(limit=5):
    print(url)                      # open in the IDC viewer
```

No credentials. No `gcloud auth`. No full-file download — DuckDB's httpfs extension streams just the row groups the filter needs.

---

## Install

```bash
pip install idc-radiomics
```

Requires Python 3.10+. Depends only on `duckdb`, `pandas`, `pyarrow`.

---

## What it gives you

For every public NLST CT scan with a TotalSegmentator segmentation:

| Field | Example | Notes |
|---|---|---|
| `PatientID`, `CT_SeriesInstanceUID`, `StudyInstanceUID` | — | Join keys back into IDC |
| `totalsegSegmentLabel`, `bodyPart`, `laterality` | `kidney_left`, `kidney`, `left` | ~100 TotalSegmentator structures |
| `segmentation_completeness`, QC flags | `complete` | Upstream heuristic QC |
| 28 radiomics features per segment | `Volume from Voxel Summation`, `Sphericity`, `Mean`, `Skewness`, `Maximum 3D Diameter of a Mesh`, ... | See `idc_radiomics.FEATURES` |

List every structure present in the current release:

```python
Cohort().organs()
#    organ         n
# 0  liver     124_803
# 1  spleen    124_712
# ...
```

## Reproducible cohorts

Every cohort has a stable 12-char hash:

```python
>>> big_livers.cohort_id()
'idcrad:v1:a3f2bc9e0d44'
```

Cite the id in a paper; anyone can re-build the exact same cohort by re-running the chain. The id depends only on the filter spec and the pinned data release (`DATA_RELEASE = "0.0.1"` in `catalog.py`), not on the local machine or time.

## Example cohorts

```python
# Aorta diameter outliers (possible aneurysms)
Cohort().organ("aorta").feature("Maximum 3D Diameter of a Mesh", min=40)

# Unusually elongated spleens
Cohort().organ("spleen").feature("Elongation", min=0.9)

# Both kidneys, left side only
Cohort().organ("kidney_left").laterality("left")

# Bring your own patient cohort — e.g. from idc-index
Cohort().patients("1.2.840.113654.2.55.123", "1.2.840.113654.2.55.456")
```

## Data provenance & citation

Upstream data: **ImagingDataCommons/CloudSegmentatorResults** [release 0.0.1][release] (Thiriveedhi et al., *Cloud-based large-scale curation of medical imaging data using AI segmentation*, 2024, [doi:10.21203/rs.3.rs-4351526/v1][paper]).

If you publish work using this library, please cite the IDC and the upstream dataset:

> Fedorov A. et al., *National Cancer Institute Imaging Data Commons*, RadioGraphics 43(12), 2023. https://doi.org/10.1148/rg.230180

## Design notes

- **DuckDB httpfs over a GitHub Release asset** → no local 1.35 GB download for a quick query. First query is slow (range-request index), later queries over the same connection hit the HTTP cache.
- **Chainable Cohort = lazy filter.** Nothing executes until `to_df()`, `count()`, `viewer_urls()`, or `cohort_id()`.
- **Pinned release.** `DATA_RELEASE` in `catalog.py` names the exact upstream version so `cohort_id()` is reproducible across time.

See [`DESIGN.md`](DESIGN.md) for the longer rationale.

## Status

Alpha. Target the first release at **NLST only** (CloudSegmentatorResults v0.0.1). Follow-ups: CPTAC + CMB (Zenodo Nov 2026), an MCP server, a Streamlit demo tab.

## Licence

MIT. The upstream parquet data is licensed separately — see the [CloudSegmentatorResults repo][csr].

[idc]: https://portal.imaging.datacommons.cancer.gov
[ts]: https://github.com/wasserth/TotalSegmentator
[csr]: https://github.com/ImagingDataCommons/CloudSegmentatorResults
[release]: https://github.com/ImagingDataCommons/CloudSegmentatorResults/releases/tag/0.0.1
[paper]: https://doi.org/10.21203/rs.3.rs-4351526/v1
