#!/usr/bin/env python3
"""Download or bootstrap the demo dish-rule classifier model.

Usage:
  python scripts/download_model.py --url <MODEL_URL> --out models/dish_rule_classifier.joblib

If no URL is provided, the script prints instructions to train the demo model locally
using `scripts/train_dish_classifier.py`.
"""
import argparse
import os
import sys

try:
    import requests
except Exception:
    print("requests is required. Install with: pip install requests")
    sys.exit(2)


def download(url: str, out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    print(f"Downloading model from {url} → {out_path}")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(8192):
            if chunk:
                f.write(chunk)
    print("Download complete")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", help="Direct URL to the model file (joblib) to download")
    p.add_argument("--out", default="models/dish_rule_classifier.joblib", help="Output path")
    args = p.parse_args()

    if not args.url:
        print("No model URL provided.")
        print("You can either:")
        print("  1) Train the demo model locally: python scripts/train_dish_classifier.py")
        print("  2) Provide a hosted model URL and run this script with --url <MODEL_URL>")
        sys.exit(0)

    try:
        download(args.url, args.out)
    except Exception as e:
        print("Failed to download model:", e)
        sys.exit(3)


if __name__ == "__main__":
    main()
