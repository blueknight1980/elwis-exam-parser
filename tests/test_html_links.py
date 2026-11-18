"""HTML publication-link extraction. No network and no official question text."""

from elwis_parser.sources.html_links import publication_links


def test_publication_links_keep_only_allowed_pdf_urls() -> None:
    html = """
    <html><body>
      <a href="/DE/example/catalog.pdf?__blob=publicationFile&amp;v=1">PDF</a>
      <a href="https://www.elwis.de/DE/example/page.html">HTML</a>
      <a href="https://example.test/catalog.pdf">Other host</a>
      <a href="http://www.elwis.de/DE/example/catalog.pdf">Insecure</a>
      <a href="https://user:secret@www.elwis.de/DE/example/catalog.pdf">Credentials</a>
    </body></html>
    """
    links = publication_links(html, page_url="https://www.elwis.de/DE/example/")
    assert links == [
        "https://www.elwis.de/DE/example/catalog.pdf?__blob=publicationFile&v=1",
    ]
