"""Unit tests — no network, no DuckDB required.

These verify the pieces of the library that don't need the query engine:
filter spec validation, cohort_id stability, and SQL string generation.
"""

from __future__ import annotations

import pytest

from idc_radiomics import Cohort, FEATURES


def test_features_list_matches_published_schema_length():
    """The published schema has 28 radiomics features. Guard against drift."""
    assert len(FEATURES) == 28


def test_cohort_id_is_stable_across_call_order():
    a = Cohort().organ("liver").feature("Volume from Voxel Summation", min=1_000_000)
    b = Cohort().feature("Volume from Voxel Summation", min=1_000_000).organ("liver")
    assert a.cohort_id() == b.cohort_id()
    assert a.cohort_id().startswith("idcrad:v1:")


def test_cohort_id_changes_when_organ_changes():
    assert Cohort().organ("liver").cohort_id() != Cohort().organ("spleen").cohort_id()


def test_cohort_id_changes_when_feature_bound_changes():
    a = Cohort().feature("Sphericity", min=0.7)
    b = Cohort().feature("Sphericity", min=0.8)
    assert a.cohort_id() != b.cohort_id()


def test_feature_name_must_be_in_catalog():
    with pytest.raises(ValueError):
        Cohort().feature("not a real feature", min=0)


def test_feature_without_bounds_is_a_noop():
    """Filter call with no min/max should not change cohort identity."""
    c = Cohort().organ("liver")
    assert c.feature("Sphericity").cohort_id() == c.cohort_id()


def test_chaining_returns_new_instances():
    """Cohort filter methods must be immutable (return new objects)."""
    base = Cohort()
    with_liver = base.organ("liver")
    assert base is not with_liver
    assert base.cohort_id() != with_liver.cohort_id()


def test_sql_quotes_identifiers_with_spaces():
    """Feature names include spaces — SQL must double-quote them."""
    c = Cohort().feature("Volume from Voxel Summation", min=1000)
    sql = c._build_sql(select_cols=c._select_columns(), limit=10)
    assert '"Volume from Voxel Summation"' in sql
    assert "'" not in sql.split("WHERE")[1].split('"Volume')[0]  # no stray quoting


def test_sql_escapes_single_quotes_in_organ_names():
    """Belt-and-braces check against injection via organ/patient inputs.
    Organ names are lowercased, so DROP becomes drop in the payload."""
    c = Cohort().organ("evil'; DROP TABLE x;--")
    sql = c._build_sql(select_cols=c._select_columns(), limit=1)
    assert "'evil''; drop table x;--'" in sql
    # Confirm the inner single quote is doubled, not left bare (no injection)
    assert "'evil'; drop" not in sql


def test_sql_escapes_single_quotes_in_patient_ids():
    """PatientIDs are kept verbatim, so the full injection payload lands here."""
    c = Cohort().patients("P1'; DROP TABLE x;--")
    sql = c._build_sql(select_cols=c._select_columns(), limit=1)
    assert "'P1''; DROP TABLE x;--'" in sql
    assert "'P1'; DROP" not in sql


def test_sql_only_complete_adds_qc_filter():
    c = Cohort().organ("liver").only_complete()
    sql = c._build_sql(select_cols=c._select_columns(), limit=5)
    assert "segmentation_completeness = 'complete'" in sql


def test_sql_laterality_is_lowercased():
    c = Cohort().organ("kidney_left").laterality("LEFT")
    sql = c._build_sql(select_cols=c._select_columns(), limit=5)
    assert "LOWER(laterality) = 'left'" in sql


def test_sql_patients_filter_uses_in_clause():
    c = Cohort().patients("P1", "P2", "P3")
    sql = c._build_sql(select_cols=c._select_columns(), limit=5)
    assert "PatientID IN ('P1', 'P2', 'P3')" in sql
