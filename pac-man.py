"""Launches Pac-Man: python3 pac-man.py <config.json>."""

import sys

try:
    from src.__main__ import run
except KeyboardInterrupt:
    print("Interrupted by user")
    sys.exit(1)


if __name__ == "__main__":
    run(sys.argv)
