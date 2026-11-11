"""Constants describing the upstream parquet artifacts and their schema.

Pinned to CloudSegmentatorResults release 0.0.1 so results are reproducible.
Bump DATA_RELEASE when the upstream publishes a new release that extends to
more IDC collections (e.g. CPTAC / CMB from the Nov 2026 Zenodo bundle).
"""

DATA_RELEASE = "0.0.1"
DATA_REPO = "ImagingDataCommons/CloudSegmentatorResults"

_BASE = (
    f"https://github.com/{DATA_REPO}/releases/download/{DATA_RELEASE}"
)

# Primary table: 28 radiomics features + QC flags + direct CT_SeriesInstanceUID.
# ~1.35 GB. DuckDB streams it over HTTPS via httpfs — no local download needed.
DATA_URL = f"{_BASE}/qual_checks_and_quantitative_measurements.parquet"

# Small sidecar (~27 MB) mapping each segmentation to its S3 / GCS object URLs.
DOWNLOAD_MAP_URL = f"{_BASE}/ct-seg-sr-map-with-series-uids-gcs-aws-ulrs.parquet"

# 28 radiomics features available per (CT scan × segmented structure).
# Column names match the parquet schema verbatim (whitespace included).
FEATURES: tuple[str, ...] = (
    "10th percentile",
    "90th percentile",
    "Elongation",
    "Energy",
    "Flatness",
    "Intensity Histogram Entropy",
    "Intensity histogram uniformity",
    "Interquartile range",
    "Kurtosis",
    "Least Axis in 3D Length",
    "Major Axis in 3D Length",
    "Maximum 3D Diameter of a Mesh",
    "Maximum grey level",
    "Mean",
    "Mean absolute deviation",
    "Median",
    "Minimum grey level",
    "Minor Axis in 3D Length",
    "Range",
    "Robust mean absolute deviation",
    "Root mean square",
    "Skewness",
    "Sphericity",
    "Surface Area of Mesh",
    "Surface to Volume Ratio",
    "Variance",
    "Volume from Voxel Summation",
    "Volume of Mesh",
)

# Non-exhaustive hint list of common TotalSegmentator structures. The parquet
# ships ~100; call Cohort().organs() to list what the current release contains.
ORGANS_HINT: tuple[str, ...] = (
    "liver", "spleen", "kidney_left", "kidney_right", "pancreas",
    "gallbladder", "stomach", "aorta", "heart", "lung_upper_lobe_left",
    "lung_upper_lobe_right", "lung_lower_lobe_left", "lung_lower_lobe_right",
    "lung_middle_lobe_right", "brain", "urinary_bladder", "prostate",
    "vertebrae_L1", "vertebrae_L2", "vertebrae_L3", "vertebrae_L4", "vertebrae_L5",
    "rib_left_1", "rib_right_1", "colon", "esophagus", "trachea",
)

# Columns used as cohort identity / join keys.
ID_COLUMNS: tuple[str, ...] = (
    "PatientID",
    "CT_SeriesInstanceUID",
    "StudyInstanceUID",
    "totalsegSegmentLabel",
    "bodyPart",
    "laterality",
    "segmentation_completeness",
)
