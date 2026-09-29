"""Strip ICC profiles from all PNGs in assets/images."""

import os
from PIL import Image

ASSETS_DIR = "src/img/"


def clean_pngs(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".png"):
            path = os.path.join(directory, filename)
            img = Image.open(path)
            img.save(path, icc_profile=None)
            print(f"Cleaned: {filename}")


if __name__ == "__main__":
    clean_pngs(ASSETS_DIR)
