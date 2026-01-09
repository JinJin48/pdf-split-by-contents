import os
import sys
import re
import logging
import time
import datetime
import urllib.request
import urllib.error
import json

# Configuration
INPUT_DIR = "input_pdf"
OUTPUT_DIR = "split_pdf"
LOG_FILE = "pdf-split.log"
LARGE_FILE_THRESHOLD = 45 * 1024 * 1024  # 45MB
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"


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


def extract_isbn_from_filename(filename):
    """
    Extract ISBN from filename.

    Expected formats:
    - ISBN13_任意.pdf
    - ISBN13.pdf
    - ISBN-13-with-hyphens_任意.pdf

    Args:
        filename: PDF filename (e.g., "978-1493221851_SAP_Analytics_Cloud.pdf")

    Returns:
        str: 13-digit ISBN (hyphens removed), or None if not found/invalid

    Raises:
        ValueError: If ISBN format is invalid
    """
    # Remove extension and get the base name
    base = os.path.splitext(filename)[0]

    # Extract the first part before underscore (or the whole name if no underscore)
    parts = base.split('_')
    isbn_part = parts[0]

    # Remove hyphens
    isbn = isbn_part.replace('-', '')

    # Validate: must be 13 digits
    if not isbn:
        return None

    if not isbn.isdigit():
        raise ValueError(f"ISBN contains non-digit characters: {isbn_part}")

    if len(isbn) != 13:
        raise ValueError(f"ISBN must be 13 digits, got {len(isbn)}: {isbn_part}")

    return isbn


def fetch_metadata_from_google_books(isbn):
    """
    Fetch book metadata from Google Books API.

    Args:
        isbn: 13-digit ISBN string

    Returns:
        dict: Metadata with keys: parent_document, author, publisher,
              published_date, description, language
              Returns empty dict on API failure
    """
    url = GOOGLE_BOOKS_API_URL.format(isbn=isbn)

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as e:
        logging.error(f"Google Books API request failed: {e}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse Google Books API response: {e}")
        return {}
    except Exception as e:
        logging.error(f"Unexpected error fetching metadata: {e}")
        return {}

    if data.get('totalItems', 0) == 0:
        logging.warning(f"No book found for ISBN: {isbn}")
        return {}

    # Get the first (most relevant) result
    volume_info = data['items'][0].get('volumeInfo', {})

    metadata = {}

    # Title -> parent_document
    if volume_info.get('title'):
        title = volume_info['title']
        if volume_info.get('subtitle'):
            title += ': ' + volume_info['subtitle']
        metadata['parent_document'] = title

    # Authors (join multiple authors with ", ")
    if volume_info.get('authors'):
        metadata['author'] = ', '.join(volume_info['authors'])

    # Publisher
    if volume_info.get('publisher'):
        metadata['publisher'] = volume_info['publisher']

    # Published date
    if volume_info.get('publishedDate'):
        metadata['published_date'] = volume_info['publishedDate']

    # Description
    if volume_info.get('description'):
        metadata['description'] = volume_info['description']

    # Language
    if volume_info.get('language'):
        metadata['language'] = volume_info['language']

    logging.info(f"Fetched metadata for ISBN {isbn}: {metadata.get('parent_document', 'Unknown')}")

    return metadata
