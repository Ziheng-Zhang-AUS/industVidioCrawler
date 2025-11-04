import os
import requests
from pathlib import Path

ROOT_DIR = "./output"
NUM_FRAMES = 2
ENDPOINT = "http://localhost:8000/predict"  # Local inference service endpoint


def process_video_folder(video_id: str, folder_path: str) -> None:
    """Sends representative video frames to a local model endpoint for inference.

    Each video folder is expected to contain multiple frame images. The function
    collects a fixed number of frames, sends them to the FastAPI service, and
    prints the model's response.

    Args:
        video_id: Identifier of the video (used for locating frames).
        folder_path: Path to the folder containing extracted frame images.
    """
    print(f"\nProcessing video: {video_id}")

    # Collect frame file paths
    files = []
    for i in range(1, NUM_FRAMES + 1):
        frame_path = os.path.join(folder_path, f"{video_id}_{i}.png")
        if os.path.exists(frame_path):
            files.append(("files", open(frame_path, "rb")))
        else:
            print(f"Missing frame image: {frame_path}. Skipping this video.")
            return

    # Text prompt for warehouse-scene classification
    question = (
        "These are frames from a video. "
        "Please determine whether this video takes place **inside a warehouse**. "
        "Focus on identifying typical indoor warehouse features, such as shelves, "
        "goods, storage areas, industrial equipment, or warehouse workers. "
        "Do not consider videos that appear to be from outside a warehouse or "
        "unrelated environments. "
        "If it is indeed a warehouse scene, briefly mention whether it appears "
        "normal or abnormal (e.g., fire, accident, disorder). "
        "Reply strictly with YES or NO, followed by a one-sentence explanation."
    )

    print("Sending request to local model ...")
    try:
        response = requests.post(ENDPOINT, data={"question": question}, files=files)

        if response.status_code == 200:
            result = response.json().get("result", "No result field in response.")
            print(f"Model output: {result}")
        else:
            print(
                f"Request failed with status code {response.status_code}. "
                f"Response: {response.text}"
            )
    except Exception as e:
        print(f"Error while calling model API: {e}")
    finally:
        for _, f in files:
            f.close()


def main() -> None:
    """Iterates through all video folders and processes them sequentially."""
    for subfolder in os.listdir(ROOT_DIR):
        folder_path = os.path.join(ROOT_DIR, subfolder)
        if os.path.isdir(folder_path):
            process_video_folder(subfolder, folder_path)


if __name__ == "__main__":
    main()