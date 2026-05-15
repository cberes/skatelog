from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path
from skatelog.models import Session


def parse_rows(csv_path: Path) -> Iterator[Session]:
    with csv_path.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for raw_row in reader:
            # nothing will be null, isn't that great?
            row = {(k or "").strip(): (v or "").strip() for k, v in raw_row.items()}
            print(row)


def import_csv(csv_path: Path) -> int:
    count = 0
    for session in parse_rows(csv_path):
        print(session)
        count += 1
    return count
