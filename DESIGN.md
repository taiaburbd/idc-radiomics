# Design notes

## The problem

IDC ships TotalSegmentator segmentations and 28 radiomics features per
segment for ~125k public NLST CT scans. The quickest way to query them
today requires a Google Cloud account, BigQuery SQL, and a 3-table join
across `segmentations`, `quantitative_measurements`, and `dicom_all`.
That bar excludes the majority of researchers who could use the data.

Dr. Andrey Fedorov flagged this directly in a 2026-10-28 message:

> IDC offers TotalSegmentator segmentations and per-segment radiomics
> features for 100k+ CT scans. What are the challenges, if any, making
> those accessible to the users and do you have any ideas on how to
> address those?

## The insight

The upstream team already publishes the same data as parquet files on a
public GitHub release (`ImagingDataCommons/CloudSegmentatorResults` v0.0.1).
DuckDB's `httpfs` extension can read those parquet files remotely with
HTTP range requests — so a filter query downloads only the row groups and
columns it needs, not the whole 1.35 GB file.

That removes every piece of setup friction:

- **No Google Cloud account** — public GitHub release.
- **No BigQuery** — DuckDB in-process.
- **No 1.35 GB download** — httpfs streams.
- **No SQL knowledge** — a chainable Python API covers the common cases.
- **No DICOM parsing** — the parquet already pivots SR + SEG into flat rows.

## Shape of the API

```python
Cohort()                       # lazy, chainable filter
    .organ("liver")            # which structures
    .feature("Sphericity",     # which radiomics features
            min=0.7)
    .only_complete()           # QC gate
```

Four terminal methods resolve the filter:

| Call | Returns | Purpose |
|---|---|---|
| `to_df(limit)` | `pd.DataFrame` | Full rows + features |
| `count()` | `int` | Cohort size |
| `viewer_urls(limit)` | `list[str]` | Browser links to the CTs |
| `cohort_id()` | `str` | Stable short hash for citation |

## Key design choices

- **DuckDB over `requests` + `pyarrow`.** DuckDB is 50 MB to install and
  pushes predicates into parquet row-group filtering. Doing this by hand
  in pyarrow would require re-implementing predicate pushdown.
- **Lazy DuckDB import.** The whole filter-building / `cohort_id` surface
  is unit-testable without DuckDB installed. Keeps CI matrices small and
  helps on exotic CPUs that need to build DuckDB from source.
- **Immutable Cohort.** Every filter method returns a new `Cohort`. Lets
  callers share a base cohort safely and makes the hash deterministic.
- **Pin the data release.** `catalog.DATA_RELEASE` names the upstream
  version. `cohort_id` includes the data URL so the same filter against a
  newer release hashes to a different id — never silently drifts.
- **Lowercase + escape.** Organ names are lowercased on the way in;
  identifiers are double-quoted, literals are single-quoted with `'` →
  `''` escape. Belt and braces — nothing in the filter path is unchecked.

## Non-goals (for v0.1)

- **Writing radiomics features from raw DICOM.** That's upstream territory
  (pyradiomics + TotalSegmentator). This library only exposes what IDC has
  already computed.
- **Non-CT modalities.** v0.1 is NLST-only. CPTAC + CMB arrive from the
  [2026-11-02 Zenodo release](https://zenodo.org/records/23825859) —
  follow-up version.
- **Server-side cohorts.** No hosted service. If someone wants a shared
  cohort, they share the `cohort_id` + chain of filter calls, not state.

## What's next

1. **MCP server** (`idc-radiomics-mcp`) that exposes `find_cohort`,
   `get_organ_stats`, and `viewer_urls` as tools so Claude / other agents
   can answer radiomics questions without any user setup. Directly
   addresses the "accessible AI interface" question.
2. **Second data release** (CPTAC + CMB).
3. **IDC Explorer integration** — the Streamlit app in the sibling repo
   depends on this library for its new "Anatomy & Radiomics" tab.
4. **Colab cookbook** linked from the README and the IDC Discourse forum.
