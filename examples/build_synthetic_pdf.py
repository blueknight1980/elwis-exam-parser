"""Write a tiny synthetic catalog PDF.

The text is invented for the parser tests. It is not an official question.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pymupdf


def main() -> None:
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("examples/synthetic-see.pdf")
    document = pymupdf.open()
    try:
        page = document.new_page()
        lines = [
            "Basisfragen",
            "Antwort a ist immer die richtige.",
            "1. Synthetische Testfrage?",
            "a. Erste Antwort",
            "b. Zweite Antwort",
            "c. Dritte Antwort",
            "d. Vierte Antwort",
        ]
        y = 80.0
        for line in lines:
            page.insert_text((37, y), line, fontsize=11)
            y += 18
        destination.parent.mkdir(parents=True, exist_ok=True)
        document.save(destination)
    finally:
        document.close()
    print(destination)


if __name__ == "__main__":
    main()
