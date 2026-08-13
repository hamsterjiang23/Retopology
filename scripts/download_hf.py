"""Download selected files from a Hugging Face repository using cached auth."""
from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import hf_hub_download


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_id")
    parser.add_argument("local_dir", type=Path)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    args.local_dir.mkdir(parents=True, exist_ok=True)
    for filename in args.files:
        path = hf_hub_download(
            repo_id=args.repo_id,
            filename=filename,
            local_dir=args.local_dir,
            token=True,
        )
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
