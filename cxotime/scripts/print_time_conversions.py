# Licensed under a 3-clause BSD style license - see LICENSE.rst
import sys

from cxotime import CxoTime


def main(date=None, file=sys.stdout):
    """Interface to entry_point script ``cxotime`` to print time conversions.

    :param date: str, float, optional
        Date for time conversion if sys.argv[1] is not provided. Mostly for testing.
    :param file: file-like, optional
        File-like object to write output (default=sys.stdout). Mostly for testing.
    """
    if date is None:
        if len(sys.argv) > 2:
            print("Usage: cxotime [date]")
            sys.exit(1)

        if len(sys.argv) == 2:
            date = sys.argv[1]

    # If the input can be converted to a float then it is a CXC seconds value
    try:
        date = float(date)
    except Exception:
        pass

    date = CxoTime(date)
    date.print_conversions(file)


if __name__ == "__main__":
    main()
