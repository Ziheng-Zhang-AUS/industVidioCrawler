import os
import subprocess
from pathlib import Path
from multiprocessing import Pool, cpu_count


def get_video_duration(video_path: str) -> float:
    """Gets the duration (in seconds) of a video file using ffprobe.

    Args:
        video_path: Path to the video file.

    Returns:
        The duration of the video in seconds.
    """
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            video_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return float(result.stdout.strip())


def extract_frames_ffmpeg(video_path: str, out_dir: str) -> None:
    """Extracts representative frames from a video using ffmpeg.

    The number of frames is determined by the video duration:
    - <= 30s: 2 frames
    - <= 240s: 5 frames
    - > 240s: 20 frames

    Frames are sampled uniformly between 10% and 90% of the video duration.

    Args:
        video_path: Path to the video file.
        out_dir: Directory to save extracted frames.
    """
    os.makedirs(out_dir, exist_ok=True)
    duration = get_video_duration(video_path)
    basename = Path(video_path).stem

    # Determine number of frames to extract
    if duration <= 30:
        n_frames = 2
    elif duration <= 240:
        n_frames = 5
    else:
        n_frames = 20

    # Uniformly sample between 10% and 90% of duration
    start = duration * 0.1
    end = duration * 0.9
    if n_frames == 1:
        timestamps = [(start + end) / 2]
    else:
        timestamps = [
            start + i * (end - start) / (n_frames - 1) for i in range(n_frames)
        ]

    for idx, ts in enumerate(timestamps):
        out_path = os.path.join(out_dir, f"{basename}_f{idx:02d}.jpg")
        if os.path.exists(out_path):
            continue  # Skip if frame already exists
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            str(ts),
            "-i",
            video_path,
            "-frames:v",
            "1",
            "-q:v",
            "2",
            out_path,
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"Extracted {len(timestamps)} frames: {video_path}")


def process_single_video(sub_path: str) -> None:
    """Processes a single video directory and extracts frames.

    Args:
        sub_path: Directory containing the video file.
    """
    mp4_files = [f for f in os.listdir(sub_path) if f.endswith(".mp4")]
    if not mp4_files:
        return

    video_path = os.path.join(sub_path, mp4_files[0])
    frame_dir = os.path.join(sub_path, "frames")

    if os.path.exists(frame_dir) and len(os.listdir(frame_dir)) > 0:
        print(f"Frames already exist, skipping: {video_path}")
        return

    extract_frames_ffmpeg(video_path, frame_dir)


def main() -> None:
    """Main entry point for extracting frames from all downloaded videos."""
    video_root = "/home/ziheng/warehouse/videos"
    subdirs = [
        os.path.join(video_root, d)
        for d in os.listdir(video_root)
        if os.path.isdir(os.path.join(video_root, d))
    ]

    print(f"Found {len(subdirs)} video directories. Starting parallel extraction...")
    pool = Pool(processes=cpu_count())
    pool.map(process_single_video, subdirs)
    pool.close()
    pool.join()
    print("All frame extraction tasks completed.")


if __name__ == "__main__":
    main()