"""
Stack Voyager Images

This script stacks TIFF images based on their filenames, which should follow a specific naming convention.

The expected filename format is: TxxxxFxxxLxxAxxZxxCxx.tif
Where:
- T: Time point index (tpIndex)
- F: Field of view index (fpIndex)
- L: Tile or stage position index (tlIndex)
- A: Additional position index (alIndex) (e.g., autofocus or acquisition round)
- Z: Z-slice index (zpIndex)
- C: Channel index (chIndex)

The output will be a single TIFF file for each unique combination of T, F, and L, containing a 5D stack of images.
Outputs the stacked images in the same folder with a name format: stack_Txxxx_Fxxx_Lxx.tif
"""

import os
import re
import numpy as np
from tifffile import imwrite, imread

folder = input("Enter the path to the folder containing TIFF files: ")
files = [f for f in os.listdir(folder) if f.endswith('.tif')]

# Regex to parse filenames
pattern = re.compile(r".*T(\d{4})F(\d{3})L(\d{2})A(\d{2})Z(\d{2})C(\d{2})\.tif$")

# Group images
images = {}
for fname in files:
    match = pattern.match(fname)
    if not match:
        continue
    t, f, l, a, z, c = map(int, match.groups())
    key = (t, f, l)  # group by T, F, L
    if key not in images:
        images[key] = []
    images[key].append((z, c, fname))

# Sort images within each group
for key, img_list in images.items():
    img_list.sort()  # sort by z, then c
    zs = sorted(set(z for z, c, _ in img_list))
    cs = sorted(set(c for z, c, _ in img_list))

    example_img = imread(os.path.join(folder, img_list[0][2]))
    height, width = example_img.shape
    stack = np.zeros((1, len(zs), len(cs), height, width), dtype=example_img.dtype)

    for z, c, fname in img_list:
        img = imread(os.path.join(folder, fname))
        z_index = zs.index(z)
        c_index = cs.index(c)
        stack[0, z_index, c_index, :, :] = img

    out_name = f"stack_T{key[0]}_F{key[1]}_L{key[2]}.tif"
    out_path = os.path.join(folder, out_name)
    imwrite(out_path, stack, imagej=True, metadata={'axes': 'TZCYX'})
    print(f"Saved: {out_path}")
