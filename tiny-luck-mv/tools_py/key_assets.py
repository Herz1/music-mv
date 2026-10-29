#!/usr/bin/env python3
"""Chroma-key magenta (#FF00FF) character raws -> RGBA sprites (skill 04: chroma-key method).
Usage: python tools_py/key_assets.py
"""
import os, glob
import numpy as np
from PIL import Image
from scipy import ndimage

CHAR = os.path.join(os.path.dirname(__file__), "..", "assets", "char")

def key(path, out):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # magenta-ness: high where min(r,b) >> g
    m = np.minimum(r, b) - g
    alpha = np.clip(1.0 - (m - 12.0) / 55.0, 0, 1)
    # clean: remove specks, feather edge
    alpha = ndimage.gaussian_filter(alpha, 0.7)
    alpha[alpha < 0.02] = 0
    # despill on edge pixels: pull r/b toward g where magenta dominates
    edge = (alpha > 0) & (alpha < 0.99)
    rr, bb = r.copy(), b.copy()
    spill = np.clip((m - 10) / 120.0, 0, 1) * edge
    rr = rr * (1 - spill) + g * spill
    bb = bb * (1 - spill) + g * spill
    rgba = np.dstack([rr, g, bb, alpha * 255]).astype(np.uint8)
    img = Image.fromarray(rgba, "RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    img.save(out)
    print(f"{os.path.basename(path)} -> {os.path.basename(out)} {img.size}")

if __name__ == "__main__":
    for raw in sorted(glob.glob(os.path.join(CHAR, "*_raw.png"))):
        name = os.path.basename(raw).replace("_raw.png", ".png")
        key(raw, os.path.join(CHAR, name))
    # master alias used by docs/storyboard
    src = os.path.join(CHAR, "REF_master.png")
    if os.path.exists(src):
        print("master ready:", src)
