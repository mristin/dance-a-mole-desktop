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

    url = "https://raw.githubusercontent.com/lepunk/react-native-videos/whack-a-mole/WhackAMole/assets/img/sprites.png"

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

            sprite_width = int(sprites.size[0] / 6)
            sprite_height = int(sprites.size[1] / 8)

            for i in range(6):
                cropped = sprites.crop(
                    (
                        int(i % 6) * sprite_width,
                        int(i / 6) * sprite_height,
                        int(i % 6) * sprite_width + sprite_width,
                        int(i / 6) * sprite_height + sprite_height
                    )
                )

                cropped.save(str(sprites_dir / f"going_up{i}.png"), **png_info)
                cropped.save(str(sprites_dir / f"going_down{5 - i}.png"), **png_info)

            up_indices = [6, 6 + 1]
            for up_i, i in enumerate(up_indices):
                cropped = sprites.crop(
                    (
                        int(i % 6) * sprite_width,
                        int(i / 6) * sprite_height,
                        int(i % 6) * sprite_width + sprite_width,
                        int(i / 6) * sprite_height + sprite_height
                    )
                )

                cropped.save(str(sprites_dir / f"up{up_i}.png"), **png_info)

            dizzy_indices = [6 * 6, 6 * 6 + 1, 6 * 6 + 2, 7 * 6, 7 * 6 + 1, 7 * 6 + 2]
            for dizzy_i, i in enumerate(dizzy_indices):
                cropped = sprites.crop(
                    (
                        int(i % 6) * sprite_width,
                        int(i / 6) * sprite_height,
                        int(i % 6) * sprite_width + sprite_width,
                        int(i / 6) * sprite_height + sprite_height
                    )
                )

                cropped.save(str(sprites_dir / f"dizzy{dizzy_i}.png"), **png_info)

    return 0


if __name__ == "__main__":
    sys.exit(main())
