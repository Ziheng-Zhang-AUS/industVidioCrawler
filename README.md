# IndustVidioCrawler

An **industrial video crawling and preprocessing pipeline** for building large-scale real-world datasets from YouTube.  
This framework automates every step — from query-based video retrieval to frame extraction and multimodal inference filtering using **Qwen2.5-VL**.

---

## Project Structure

```
industVidioCrawler/
│
├── data/
│   ├── urls.txt                 # Search page URLs (YouTube results)
│   ├── video_ids.txt            # Newly crawled video IDs
│   └── video_ids_all.txt        # All cumulative video IDs
│
├── src/
│   ├── crawler/
│   │   ├── get_ids_from_urls.py # Crawl video IDs from YouTube search results
│   │   └── get_videos.py        # Download videos using yt-dlp
│   │
│   ├── preprocessing/
│   │   └── extract_frames.py    # Extract representative frames via ffmpeg
│   │
│   └── inference/
│       ├── deploy.py            # FastAPI server for Qwen2.5-VL inference
│       └── run.py               # Send extracted frames for model-based filtering
│
├── configs/                     # (Optional) Configuration or parameter files
├── main_pipeline.py             # One-click orchestrator for the entire workflow
├── requirements.txt             # Python dependencies
├── .gitignore
└── README.md
```

---

## Environment Setup

### 1. Clone and navigate

```bash
git clone https://github.com/Ziheng-Zhang-AUS/industVidioCrawler.git
cd industVidioCrawler
```

### 2. Create a Python environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Ensure required tools are installed

- **Chrome / Chromium** (for Selenium crawling)
- **ffmpeg & ffprobe** (for video analysis)
- **yt-dlp** (for downloading videos)
- **CUDA** environment (for Qwen2.5-VL inference)

---

## Usage

### Option 1. Run the full pipeline

Execute all stages (crawl → download → extract → inference):

```bash
python main_pipeline.py --stage all
```

### Option 2. Run specific stages

| Stage      | Description                                | Command                                    |
| ---------- | ------------------------------------------ | ------------------------------------------ |
| `crawl`    | Crawl YouTube search results for video IDs | `python main_pipeline.py --stage crawl`    |
| `download` | Download videos via yt-dlp                 | `python main_pipeline.py --stage download` |
| `frames`   | Extract representative frames              | `python main_pipeline.py --stage frames`   |
| `infer`    | Run Qwen-VL inference on frames            | `python main_pipeline.py --stage infer`    |

---

## Crawling Details

**`get_ids_from_urls.py`**

- Takes URLs from `data/urls.txt`.
- Uses **Selenium** with headless Chrome to dynamically scroll and extract all video IDs.
- Supports multi-processing for large-scale crawling.

**Example:**

```bash
python src/crawler/get_ids_from_urls.py
```

Output:

- `video_ids.txt` — newly discovered IDs
- `video_ids_all.txt` — cumulative history to avoid duplication

---

## Video Downloading

**`get_videos.py`**

- Downloads videos in low resolution using **yt-dlp**.
- Organizes them under `/data/videos/{video_id}/video_id.mp4`.
- Supports parallel downloading (configurable via `NUM_PROCESSES`).

---

## Frame Extraction

**`extract_frames.py`**

- Uses **ffmpeg** to sample frames between 10%–90% of video duration.
- Frame count scales with duration (2, 5, or 20 frames).
- Output saved to `{video_id}/frames/`.

---

## Model Inference

**`deploy.py`**

- Deploys a **FastAPI** endpoint wrapping `Qwen2.5-VL-3B-Instruct`.
- Accepts image uploads and text prompts for multimodal reasoning.

Start the server:

```bash
uvicorn src.inference.deploy:app --host 0.0.0.0 --port 8000
```

**`run.py`**

- Sends frames to the inference server.
- The default question checks whether the video depicts a **warehouse scene** and classifies it as _normal_ or _abnormal_.

---

## Example Prompt

```text
These are frames from a video. Please determine whether this video takes place inside a warehouse.
Focus on identifying typical indoor warehouse features, such as shelves, goods, storage areas,
industrial equipment, or warehouse workers. Reply strictly with YES or NO, followed by one sentence.
```

---

## Configuration

You can modify parameters directly in script headers, such as:

- `NUM_VIDEOS_PER_URL` (in `get_ids_from_urls.py`)
- `NUM_PROCESSES` and `OUTPUT_DIR` (in `get_videos.py`)
- `ROOT_DIR` and `NUM_FRAMES` (in `run.py`)

---

## Future Extensions

- Integrate video classification or captioning models for fine-grained filtering.
- Add database storage for metadata and annotation synchronization.
- Incorporate logging and monitoring (`logs/pipeline_*.log`).
- Support automatic resume and failure recovery.

---

## Author

**Ziheng Zhang**  
Master of Computing, Australian National University  
GitHub: [@Ziheng-Zhang-AUS](https://github.com/Ziheng-Zhang-AUS)

---

## License

This project is released under the **MIT License**.
See [LICENSE](LICENSE) for details.
