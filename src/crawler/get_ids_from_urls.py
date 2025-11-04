from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

# ====== Configuration ======
URL_FILE = "urls.txt"
NUM_VIDEOS_PER_URL = 1000  # Maximum number of videos to collect per search page
OUTPUT_FILE = "video_ids.txt"
ALL_IDS_FILE = "video_ids_all.txt"
SCROLL_PAUSE_TIME = 2  # Wait time after each scroll (seconds)
MAX_WORKERS = 8  # Maximum number of parallel processes
# ============================


def extract_video_ids(html: str) -> list[str]:
    """Extracts all video IDs from a YouTube search result page HTML.

    Args:
        html: The HTML content of the page.

    Returns:
        A list of 11-character YouTube video IDs.
    """
    return re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)


def scroll_to_load_single(url: str, target_count: int) -> list[str]:
    """Scrolls through a YouTube search result page and extracts video IDs.

    Args:
        url: The YouTube search result URL to crawl.
        target_count: The maximum number of video IDs to collect from this URL.

    Returns:
        A list of collected video IDs.
    """
    print(f"Starting: {url}")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--window-size=1920x1080")
    # Each process uses an independent Chrome user data directory to avoid conflicts.
    chrome_options.add_argument(f"--user-data-dir=/tmp/chrome_temp_{os.getpid()}")

    driver = webdriver.Chrome(options=chrome_options)
    video_ids = set()

    try:
        driver.get(url)
        time.sleep(3)

        last_height = driver.execute_script("return document.documentElement.scrollHeight")

        while len(video_ids) < target_count:
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)

            html = driver.page_source
            ids = extract_video_ids(html)
            video_ids.update(ids)

            print(f"{url[-20:]}: Extracted {len(video_ids)} videos so far")

            if len(video_ids) >= target_count:
                break

            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                print(f"{url[-20:]}: Reached the bottom of the page")
                break
            last_height = new_height

    except Exception as e:
        print(f"Error while processing {url}: {e}")
    finally:
        driver.quit()

    result = list(video_ids)[:target_count]
    print(f"{url[-20:]}: Completed, total {len(result)} video IDs collected")
    return result


def load_urls_from_file(path: str) -> list[str]:
    """Loads YouTube search URLs from a text file.

    Args:
        path: The file path containing search URLs.

    Returns:
        A list of valid, non-empty URLs.
    """
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def load_existing_ids(path: str) -> set[str]:
    """Loads existing video IDs from a file to avoid duplication.

    Args:
        path: File path for the existing ID list.

    Returns:
        A set of video IDs, or an empty set if the file does not exist.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()


def save_new_ids_to_file(new_ids: set[str], output_path: str) -> None:
    """Saves new video IDs to a specified output file.

    Args:
        new_ids: A set of new video IDs.
        output_path: Path to the file where IDs will be written.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for vid in sorted(new_ids):
            f.write(vid + "\n")


def append_new_ids_to_all(new_ids: set[str], all_path: str) -> None:
    """Appends new video IDs to the cumulative ID file.

    Args:
        new_ids: A set of new video IDs to append.
        all_path: Path to the cumulative ID file.
    """
    with open(all_path, "a", encoding="utf-8") as f:
        for vid in sorted(new_ids):
            f.write(vid + "\n")


def main() -> None:
    """Main entry point for multi-process YouTube video ID collection."""
    urls = load_urls_from_file(URL_FILE)
    print(f"Loaded {len(urls)} search URLs")
    print(f"Using {MAX_WORKERS} parallel processes")

    all_ids = set()

    # Parallel crawling using ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_url = {
            executor.submit(scroll_to_load_single, url, NUM_VIDEOS_PER_URL): url
            for url in urls
        }

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                ids = future.result()
                all_ids.update(ids)
                print(f"Collected from {url[-20:]}: {len(ids)} IDs")
            except Exception as e:
                print(f"Error retrieving results for {url}: {e}")

    print(f"\nCompleted: {len(all_ids)} unique video IDs collected")

    # Load existing IDs and compute new ones
    existing_ids = load_existing_ids(ALL_IDS_FILE)
    print(f"Found {len(existing_ids)} existing video IDs in {ALL_IDS_FILE}")

    new_ids = all_ids - existing_ids
    duplicate_count = len(all_ids) - len(new_ids)

    print(f"Removed {duplicate_count} duplicates")
    print(f"Newly collected IDs: {len(new_ids)}")

    # Save and append results
    save_new_ids_to_file(new_ids, OUTPUT_FILE)
    print(f"New video IDs written to {OUTPUT_FILE}")

    append_new_ids_to_all(new_ids, ALL_IDS_FILE)
    print(f"All IDs appended to {ALL_IDS_FILE}")


if __name__ == "__main__":
    main()