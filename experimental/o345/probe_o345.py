#!/usr/bin/env python3

import json
import sys

from o345 import Canonical345, meta_observe


def main():
    if len(sys.argv) != 2:
        print("Usage: python probe_o345.py N")
        raise SystemExit(2)

    n = int(sys.argv[1]) % 60
    x = Canonical345.from_n(n)

    print(
        json.dumps(
            meta_observe(x),
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
