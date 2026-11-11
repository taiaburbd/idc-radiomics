---
title: 'idc-radiomics: Zero-setup access to TotalSegmentator anatomy and radiomics features for NCI Imaging Data Commons CT scans'
tags:
  - Python
  - medical imaging
  - radiomics
  - DICOM
  - cancer imaging
  - NCI Imaging Data Commons
  - TotalSegmentator
authors:
  - name: Taiabur Rahman
    orcid: 0009-0004-4175-1166
    affiliation: 1
affiliations:
  - name: Independent researcher
    index: 1
date: 11 November 2026
bibliography: paper.bib
---

# Summary

The NCI Imaging Data Commons (IDC) [@fedorov2023idc] publishes TotalSegmentator
[@wasserth2023totalsegmentator] anatomy segmentations and 28 per-structure
radiomics features for more than 125,000 public NLST chest CT scans
[@thiriveedhi2024cloud]. The canonical path to these measurements is Google
BigQuery with multi-table joins across `segmentations`,
`quantitative_measurements`, and `dicom_all`. That path assumes the user has a
Google Cloud account, billing enabled, and comfort writing SQL against the IDC
schema — barriers that filter out many clinical researchers, students, and
contributors from outside the GCP ecosystem.

`idc-radiomics` is a small Python library that removes those prerequisites. It
lazily reads the same curated parquet artifact the IDC team publishes on
GitHub (`CloudSegmentatorResults` release 0.0.1) through DuckDB's `httpfs`
extension, pulling only the row groups a filter touches. Users express
cohorts through a chainable `Cohort` object — `Cohort().organ("liver")
.feature("Volume from Voxel Summation", min=2_000_000)` — and materialise them
as a pandas DataFrame, a count, or a list of IDC viewer URLs. Each filter
chain produces a short, deterministic `cohort_id` suitable for citation in
methods sections and supplementary material.

# Statement of need

Two concrete gaps motivated this library:

1. **Access friction.** IDC exposes radiomics through BigQuery, which requires a
   Google account and credentialed tooling. Published tutorials assume
   familiarity with GoogleSQL dialect joins. A common question on the IDC
   Discourse is simply how to pull per-organ volumes without standing up GCP.
2. **Download friction.** The upstream parquet is approximately 1.35 GB. Most
   exploratory questions ("which NLST scans have aortas over 40 mm?") touch
   kilobytes of that file. Downloading the full artifact wastes bandwidth and
   storage, especially in teaching and workshop settings.

`idc-radiomics` addresses both by combining a pinned public artifact with
DuckDB's HTTP range-read support. A typical cohort query transfers megabytes
rather than gigabytes, requires no credentials, and depends only on `duckdb`,
`pandas`, and `pyarrow`.

The library is deliberately narrow in scope: it does not compute radiomics
from raw DICOM (that work is upstream of the parquet artifact) and does not
attempt to replace BigQuery for users who already have it working. It targets
the exploratory, teaching, and reproducibility use cases where zero setup is
more valuable than full-schema access.

# State of the field

Two existing tools cover adjacent territory. `idc-index`
[@idc_index] is the IDC team's official Python package for scan-level
discovery and download; it does not surface the radiomics parquet and expects
the user to resolve measurements separately. `pyradiomics`
[@vangriethuysen2017pyradiomics] computes radiomics locally from DICOM/NIfTI
inputs; it is complementary rather than overlapping, since `idc-radiomics`
only consumes precomputed features. To our knowledge no existing package
offers chainable, zero-credential access to the CloudSegmentatorResults
radiomics table.

# Design

`Cohort` is lazy: method calls accumulate a predicate list and nothing
executes until a terminal method (`to_df`, `count`, `viewer_urls`,
`cohort_id`) is called. `cohort_id` is computed from the predicate list and
the pinned release string without opening a DuckDB connection, so the
identifier can be generated in CI environments or on machines without a
working DuckDB build. When a terminal method does run, the library builds a
single SQL statement against `read_parquet('https://.../CloudSegmentatorResults/.../0.0.1/...parquet')`
and relies on DuckDB's parquet predicate pushdown to minimise I/O.

The data release is pinned in `src/idc_radiomics/catalog.py`. When the
upstream bundle bumps, the pinned string changes and the same filter chain
produces a new `cohort_id` — preventing silent drift in published cohorts.

# Example

```python
from idc_radiomics import Cohort

big_livers = (
    Cohort()
    .organ("liver")
    .feature("Volume from Voxel Summation", min=2_000_000)
)

big_livers.cohort_id()     # e.g. "idcrad:v1:ca5a3209d67f"
big_livers.count()         # matching segments
df = big_livers.to_df(limit=50)
for url in big_livers.viewer_urls(limit=5):
    print(url)             # open CT in the IDC viewer
```

# Acknowledgements

The library would not exist without the open publication of the
CloudSegmentatorResults artifact by the NCI Imaging Data Commons team
[@thiriveedhi2024cloud], the TotalSegmentator model
[@wasserth2023totalsegmentator], and the NLST cohort [@nlst2011]. DuckDB's
`httpfs` extension [@raasveldt2019duckdb] makes zero-setup remote parquet
access practical.

# References
