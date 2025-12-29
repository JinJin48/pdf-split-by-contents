import os
import sys
import re
import logging
import time
import datetime

# Configuration
INPUT_DIR = "input_pdf"
OUTPUT_DIR = "split_pdf"
LOG_FILE = "pdf-split.log"
LARGE_FILE_THRESHOLD = 45 * 1024 * 1024  # 45MB


def setup_logging(background_mode, log_file=LOG_FILE):
    """Configure logging."""
    handlers = [logging.FileHandler(log_file, encoding='utf-8', mode='a')]
    if not background_mode:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def estimate_time(start_wall_time, processed_count, total_count):
    """Log estimated completion time."""
    if processed_count == 0:
        return

    elapsed = time.time() - start_wall_time
    avg_per_item = elapsed / processed_count
    remaining = total_count - processed_count
    est_seconds = remaining * avg_per_item

    est_finish = datetime.datetime.now() + datetime.timedelta(seconds=est_seconds)
    logging.info(f"Progress: {processed_count}/{total_count}. "
                 f"Avg: {avg_per_item:.1f}s/item. "
                 f"Est. Finish: {est_finish.strftime('%Y-%m-%d %H:%M:%S')}")


def clean_filename(name):
    """Sanitize filename."""
    return re.sub(r'[\\/*?:"<>|]', "", name)
