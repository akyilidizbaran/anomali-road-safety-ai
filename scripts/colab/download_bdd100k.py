#!/usr/bin/env python3
"""Optional BDD100K downloader for Google Colab.

This script intentionally writes data under Google Drive / external dataset
paths, never inside the Git repository. It supports three practical modes:

1. kaggle: uses Kaggle API credentials from Colab environment/secrets.
2. direct: downloads archives from user-provided direct URLs.
3. gdown: downloads Google Drive files by user-provided IDs or URLs.

The official BDD100K portal may change download mechanisms. Keep URLs and
credentials outside Git and pass them as environment variables or CLI args.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlretrieve


DEFAULT_ROOT = Path("/content/drive/MyDrive/anomali-road-safety-ai/datasets/bdd100k")


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.check_call(cmd)


def ensure_package(package: str) -> None:
    try:
        __import__(package)
    except ImportError:
        run([sys.executable, "-m", "pip", "install", "-q", package])


def extract_archive(archive: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    suffixes = "".join(archive.suffixes)
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(output_dir)
    elif suffixes.endswith(".tar.gz") or suffixes.endswith(".tgz"):
        run(["tar", "-xzf", str(archive), "-C", str(output_dir)])
    elif archive.suffix == ".tar":
        run(["tar", "-xf", str(archive), "-C", str(output_dir)])
    else:
        print(f"Archive kept without extraction: {archive}")


def download_direct(urls: list[str], output_dir: Path, extract: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for url in urls:
        name = Path(urlparse(url).path).name or "bdd100k_download"
        target = output_dir / name
        if target.exists():
            print(f"Exists, skipping: {target}")
        else:
            print(f"Downloading {url} -> {target}")
            urlretrieve(url, target)
        if extract:
            extract_archive(target, output_dir)


def download_gdown(ids_or_urls: list[str], output_dir: Path, extract: bool) -> None:
    ensure_package("gdown")
    output_dir.mkdir(parents=True, exist_ok=True)
    for item in ids_or_urls:
        cmd = ["gdown", "--fuzzy", item, "-O", str(output_dir)]
        run(cmd)
    if extract:
        for archive in output_dir.iterdir():
            if archive.is_file() and archive.suffix in {".zip", ".tar"}:
                extract_archive(archive, output_dir)
            elif archive.is_file() and "".join(archive.suffixes).endswith((".tar.gz", ".tgz")):
                extract_archive(archive, output_dir)


def download_kaggle(dataset: str, output_dir: Path, extract: bool) -> None:
    ensure_package("kaggle")
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_json = kaggle_dir / "kaggle.json"
    env_user = os.getenv("KAGGLE_USERNAME")
    env_key = os.getenv("KAGGLE_KEY")
    if not kaggle_json.exists() and not (env_user and env_key):
        raise RuntimeError(
            "Kaggle credentials not found. Set KAGGLE_USERNAME and KAGGLE_KEY "
            "as Colab secrets/env vars, or upload ~/.kaggle/kaggle.json."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["kaggle", "datasets", "download", "-d", dataset, "-p", str(output_dir)]
    if extract:
        cmd.append("--unzip")
    run(cmd)


def find_expected_structure(root: Path) -> dict[str, bool]:
    candidates = {
        "train_images": [
            root / "images" / "100k" / "train",
            root / "images" / "train",
        ],
        "val_images": [
            root / "images" / "100k" / "val",
            root / "images" / "val",
        ],
        "train_labels": [
            root / "labels" / "det_20" / "det_train.json",
            root / "labels" / "bdd100k_labels_images_train.json",
            root / "bdd100k_labels_images_train.json",
        ],
        "val_labels": [
            root / "labels" / "det_20" / "det_val.json",
            root / "labels" / "bdd100k_labels_images_val.json",
            root / "bdd100k_labels_images_val.json",
        ],
    }
    return {key: any(path.exists() for path in paths) for key, paths in candidates.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=["kaggle", "direct", "gdown"], required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--kaggle-dataset", default=os.getenv("BDD100K_KAGGLE_DATASET", ""))
    parser.add_argument("--url", action="append", default=[])
    parser.add_argument("--gdrive", action="append", default=[])
    args = parser.parse_args()

    if args.method == "kaggle":
        if not args.kaggle_dataset:
            raise RuntimeError("Pass --kaggle-dataset or set BDD100K_KAGGLE_DATASET.")
        download_kaggle(args.kaggle_dataset, args.output_dir, args.extract)
    elif args.method == "direct":
        urls = args.url or [v for v in os.getenv("BDD100K_DIRECT_URLS", "").split(",") if v]
        if not urls:
            raise RuntimeError("Pass one or more --url values or set BDD100K_DIRECT_URLS.")
        download_direct(urls, args.output_dir, args.extract)
    elif args.method == "gdown":
        ids = args.gdrive or [v for v in os.getenv("BDD100K_GDRIVE_IDS", "").split(",") if v]
        if not ids:
            raise RuntimeError("Pass one or more --gdrive values or set BDD100K_GDRIVE_IDS.")
        download_gdown(ids, args.output_dir, args.extract)

    status = find_expected_structure(args.output_dir)
    print("BDD100K structure check:")
    for key, ok in status.items():
        print(f"  {key}: {'OK' if ok else 'MISSING'}")

    if not all(status.values()):
        print(
            "Some expected paths are missing. Move/extract files to the layout "
            "expected by notebooks/VD_EXP_002_BDD100K_YOLO11n_Colab.ipynb."
        )


if __name__ == "__main__":
    main()
