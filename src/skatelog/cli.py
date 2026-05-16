import sys
from pathlib import Path
from skatelog.importer import import_csv


def main() -> None:
    import_csv(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
