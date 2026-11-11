"""
idc-radiomics — Query TotalSegmentator anatomy & radiomics for IDC CT scans
without BigQuery or a Google Cloud account.

Data source:
    ImagingDataCommons/CloudSegmentatorResults release 0.0.1
    (9.5M segmentations over 125k NLST CT scans, 28 radiomics features each).

Quick start:

    from idc_radiomics import Cohort

    livers = Cohort().organ("liver").feature("Volume from Voxel Summation", min=2_000_000)
    df = livers.to_df(limit=50)
    for url in livers.viewer_urls(limit=5):
        print(url)
"""

from .cohort import Cohort
from .catalog import DATA_URL, FEATURES, ORGANS_HINT

__all__ = ["Cohort", "DATA_URL", "FEATURES", "ORGANS_HINT"]
__version__ = "0.1.0"
