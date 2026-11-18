"""Source registry, local files, and guarded downloads."""

from elwis_parser.sources.downloader import download_pdf, validate_download_url
from elwis_parser.sources.html_links import publication_links
from elwis_parser.sources.local import load_local_pdf
from elwis_parser.sources.registry import (
    ALLOWED_DOWNLOAD_HOSTS,
    EXAMINATIONS,
    VERIFIED_SOURCES,
    ExaminationSpec,
    SourceRecord,
    get_examination,
    get_source,
    normalize_exam_id,
)

__all__ = [
    "ALLOWED_DOWNLOAD_HOSTS",
    "EXAMINATIONS",
    "VERIFIED_SOURCES",
    "ExaminationSpec",
    "SourceRecord",
    "download_pdf",
    "get_examination",
    "get_source",
    "load_local_pdf",
    "normalize_exam_id",
    "publication_links",
    "validate_download_url",
]
