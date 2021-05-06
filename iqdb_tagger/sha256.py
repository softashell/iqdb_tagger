#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sha256 module."""
import hashlib
import sys


def sha256_checksum(filename: str, block_size: int = 65536) -> str:
    """Get sha256 checksum."""
    sha256 = hashlib.sha256()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()


def main() -> None:
    """Run main func for module."""
    for f in sys.argv[1:]:
        checksum = sha256_checksum(f)
        print(f + "\t" + checksum)


if __name__ == "__main__":
    main()
