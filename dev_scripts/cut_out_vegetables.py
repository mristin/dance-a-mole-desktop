"""Download and cut out sprites from https://github.com/lepunk/react-native-videos/."""

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

    url = "https://opengameart.org/sites/default/files/Vegetables_0.png"

    with requests.get(url) as response:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_pth = os.path.join(tmp_dir, "sprites.png")
            with open(tmp_pth, "wb") as fid:
                fid.write(response.content)

            sprites = PIL.Image.open(tmp_pth)

            png_info = dict()
            if sprites.mode not in ['RGB', 'RGBA']:
                sprites = sprites.convert('RGBA')
                png_info = sprites.info

            sprite_width = int(sprites.size[0] / 4)
            sprite_height = sprite_width

            # We crop only the small vegetables.
            for i in range(12):
                cropped = sprites.crop(
                    (
                        int(i % 4) * sprite_width,
                        int(i / 4) * sprite_height,
                        int(i % 4) * sprite_width + sprite_width,
                        int(i / 4) * sprite_height + sprite_height
                    )
                )

                cropped.save(str(sprites_dir / f"vegetable{i}.png"), **png_info)

    return 0


if __name__ == "__main__":
    sys.exit(main())
