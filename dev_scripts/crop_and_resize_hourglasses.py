"""
Crop the hourglasses from https://olgas-lab.itch.io/hourglass.

Make sure you downloaded them before to ``danceamole/media/sprites``.
"""

import argparse
import os
import pathlib
import sys
import tempfile

import PIL
import PIL.Image

import requests


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    this_path = pathlib.Path(os.path.realpath(__file__))
    sprites_dir = this_path.parent.parent / "danceamole/media/sprites"

    for i in range(5):
        pth = sprites_dir / f"original_hourglass{i}.png"

        image = PIL.Image.open(str(pth))

        png_info = dict()
        if image.mode not in ['RGB', 'RGBA']:
            image = image.convert('RGBA')
            png_info = image.info

        cropped = image.crop((230, 141, 460, 506))
        cropped = cropped.resize((73, 122))
        cropped.save(str(sprites_dir / f"hourglass{i}.png"), **png_info)

    return 0


if __name__ == "__main__":
    sys.exit(main())
