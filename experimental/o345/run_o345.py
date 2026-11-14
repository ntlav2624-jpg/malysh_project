#!/usr/bin/env python3

import argparse
import json

from o345 import Canonical345, meta_observe


parser = argparse.ArgumentParser()
parser.add_argument("n", type=int)
args = parser.parse_args()

state = Canonical345.from_n(args.n)

print(
    json.dumps(
        meta_observe(state),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
)
