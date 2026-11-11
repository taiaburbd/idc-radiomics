"""IDC viewer link helpers. Matches the public IDC Portal viewer URL scheme
(no auth, opens a public CT series in the browser)."""

VIEWER_BASE = "https://viewer.imaging.datacommons.cancer.gov"


def viewer_url(study_uid: str, series_uid: str) -> str:
    """URL that opens a CT series in the public IDC OHIF viewer."""
    return (
        f"{VIEWER_BASE}/v3/viewer/"
        f"?StudyInstanceUIDs={study_uid}"
        f"&initialSeriesInstanceUID={series_uid}"
    )
