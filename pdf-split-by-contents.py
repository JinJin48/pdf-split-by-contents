#!/usr/bin/env python3
"""
PDF Splitter - Split large PDFs by bookmarks or manually specified ranges.

Usage:
    python pdf-split.py                           # Process all PDFs in input_pdf/
    python pdf-split.py document.pdf              # Process a single PDF
    python pdf-split.py -o custom_output          # Specify output directory
    python pdf-split.py --background              # Run without GUI prompts (skip if no bookmarks)
    python pdf-split.py --no-split                # Skip PDFs without bookmarks
    python pdf-split.py --title "Book Title" --author "Author Name"  # Add metadata
"""

import os
import sys
import argparse
import logging
import time
import datetime
import tkinter as tk
from tkinter import simpledialog
from pathlib import Path
import fitz  # PyMuPDF

from common import (
    INPUT_DIR, OUTPUT_DIR, LARGE_FILE_THRESHOLD,
    setup_logging, estimate_time, clean_filename
)


class PdfSplitter:
    """Handles splitting large PDFs by bookmarks or page ranges."""

    def __init__(self, pdf_path, metadata=None):
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(self.pdf_path)
        self.metadata = metadata or {}

    @property
    def page_count(self):
        return self.doc.page_count

    def split_smart(self, output_dir):
        """
        Smart split based on document structure:
        - L3 = Section (Primary split)
        - L2 = Chapter (Fallback if no sections exist)

        Returns list of (start, end, title, chapter_num, chapter_title) tuples
        """
        toc = self.doc.get_toc()
        if not toc:
            return None

        l2_indices = [i for i, x in enumerate(toc) if x[0] == 2]
        if not l2_indices:
            l2_indices = [i for i, x in enumerate(toc) if x[0] == 1]
            if not l2_indices:
                return None

        # ranges: (start, end, safe_title, chapter_num, chapter_title)
        ranges = []
        total_chapters = len(l2_indices)

        first_node_start = toc[l2_indices[0]][2] - 1
        if first_node_start > 0:
            ranges.append((0, first_node_start - 1, "00_Contents", 0, "Contents"))

        for i, idx in enumerate(l2_indices):
            node = toc[idx]
            lvl, title, _ = node[:3]
            chapter_num = i + 1  # 1-based chapter number
            chapter_title = title

            next_l2_idx = l2_indices[i + 1] if i < len(l2_indices) - 1 else len(toc)

            start_page = node[2] - 1

            if next_l2_idx < len(toc):
                end_page = toc[next_l2_idx][2] - 1 - 1
            else:
                end_page = self.doc.page_count - 1

            safe_title = clean_filename(title)

            # Find child sections (Level 3)
            children = []
            for k in range(idx + 1, next_l2_idx):
                child = toc[k]
                if child[0] == lvl + 1:
                    children.append((k, child))

            if children:
                # Split by sections
                first_child_start = children[0][1][2] - 1
                if first_child_start > start_page:
                    ranges.append((start_page, first_child_start - 1, f"{safe_title}_Intro",
                                   chapter_num, chapter_title))

                for j, (pidx, child_node) in enumerate(children):
                    c_title = child_node[1]
                    c_start = child_node[2] - 1

                    if j < len(children) - 1:
                        c_end = children[j + 1][1][2] - 1 - 1
                    else:
                        c_end = end_page

                    c_safe_title = clean_filename(c_title)
                    ranges.append((c_start, c_end, c_safe_title, chapter_num, chapter_title))
            else:
                # No sections, keep as chapter
                ranges.append((start_page, end_page, safe_title, chapter_num, chapter_title))

        return self._save_ranges(ranges, output_dir, total_chapters)

    def _add_forced_splits(self, range_list, start, end, base_title, limit):
        """Force split large sections into smaller chunks."""
        current = start
        part = 1
        while current <= end:
            next_split = min(current + limit - 1, end)
            range_list.append((current, next_split, f"{base_title}_part{part}"))
            current = next_split + 1
            part += 1

    def split_by_bookmarks(self, output_dir):
        """Split PDF by bookmarks (alias for split_smart)."""
        return self.split_smart(output_dir)

    def split_manually(self, range_str, output_dir):
        """
        Split based on user-specified ranges.

        Args:
            range_str: String like '1-10, 11-20, 21-end'
            output_dir: Directory to save split PDFs
        """
        parts = range_str.split(',')
        ranges = []

        for idx, p in enumerate(parts):
            p = p.strip()
            if not p:
                continue

            if '-' in p:
                s, e = p.split('-')
                s = str(s).strip().lower()
                e = str(e).strip().lower()
            else:
                s = p
                e = p

            try:
                start = int(s)
            except ValueError:
                start = 1

            if e == 'end':
                end = self.doc.page_count
            else:
                try:
                    end = int(e)
                except ValueError:
                    end = self.doc.page_count

            part_num = len(ranges) + 1
            # Manual split: chapter_num=part_num, chapter_title=Part title
            ranges.append((start - 1, end - 1, f"Part_{start}-{end}", part_num, f"Part {start}-{end}"))

        total_parts = len(ranges)
        return self._save_ranges(ranges, output_dir, total_parts)

    def split_by_pages(self, pages_per_chunk, output_dir):
        """
        Split PDF into fixed-size chunks.

        Args:
            pages_per_chunk: Number of pages per output file
            output_dir: Directory to save split PDFs
        """
        ranges = []
        total_pages = self.doc.page_count

        current = 0
        part = 1
        while current < total_pages:
            end = min(current + pages_per_chunk - 1, total_pages - 1)
            ranges.append((current, end, f"Part_{part:03d}", part, f"Part {part:03d}"))
            current = end + 1
            part += 1

        total_parts = len(ranges)
        return self._save_ranges(ranges, output_dir, total_parts)

    def _save_ranges(self, ranges, output_dir, total_chapters=0):
        """Save page ranges as separate PDF files with YAML metadata."""
        files = []
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        split_date = datetime.date.today().isoformat()
        total_splits = len(ranges)

        for i, range_data in enumerate(ranges):
            # Unpack range data (backward compatible)
            if len(range_data) == 3:
                start, end, title = range_data
                chapter_num, chapter_title = i + 1, title
            else:
                start, end, title, chapter_num, chapter_title = range_data

            new_doc = fitz.open()
            new_doc.insert_pdf(self.doc, from_page=start, to_page=end)

            safe_title = clean_filename(title)[:50]
            fname = f"{i:03d}_{safe_title}.pdf"
            fpath = output_dir / fname

            new_doc.save(fpath)
            new_doc.close()
            files.append(fpath)

            # Generate YAML metadata file
            self._write_metadata_yaml(
                fpath, i + 1, total_splits, chapter_num, chapter_title, total_chapters, split_date
            )

            logging.info(f"Created chunk: {fname} (Pages {start + 1}-{end + 1})")

        return files

    def _write_metadata_yaml(self, pdf_path, split_index, total_splits,
                              chapter_num, chapter_title, total_chapters, split_date):
        """Write YAML metadata file for a split PDF."""
        yaml_path = pdf_path.with_suffix('.yaml')

        # Build metadata dict with only specified values
        meta = {}

        # Parent document info (always included)
        meta['parent_document'] = self.pdf_path.name

        # Book metadata (only if specified)
        if self.metadata.get('title'):
            meta['parent_title'] = self.metadata['title']
        if self.metadata.get('isbn'):
            meta['isbn'] = self.metadata['isbn']
        if self.metadata.get('author'):
            meta['author'] = self.metadata['author']
        if self.metadata.get('publisher'):
            meta['publisher'] = self.metadata['publisher']
        if self.metadata.get('published_date'):
            meta['published_date'] = self.metadata['published_date']
        if self.metadata.get('genre'):
            meta['genre'] = self.metadata['genre']
        if self.metadata.get('description'):
            meta['description'] = self.metadata['description']

        # Split info (always included)
        meta['chapter_number'] = chapter_num
        meta['chapter_title'] = chapter_title
        meta['total_chapters'] = total_chapters
        meta['split_index'] = split_index
        meta['split_date'] = split_date

        # Write YAML manually (avoid PyYAML dependency)
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write('---\n')
            for key, value in meta.items():
                # Handle special characters in values
                if isinstance(value, str) and any(c in value for c in ':#{}[]&*?|-<>=!%@\\'):
                    f.write(f'{key}: "{value}"\n')
                else:
                    f.write(f'{key}: {value}\n')
            f.write('---\n')

        logging.info(f"Created metadata: {yaml_path.name}")

    def close(self):
        """Close the PDF document."""
        self.doc.close()


