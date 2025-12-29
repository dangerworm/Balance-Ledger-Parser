#!/usr/bin/env python3
"""
kraken_batch_zip.py

WSL-friendly batch runner:
- unzip images
- sort by trailing number in filename
- run kraken CLI for each image
- write per-page text + combined transcript

Requirements (in the same environment):
- kraken installed (pip install kraken[pdf])  :contentReference[oaicite:4]{index=4}
- a recognition model .mlmodel
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path

IMG_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
TRAILING_NUM = re.compile(r"(\d+)(?=\D*$)")


def extract_zip(zip_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(out_dir)


def find_images(root: Path) -> list[Path]:
    imgs = [p for p in root.rglob("*") if p.suffix.lower() in IMG_EXTS]
    return sorted(imgs, key=sort_key)


def sort_key(p: Path) -> tuple[int, str]:
    m = TRAILING_NUM.search(p.stem)
    n = int(m.group(1)) if m else 10**9
    return (n, p.name.lower())


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    # Some kraken commands emit useful info to stdout
    if proc.stdout.strip():
        print(proc.stdout)


def kraken_ocr(image_path: Path, model_path: Path, out_txt: Path) -> None:
    """
    Uses kraken CLI. The exact CLI options can differ by version;
    if your installed kraken uses slightly different subcommands,
    we’ll adjust to match `kraken -h` output.
    """
    out_txt.parent.mkdir(parents=True, exist_ok=True)

    # Common pattern:
    # kraken -i input.jpg output.txt ocr -m model.mlmodel
    cmd = [
        "kraken",
        "-i", str(image_path), str(out_txt),
        "ocr",
        "-m", str(model_path),
    ]
    run(cmd)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("zip_path", type=Path)
    ap.add_argument("--work", type=Path, default=Path("work_unzipped"))
    ap.add_argument("--out", type=Path, default=Path("out_kraken"))
    ap.add_argument("--model", type=Path, required=True, help="Path to a .mlmodel file")
    args = ap.parse_args()

    if not args.zip_path.exists():
        sys.exit(f"ZIP not found: {args.zip_path}")
    if not args.model.exists():
        sys.exit(f"Model not found: {args.model}")

    extract_zip(args.zip_path, args.work)
    images = find_images(args.work)
    if not images:
        sys.exit("No images found after extraction.")

    pages_dir = args.out / "pages"
    combined_path = args.out / "combined.txt"
    args.out.mkdir(parents=True, exist_ok=True)

    combined_chunks: list[str] = []

    for i, img in enumerate(images, start=1):
        out_txt = pages_dir / f"page_{i:04d}.txt"
        kraken_ocr(img, args.model, out_txt)
        txt = out_txt.read_text(encoding="utf-8", errors="replace").strip()
        combined_chunks.append(f"\n\n===== PAGE {i:04d} : {img.name} =====\n\n{txt}\n")

    combined_path.write_text("".join(combined_chunks), encoding="utf-8")
    print(f"Done. Wrote {len(images)} pages to {args.out.resolve()}")


if __name__ == "__main__":
    main()
