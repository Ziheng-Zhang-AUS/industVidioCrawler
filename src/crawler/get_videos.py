import os
import sys
import subprocess
import time
import traceback
from multiprocessing import Pool, cpu_count

# ================== Configuration ==================
OUTPUT_DIR = "/home/ziheng/warehouse/videos"  # Directory to save downloaded videos
NUM_PROCESSES = 10  # Number of parallel download processes (recommended ≤10)
ID_FILE = "video_ids.txt"  # Text file containing YouTube video IDs
COOKIES_FILE = "cookies.txt"  # Optional: YouTube cookies for authenticated downloads
# ===================================================


def check_python_version() -> None:
    """Checks the current Python version and prints a warning if it is too low."""
    if sys.version_info < (3, 9):
        print("Warning: Python version is below 3.9. "
              "yt-dlp is recommended to run on Python >= 3.9.")


def load_video_ids(filename: str) -> list[str]:
    """Loads video IDs from a text file.

    Args:
        filename: Path to the file containing one video ID per line.

    Returns:
        A list of video IDs.
    """
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def download_video(video_id: str) -> None:
    """Downloads a single YouTube video using yt-dlp.

    The video is saved to a subdirectory named after the video ID.
    If the video already exists, it is skipped.

    Args:
        video_id: The 11-character YouTube video ID.
    """
    try:
        print(f"\n===== Downloading video {video_id} =====")
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        out_dir = os.path.join(OUTPUT_DIR, video_id)
        os.makedirs(out_dir, exist_ok=True)
        output_path = os.path.join(out_dir, f"{video_id}.mp4")

        if os.path.exists(output_path):
            print(f"[{video_id}] Video already exists, skipping.")
            return

        # Build yt-dlp command to download the lowest-quality mp4 video
        cmd = [
            "yt-dlp",
            "-f", "worst[ext=mp4]/worst",
            "-o", output_path,
            video_url
        ]

        if os.path.exists(COOKIES_FILE):
            cmd += ["--cookies", COOKIES_FILE]

        print(f"[{video_id}] Starting download ...")
        start_time = time.time()
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        elapsed = time.time() - start_time

        if proc.returncode == 0:
            print(f"[{video_id}] Download successful ({elapsed:.1f}s): {output_path}")
        else:
            print(f"[{video_id}] Download failed:")
            print(proc.stderr)

    except Exception as e:
        print(f"[{video_id}] Exception occurred: {e}")
        traceback.print_exc()


def main() -> None:
    """Main entry point for downloading YouTube videos in parallel."""
    check_python_version()
    video_ids = load_video_ids(ID_FILE)
    print(f"Preparing to download {len(video_ids)} videos...")

    pool_size = NUM_PROCESSES or cpu_count()
    print(f"Using {pool_size} parallel processes.")
    pool = Pool(processes=pool_size)

    for vid in video_ids:
        pool.apply_async(download_video, args=(vid,))

    pool.close()
    pool.join()
    print("\nAll video downloads completed.")


if __name__ == "__main__":
    main()