def split_pdf(pdf_path, output_dir, background_mode=False, no_split=False, metadata=None):
    """
    Split a single PDF file.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Output directory for split files
        background_mode: If True, skip GUI prompts
        no_split: If True, skip files without bookmarks
        metadata: Optional dict with book metadata (title, isbn, author, etc.)

    Returns:
        List of paths to split PDF files, or None if skipped
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_size = pdf_path.stat().st_size

    if file_size < LARGE_FILE_THRESHOLD:
        logging.info(f"File {pdf_path.name} is small ({file_size / 1024 / 1024:.2f} MB). No split needed.")
        return [pdf_path]

    logging.info(f"File {pdf_path.name} is {file_size / 1024 / 1024:.2f} MB. Initiating split...")

    splitter = PdfSplitter(pdf_path, metadata)
    try:
        chunks = splitter.split_by_bookmarks(output_dir)
        if not chunks:
            logging.warning("No suitable bookmarks found for splitting.")
            if no_split or background_mode:
                logging.warning(f"Skipping '{pdf_path.name}' - no bookmarks available.")
                return None
            else:
                root = tk.Tk()
                root.withdraw()
                page_count = splitter.page_count
                range_str = simpledialog.askstring(
                    "Large PDF Split",
                    f"'{pdf_path.name}' has no bookmarks.\n"
                    f"Total Pages: {page_count}\n\n"
                    f"Enter split ranges (e.g. '1-50, 51-100, 101-end'):"
                )
                root.destroy()
                if range_str:
                    chunks = splitter.split_manually(range_str, output_dir)
                else:
                    logging.warning(f"Skipping '{pdf_path.name}' - no ranges specified.")
                    return None
    except Exception as e:
        logging.error(f"Split failed: {e}")
        import traceback
        logging.error(traceback.format_exc())
        chunks = [pdf_path]
    finally:
        splitter.close()

    return chunks


def main():
    parser = argparse.ArgumentParser(
        description="PDF Splitter - Split large PDFs by bookmarks or page ranges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf-split.py                      Process all PDFs in input_pdf/
  python pdf-split.py document.pdf         Split a single PDF
  python pdf-split.py -o output_folder     Specify output directory
  python pdf-split.py --background         Run without GUI prompts (skip if no bookmarks)
  python pdf-split.py --no-split           Skip PDFs without bookmarks
  python pdf-split.py --title "Book Title" --author "Author Name"  Add metadata
        """
    )
    parser.add_argument("pdf", nargs="?",
                        help="Path to PDF file (optional, processes all PDFs in input_pdf/ if not specified)")
    parser.add_argument("-o", "--output", default=OUTPUT_DIR,
                        help=f"Output directory for split PDFs (default: {OUTPUT_DIR})")
    parser.add_argument("--background", action="store_true",
                        help="Run in background mode (no GUI prompts, skip if no bookmarks)")
    parser.add_argument("--no-split", action="store_true",
                        help="Skip PDFs without bookmarks instead of prompting")

    # Metadata options
    parser.add_argument("--title", help="Book title (defaults to filename if not specified)")
    parser.add_argument("--isbn", help="ISBN (13 digits)")
    parser.add_argument("--author", help="Author name")
    parser.add_argument("--publisher", help="Publisher name")
    parser.add_argument("--published-date", help="Publication date (YYYY-MM-DD format)")
    parser.add_argument("--genre", help="Genre/category")
    parser.add_argument("--description", help="Book description/summary")

    args = parser.parse_args()

    # Build metadata dict from CLI options
    metadata = {
        'title': args.title,
        'isbn': args.isbn,
        'author': args.author,
        'publisher': args.publisher,
        'published_date': args.published_date,
        'genre': args.genre,
        'description': args.description,
    }

    setup_logging(args.background)
    logging.info("=== PDF Splitter Started ===")

    output_dir = Path(args.output)

    if args.pdf:
        pdfs = [Path(args.pdf)]
    else:
        input_path = Path(INPUT_DIR)
        if not input_path.exists():
            input_path.mkdir(exist_ok=True)
            logging.info(f"Created input directory: {input_path}")
        pdfs = list(input_path.glob("*.pdf"))

    if not pdfs:
        logging.warning(f"No PDFs found. Place PDF files in '{INPUT_DIR}/' folder.")
        return

    start_time = time.time()
    processed_count = 0
    total_count = len(pdfs)

    for pdf in pdfs:
        logging.info(f"Processing: {pdf.name}")

        pdf_output_dir = output_dir / pdf.stem
        chunks = split_pdf(pdf, pdf_output_dir, args.background, args.no_split, metadata)

        if chunks is None:
            logging.info(f"Skipped: {pdf.name}")
        else:
            logging.info(f"Split into {len(chunks)} chunk(s)")
        processed_count += 1
        estimate_time(start_time, processed_count, total_count)

    logging.info("=== PDF Splitter Completed ===")


if __name__ == "__main__":
    main()
