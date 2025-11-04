#!/usr/bin/env python3
"""
main_pipeline.py
----------------
End-to-end controller script for the Industrial Video Crawling & Preprocessing pipeline.

This script orchestrates the following stages:
1. Crawl YouTube video IDs
2. Download videos using yt-dlp
3. Extract representative frames using ffmpeg
4. Run local inference via Qwen-VL (optional)

Usage:
    python main_pipeline.py --stage all
    python main_pipeline.py --stage crawl
    python main_pipeline.py --stage download
    python main_pipeline.py --stage frames
    python main_pipeline.py --stage infer
"""

import argparse
import subprocess
import sys
from datetime import datetime


def run_step(description: str, command: list[str]) -> None:
    """Runs a single pipeline step via subprocess and handles logging.

    Args:
        description: Human-readable description of the step.
        command: Command to execute as a list of strings.
    """
    print(f"\n=== {description} ===")
    print(f"Command: {' '.join(command)}")
    try:
        start = datetime.now()
        subprocess.run(command, check=True)
        elapsed = (datetime.now() - start).total_seconds()
        print(f"{description} completed in {elapsed:.1f} seconds.\n")
    except subprocess.CalledProcessError as e:
        print(f"Error during {description}: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Industrial Video Crawling and Preprocessing Pipeline"
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="all",
        choices=["crawl", "download", "frames", "infer", "all"],
        help="Specify which stage(s) to run.",
    )
    args = parser.parse_args()

    steps = {
        "crawl": {
            "desc": "Crawling YouTube video IDs",
            "cmd": ["python", "src/crawler/get_ids_from_urls.py"],
        },
        "download": {
            "desc": "Downloading videos via yt-dlp",
            "cmd": ["python", "src/crawler/get_videos.py"],
        },
        "frames": {
            "desc": "Extracting frames from downloaded videos",
            "cmd": ["python", "src/preprocessing/extract_frames.py"],
        },
        "infer": {
            "desc": "Running inference on sampled frames",
            "cmd": ["python", "src/inference/run.py"],
        },
    }

    print("\n=== Industrial Video Crawling & Preprocessing Pipeline ===")
    print(f"Selected stage: {args.stage}\n")

    if args.stage == "all":
        for key in ["crawl", "download", "frames", "infer"]:
            run_step(steps[key]["desc"], steps[key]["cmd"])
    else:
        step = steps[args.stage]
        run_step(step["desc"], step["cmd"])

    print("\nPipeline execution finished successfully.")


if __name__ == "__main__":
    main()