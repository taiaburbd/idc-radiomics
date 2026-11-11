"""Basic usage of idc-radiomics.

Run from the repo root with the project venv:
    .venv/bin/python examples/basic.py

Prints a small table of large livers from NLST, plus three viewer URLs
you can open in a browser to see the actual CT scans.
"""

from idc_radiomics import Cohort

# Build a cohort: NLST CTs where TotalSegmentator segmented a "big" liver,
# QC-passed. Volume is in mm^3 — 2_000_000 mm^3 ≈ 2 litres.
big_livers = (
    Cohort()
    .organ("liver")
    .feature("Volume from Voxel Summation", min=2_000_000)
    .only_complete()  # QC-passed segmentations only
)

print(f"Cohort id: {big_livers.cohort_id()}")
print(f"Matching segments: {big_livers.count():,}\n")

# Table preview (one row per segment = one CT scan × liver)
df = big_livers.to_df(limit=5)
print(df[[
    "PatientID", "CT_SeriesInstanceUID", "bodyPart",
    "Volume from Voxel Summation", "segmentation_completeness",
]].to_string(index=False))

# Viewer URLs — click to open the CT scan in the public IDC viewer
print("\nViewer URLs:")
for url in big_livers.viewer_urls(limit=3):
    print(" ", url)
