"""Integration tests — hit the live parquet over HTTPS (DuckDB httpfs).

Skip with `pytest -m 'not network'` to run only unit tests.
A failure here usually means (a) the upstream release moved or (b) network
is unavailable. Requires a CPU with SSE4.2+ for DuckDB wheels.
"""

from __future__ import annotations

import pytest

from idc_radiomics import Cohort


pytestmark = pytest.mark.network  # mark whole module as network-dependent


def test_organs_discovery_returns_rows():
    """Confirms httpfs streaming works end-to-end."""
    df = Cohort().organs(limit=5)
    assert len(df) == 5
    assert set(df.columns) == {"organ", "n"}
    assert (df["n"] > 0).all()


def test_liver_volume_cohort_returns_rows():
    """The canonical example query — big livers in NLST."""
    c = (
        Cohort()
        .organ("liver")
        .feature("Volume from Voxel Summation", min=2_000_000)
        .only_complete()
    )
    df = c.to_df(limit=5)
    assert len(df) > 0
    assert "CT_SeriesInstanceUID" in df.columns
    assert "Volume from Voxel Summation" in df.columns
    assert (df["Volume from Voxel Summation"] >= 2_000_000).all()
    assert df["bodyPart"].str.lower().eq("liver").all() or \
           df["totalsegSegmentLabel"].str.lower().eq("liver").all()


def test_viewer_urls_are_well_formed():
    urls = Cohort().organ("liver").viewer_urls(limit=3)
    assert len(urls) == 3
    assert all(u.startswith("https://viewer.imaging.datacommons.cancer.gov/") for u in urls)
    assert all("StudyInstanceUIDs=" in u for u in urls)
