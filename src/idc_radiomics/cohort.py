"""Cohort — the main API. A lazy, chainable query over the TotalSegmentator
radiomics parquet that resolves to a pandas DataFrame plus viewer URLs.

Why DuckDB over HTTPS: the parquet is 1.35 GB. With httpfs range reads, DuckDB
pulls only the column + row groups it needs for the current filter — so a
typical cohort query transfers a few MB, not 1.35 GB. Users get zero-setup
access without downloading the file or opening a BigQuery account.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from .catalog import DATA_URL, FEATURES, ID_COLUMNS
from .urls import viewer_url

if TYPE_CHECKING:
    import duckdb
    import pandas as pd


def _quote_ident(name: str) -> str:
    """Quote an identifier that contains spaces or unusual characters."""
    return '"' + name.replace('"', '""') + '"'


def _quote_literal(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


@dataclass(frozen=True)
class _FeatureFilter:
    name: str
    min: Optional[float] = None
    max: Optional[float] = None

    def sql(self) -> str:
        col = _quote_ident(self.name)
        parts = []
        if self.min is not None:
            parts.append(f"{col} >= {float(self.min)}")
        if self.max is not None:
            parts.append(f"{col} <= {float(self.max)}")
        return " AND ".join(parts)


@dataclass
class Cohort:
    """A lazy filter over the TotalSegmentator radiomics parquet.

    Each method returns a new Cohort so filters can be chained. Nothing runs
    until you call to_df(), count(), viewer_urls() or cohort_id().
    """

    data_url: str = DATA_URL
    _organs: tuple[str, ...] = field(default_factory=tuple)
    _laterality: Optional[str] = None
    _features: tuple[_FeatureFilter, ...] = field(default_factory=tuple)
    _only_complete: bool = False
    _patients: tuple[str, ...] = field(default_factory=tuple)

    # ---- filter builders -------------------------------------------------

    def organ(self, *names: str) -> "Cohort":
        """Match one or more TotalSegmentator structure labels.

        Use the `totalsegSegmentLabel` column (fine-grained, e.g. `liver`,
        `kidney_left`, `vertebrae_L3`). Case-insensitive.
        """
        if not names:
            return self
        lowered = tuple(n.lower() for n in names)
        return self._replace(_organs=self._organs + lowered)

    def laterality(self, side: str) -> "Cohort":
        """Match `left` or `right` (for paired structures)."""
        return self._replace(_laterality=side.lower())

    def feature(
        self,
        name: str,
        min: Optional[float] = None,
        max: Optional[float] = None,
    ) -> "Cohort":
        """Filter by a radiomics feature value range.

        `name` must match one of `idc_radiomics.FEATURES` verbatim (column
        names include spaces, e.g. "Volume from Voxel Summation").
        """
        if name not in FEATURES:
            raise ValueError(
                f"Unknown feature: {name!r}. See idc_radiomics.FEATURES for the full list."
            )
        if min is None and max is None:
            return self
        f = _FeatureFilter(name=name, min=min, max=max)
        return self._replace(_features=self._features + (f,))

    def only_complete(self) -> "Cohort":
        """Keep only segmentations the upstream QC marked pass
        (segmentation_completeness = 'pass' in CloudSegmentatorResults 0.0.1)."""
        return self._replace(_only_complete=True)

    def patients(self, *patient_ids: str) -> "Cohort":
        """Restrict to specific PatientIDs."""
        return self._replace(_patients=self._patients + tuple(patient_ids))

    # ---- execution -------------------------------------------------------

    def to_df(self, limit: Optional[int] = 1000) -> "pd.DataFrame":
        """Run the cohort query and return a DataFrame (one row per segment).

        Pass `limit=None` to lift the cap. The default 1000 protects against
        accidentally pulling millions of rows.
        """
        sql = self._build_sql(select_cols=self._select_columns(), limit=limit)
        return _connect().execute(sql).fetchdf()

    def count(self) -> int:
        """Total matching segments (one per CT × structure)."""
        sql = self._build_sql(select_cols=("COUNT(*) AS n",), limit=None)
        return int(_connect().execute(sql).fetchone()[0])

    def viewer_urls(self, limit: int = 20) -> list[str]:
        """Return public IDC viewer URLs for the first `limit` distinct CT
        series in the cohort. Opens in a browser, no login."""
        sql = self._build_sql(
            select_cols=("DISTINCT StudyInstanceUID", "CT_SeriesInstanceUID"),
            limit=limit,
        )
        rows = _connect().execute(sql).fetchall()
        return [viewer_url(study, series) for study, series in rows]

    def cohort_id(self) -> str:
        """Stable short hash of the filter spec. Use to cite the exact cohort
        in a paper or re-create it later: `Cohort(...).cohort_id()` is the
        same bytes every time for the same filters."""
        spec = {
            "data_url": self.data_url,
            "organs": sorted(self._organs),
            "laterality": self._laterality,
            "features": [
                {"name": f.name, "min": f.min, "max": f.max}
                for f in self._features
            ],
            "only_complete": self._only_complete,
            "patients": sorted(self._patients),
        }
        payload = json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()
        digest = hashlib.sha256(payload).hexdigest()[:12]
        return f"idcrad:v1:{digest}"

    def organs(self, limit: int = 200) -> "pd.DataFrame":
        """List the structure labels present in the dataset, with counts.

        Useful discovery call — the ORGANS_HINT constant is non-exhaustive.
        """
        sql = (
            f"SELECT totalsegSegmentLabel AS organ, COUNT(*) AS n "
            f"FROM read_parquet({_quote_literal(self.data_url)}) "
            f"GROUP BY organ ORDER BY n DESC LIMIT {int(limit)}"
        )
        return _connect().execute(sql).fetchdf()

    # ---- internals -------------------------------------------------------

    def _select_columns(self) -> tuple[str, ...]:
        cols = list(ID_COLUMNS)
        cols.extend(f.name for f in self._features)
        return tuple(_quote_ident(c) for c in cols)

    def _build_sql(
        self, select_cols: tuple[str, ...], limit: Optional[int]
    ) -> str:
        where = self._where()
        where_sql = f"WHERE {where}" if where else ""
        lim_sql = f"LIMIT {int(limit)}" if limit else ""
        select_sql = ", ".join(select_cols)
        return (
            f"SELECT {select_sql} "
            f"FROM read_parquet({_quote_literal(self.data_url)}) "
            f"{where_sql} {lim_sql}"
        )

    def _where(self) -> str:
        parts: list[str] = []
        if self._organs:
            values = ", ".join(_quote_literal(o) for o in self._organs)
            parts.append(f"LOWER(totalsegSegmentLabel) IN ({values})")
        if self._laterality:
            parts.append(f"LOWER(laterality) = {_quote_literal(self._laterality)}")
        if self._only_complete:
            parts.append("segmentation_completeness = 'pass'")
        if self._patients:
            values = ", ".join(_quote_literal(p) for p in self._patients)
            parts.append(f"PatientID IN ({values})")
        for f in self._features:
            parts.append(f.sql())
        return " AND ".join(parts)

    def _replace(self, **changes) -> "Cohort":
        from dataclasses import replace

        return replace(self, **changes)


# ---- shared DuckDB connection ------------------------------------------

_CONN = None  # type: ignore[var-annotated]


def _connect():
    """One in-process DuckDB connection with httpfs loaded. Reusing it
    across calls keeps the HTTP range cache warm between queries.

    DuckDB is imported lazily so the rest of the module (filter building,
    cohort_id, SQL string generation) can be unit-tested without it.
    """
    global _CONN
    if _CONN is None:
        import duckdb  # local import — see docstring

        _CONN = duckdb.connect()
        _CONN.execute("INSTALL httpfs; LOAD httpfs;")
    return _CONN
