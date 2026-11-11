# Changelog

All notable changes to `idc-radiomics` are recorded here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this
project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-11-11

Initial public release.

### Added
- Chainable `Cohort` API with `.organ(...)`, `.feature(...)`,
  `.laterality(...)`, `.only_complete()`, `.patients(...)`.
- Terminal methods: `.to_df(limit=...)`, `.count()`, `.viewer_urls(limit=...)`,
  `.cohort_id()`, and `.organs()` for structure discovery.
- Pinned catalog of 28 radiomics features and the
  `CloudSegmentatorResults` v0.0.1 parquet URL.
- Remote query engine: DuckDB `httpfs` with parquet predicate pushdown —
  no local download of the 1.35 GB artifact.
- Deterministic `cohort_id` hash (`idcrad:v1:<12 hex>`) that includes the
  pinned data release, so filter chains across releases stay distinguishable.
- Unit tests (no network, no DuckDB) and integration tests (live parquet
  over HTTPS), split by `pytest -m network`.
- GitHub Actions CI matrix across Python 3.10 / 3.11 / 3.12.

### Known limitations
- NLST-only in this release. CPTAC and CMB arrive in the follow-up once the
  [Zenodo 2026-11-02 bundle](https://zenodo.org/records/23825859) is
  wired in.
- First query from a fresh process is slow (seconds to tens of seconds)
  while DuckDB indexes the remote parquet. Subsequent queries reuse the
  connection.
- DuckDB wheels require SSE4.2+; very old virtualised CPUs will need to
  build DuckDB from source.
