# Examples

`build_synthetic_pdf.py` writes a one-page PDF with invented marker text. Use it to try the CLI without an official catalog:

```bash
python examples/build_synthetic_pdf.py
elwis-parser parse examples/synthetic-see.pdf --exam sbf-see --output examples/out --overwrite
```

The file is not an ELWIS document and must not be treated as one. Official catalogs belong in `data/sources/` and are not committed.
