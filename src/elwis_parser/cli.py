"""Command-line interface for the ELWIS exam parser."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Annotated

import pymupdf
import typer

from elwis_parser import __version__
from elwis_parser.config import Settings
from elwis_parser.exceptions import ElwisParserError, UsageError
from elwis_parser.logging_config import configure_logging
from elwis_parser.pdf.backend import open_pdf
from elwis_parser.pipeline import export_csv, extract_pdf, inspect_pdf, parse_pdf, validate_export
from elwis_parser.sources.downloader import download_pdf
from elwis_parser.sources.local import load_local_pdf
from elwis_parser.sources.registry import EXAMINATIONS, VERIFIED_SOURCES, get_source
from elwis_parser.utils.hashing import sha256_file

app = typer.Typer(
    help="Extract, validate, and export official ELWIS sport-boat exam catalogs.",
    no_args_is_help=True,
)
sources_app = typer.Typer(help="List and check catalog source records.")
app.add_typer(sources_app, name="sources")


def _settings() -> Settings:
    return Settings.from_env()


@contextmanager
def _handled() -> Iterator[None]:
    """Convert expected failures into process exit codes."""
    try:
        yield
    except ElwisParserError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=exc.exit_code) from None
    except Exception as exc:
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            typer.echo(f"Unexpected error: {exc}", err=True)
            raise
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise typer.Exit(code=3) from None


@app.callback()
def main(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable debug logging.")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Hide informational logs.")] = False,
) -> None:
    """Extract, validate, and export official ELWIS sport-boat exam catalogs."""
    configure_logging(verbose=verbose, quiet=quiet)


@app.command()
def version() -> None:
    """Show the parser version."""
    typer.echo(f"elwis-exam-parser {__version__}")


@app.command()
def inspect(
    pdf: Annotated[Path, typer.Argument(help="PDF file to inspect.")],
    page: Annotated[
        int | None, typer.Option("--page", help="1-based page to show in detail.")
    ] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Print JSON instead of text.")] = False,
    render_dir: Annotated[
        Path | None,
        typer.Option("--render-dir", help="Write a PNG preview. Requires --page."),
    ] = None,
) -> None:
    """Inspect PDF structure without interpreting questions."""
    with _handled():
        typer.echo(inspect_pdf(pdf, settings=_settings(), page=page, as_json=as_json))
        if render_dir is not None:
            if page is None:
                raise UsageError("--render-dir requires --page.")
            _render_page(pdf, page, render_dir)


@app.command()
def extract(
    pdf: Annotated[Path, typer.Argument(help="PDF file to extract.")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Directory for the extraction.")],
    overwrite: Annotated[
        bool, typer.Option("--overwrite", help="Replace an existing extraction.")
    ] = False,
) -> None:
    """Extract text positions, images, and vector regions."""
    with _handled():
        destination = extract_pdf(pdf, output, settings=_settings(), overwrite=overwrite)
        typer.echo(str(destination))


@app.command("parse")
def parse_command(
    pdf: Annotated[Path, typer.Argument(help="Official or synthetic catalog PDF.")],
    exam: Annotated[str, typer.Option("--exam", "-e", help="Examination, for example sbf-see.")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Directory for catalog.json.")],
    strict: Annotated[
        bool,
        typer.Option("--strict", help="Do not write catalog.json when validation reports errors."),
    ] = False,
    overwrite: Annotated[
        bool, typer.Option("--overwrite", help="Replace an existing catalog.json.")
    ] = False,
    source_url: Annotated[str | None, typer.Option("--source-url", help="Provenance URL.")] = None,
    publisher: Annotated[
        str | None, typer.Option("--publisher", help="Publisher override.")
    ] = None,
    title: Annotated[str | None, typer.Option("--title", help="Title override.")] = None,
    document_date: Annotated[
        str | None,
        typer.Option("--document-date", help="ISO date stated for the catalog edition."),
    ] = None,
) -> None:
    """Parse a catalog PDF into versioned JSON."""
    with _handled():
        try:
            parsed_date = date.fromisoformat(document_date) if document_date else None
        except ValueError as exc:
            raise UsageError(
                "--document-date must be an ISO date, for example 2023-08-01."
            ) from exc
        destination, report = parse_pdf(
            pdf,
            exam,
            output,
            settings=_settings(),
            strict=strict,
            overwrite=overwrite,
            source_url=source_url,
            publisher=publisher,
            title=title,
            document_date=parsed_date,
        )
        typer.echo(
            f"{destination} ({report.status}: "
            f"{report.error_count} errors, {report.warning_count} warnings)"
        )
        if report.error_count:
            raise typer.Exit(code=2)


@app.command()
def validate(
    catalog: Annotated[Path, typer.Argument(help="catalog.json file.")],
    as_json: Annotated[
        bool, typer.Option("--json", help="Print the validation report as JSON.")
    ] = False,
) -> None:
    """Validate an exported catalog."""
    with _handled():
        report = validate_export(catalog)
        if as_json:
            import json

            typer.echo(json.dumps(report.summary(), ensure_ascii=False, indent=2))
        else:
            typer.echo(
                f"{report.status}: {report.error_count} errors, {report.warning_count} warnings"
            )
        if report.error_count:
            raise typer.Exit(code=2)


@app.command()
def export(
    catalog: Annotated[Path, typer.Argument(help="catalog.json file.")],
    output: Annotated[Path, typer.Option("--output", "-o", help="CSV output file.")],
    export_format: Annotated[
        str,
        typer.Option("--format", help="Export format. Only csv is implemented."),
    ] = "csv",
    overwrite: Annotated[
        bool, typer.Option("--overwrite", help="Replace an existing CSV file.")
    ] = False,
) -> None:
    """Export a catalog to CSV."""
    with _handled():
        if export_format != "csv":
            raise UsageError(f"Unsupported export format {export_format!r}. Use csv.")
        destination = export_csv(catalog, output, overwrite=overwrite)
        typer.echo(str(destination))


@sources_app.command("list")
def sources_list() -> None:
    """List examinations and verified source records."""
    for exam in EXAMINATIONS:
        status = "parser" if exam.parser_implemented else "model only"
        typer.echo(f"{exam.id}\t{status}\t{exam.name}")
    typer.echo("")
    for source in VERIFIED_SOURCES:
        typer.echo(f"{source.id}\t{source.filename}\t{source.document_date or '-'}")


@sources_app.command("verify")
def sources_verify(
    directory: Annotated[
        Path,
        typer.Option("--directory", help="Directory that may contain the pinned PDFs."),
    ] = Path("data/sources"),
) -> None:
    """Compare local catalog files with the pinned checksums. Does not download."""
    with _handled():
        mismatches = 0
        for source in VERIFIED_SOURCES:
            path = directory / source.filename
            if not path.is_file():
                typer.echo(f"{source.id}: not present at {path}")
                continue
            digest = sha256_file(path)
            if source.sha256 and digest != source.sha256:
                mismatches += 1
                typer.echo(
                    f"{source.id}: checksum mismatch. Expected {source.sha256}, got {digest}."
                )
            else:
                typer.echo(f"{source.id}: checksum matches")
        if mismatches:
            raise typer.Exit(code=2)


@sources_app.command("fetch")
def sources_fetch(
    source_id: Annotated[str, typer.Argument(help="Source id from `sources list`.")],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Directory for the downloaded PDF."),
    ] = Path("data/sources"),
    overwrite: Annotated[
        bool, typer.Option("--overwrite", help="Replace an existing file.")
    ] = False,
) -> None:
    """Download one verified catalog PDF."""
    with _handled():
        try:
            record = get_source(source_id)
        except KeyError as exc:
            raise UsageError(str(exc)) from exc
        if not record.download_url:
            raise UsageError(f"{source_id} has no verified download URL.")
        output.mkdir(parents=True, exist_ok=True)
        destination = output / record.filename
        if destination.exists() and not overwrite:
            raise UsageError(
                f"Output already exists: {destination}. Pass --overwrite to replace it."
            )
        path, digest = download_pdf(
            record.download_url,
            destination,
            settings=_settings(),
            expected_sha256=record.sha256,
        )
        typer.echo(f"{path} {digest}")


def _render_page(pdf: Path, page_number: int, render_dir: Path) -> None:
    settings = _settings()
    load_local_pdf(pdf, settings=settings)
    document = open_pdf(pdf, settings)
    try:
        if page_number < 1 or page_number > int(document.page_count):
            raise UsageError(f"Page {page_number} is outside 1..{document.page_count}.")
        render_dir.mkdir(parents=True, exist_ok=True)
        page = document[page_number - 1]
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
        target = render_dir / f"page-{page_number}.png"
        pixmap.save(str(target))
    finally:
        document.close()
    typer.echo(str(target))


def run() -> None:
    """Entry point used by ``python -m elwis_parser``."""
    app()


if __name__ == "__main__":
    run()
