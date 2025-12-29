#!/usr/bin/env python3
"""
PDF Splitter - Split large PDFs by bookmarks or manually specified ranges.

Usage:
    python pdf-split.py                           # Process all PDFs in input_pdf/
    python pdf-split.py document.pdf              # Process a single PDF
    python pdf-split.py -o custom_output          # Specify output directory
    python pdf-split.py --background              # Run without GUI prompts
"""

import os
import sys
import argparse
import logging
import time
import tkinter as tk
from tkinter import simpledialog
from pathlib import Path
import fitz  # PyMuPDF

from common import (
    INPUT_DIR, OUTPUT_DIR, LARGE_FILE_THRESHOLD,
    setup_logging, load_progress, save_progress,
    estimate_time, clean_filename
)


class PdfSplitter:
    """Handles splitting large PDFs by bookmarks or page ranges."""

    def __init__(self, pdf_path):
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(self.pdf_path)

    @property
    def page_count(self):
        return self.doc.page_count

    def split_smart(self, output_dir):
        """
        Smart split based on document structure:
        - L2 = Chapter (Primary split)
        - L3 = Section (Secondary if L2 > 50 pages)
        - Force split if > 50 pages and no L3
        """
        toc = self.doc.get_toc()
        if not toc:
            return None

        l2_indices = [i for i, x in enumerate(toc) if x[0] == 2]
        if not l2_indices:
            l2_indices = [i for i, x in enumerate(toc) if x[0] == 1]
            if not l2_indices:
                return None

        ranges = []

        first_node_start = toc[l2_indices[0]][2] - 1
        if first_node_start > 0:
            ranges.append((0, first_node_start - 1, "00_Frontmatter"))

        for i, idx in enumerate(l2_indices):
            node = toc[idx]
            lvl, title, _ = node[:3]

            next_l2_idx = l2_indices[i + 1] if i < len(l2_indices) - 1 else len(toc)

            start_page = node[2] - 1

            if next_l2_idx < len(toc):
                end_page = toc[next_l2_idx][2] - 1 - 1
            else:
                end_page = self.doc.page_count - 1

            page_count = end_page - start_page + 1
            safe_title = clean_filename(title)

            THRESHOLD = 50
            if page_count > THRESHOLD:
                children = []
                for k in range(idx + 1, next_l2_idx):
                    child = toc[k]
                    if child[0] == lvl + 1:
                        children.append((k, child))

                if children:
                    first_child_start = children[0][1][2] - 1
                    if first_child_start > start_page:
                        ranges.append((start_page, first_child_start - 1, f"{safe_title}_Intro"))

                    for j, (pidx, child_node) in enumerate(children):
                        c_title = child_node[1]
                        c_start = child_node[2] - 1

                        if j < len(children) - 1:
                            c_end = children[j + 1][1][2] - 1 - 1
                        else:
                            c_end = end_page

                        c_len = c_end - c_start + 1
                        c_safe_title = clean_filename(c_title)

                        if c_len > THRESHOLD:
                            self._add_forced_splits(ranges, c_start, c_end, c_safe_title, THRESHOLD)
                        else:
                            ranges.append((c_start, c_end, c_safe_title))
                else:
                    self._add_forced_splits(ranges, start_page, end_page, safe_title, THRESHOLD)
            else:
                ranges.append((start_page, end_page, safe_title))

        return self._save_ranges(ranges, output_dir)

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

        for p in parts:
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

            ranges.append((start - 1, end - 1, f"Part_{start}-{end}"))

        return self._save_ranges(ranges, output_dir)

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
            ranges.append((current, end, f"Part_{part:03d}"))
            current = end + 1
            part += 1

        return self._save_ranges(ranges, output_dir)

    def _save_ranges(self, ranges, output_dir):
        """Save page ranges as separate PDF files."""
        files = []
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, (start, end, title) in enumerate(ranges):
            new_doc = fitz.open()
            new_doc.insert_pdf(self.doc, from_page=start, to_page=end)

            safe_title = clean_filename(title)[:50]
            fname = f"{i:03d}_{safe_title}.pdf"
            fpath = output_dir / fname

            new_doc.save(fpath)
            new_doc.close()
            files.append(fpath)
            logging.info(f"Created chunk: {fname} (Pages {start + 1}-{end + 1})")

        return files

    def close(self):
        """Close the PDF document."""
        self.doc.close()


def split_pdf(pdf_path, output_dir, background_mode=False, force_split=False):
    """
    Split a single PDF file.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Output directory for split files
        background_mode: If True, skip GUI prompts
        force_split: If True, split even small files

    Returns:
        List of paths to split PDF files
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_size = pdf_path.stat().st_size

    if not force_split and file_size < LARGE_FILE_THRESHOLD:
        logging.info(f"File {pdf_path.name} is small ({file_size / 1024 / 1024:.2f} MB). No split needed.")
        return [pdf_path]

    logging.info(f"File {pdf_path.name} is {file_size / 1024 / 1024:.2f} MB. Initiating split...")

    splitter = PdfSplitter(pdf_path)
    try:
        chunks = splitter.split_by_bookmarks(output_dir)
        if not chunks:
            logging.warning("No suitable bookmarks found for splitting.")
            if not background_mode:
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
                    logging.info("No ranges specified. Splitting by 50 pages.")
                    chunks = splitter.split_by_pages(50, output_dir)
            else:
                logging.info("Background mode: Splitting by 50 pages.")
                chunks = splitter.split_by_pages(50, output_dir)
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
  python pdf-split.py --force              Force split even small files
  python pdf-split.py --background         Run without GUI prompts
        """
    )
    parser.add_argument("pdf", nargs="?",
                        help="Path to PDF file (optional, processes all PDFs in input_pdf/ if not specified)")
    parser.add_argument("-o", "--output", default=OUTPUT_DIR,
                        help=f"Output directory for split PDFs (default: {OUTPUT_DIR})")
    parser.add_argument("--force", action="store_true",
                        help="Force split even if file is small")
    parser.add_argument("--background", action="store_true",
                        help="Run in background mode (no GUI prompts)")
    args = parser.parse_args()

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

    progress = load_progress()
    start_time = time.time()
    processed_count = 0
    total_count = len(pdfs)

    for pdf in pdfs:
        name = pdf.stem
        logging.info(f"Processing: {pdf.name}")

        if name in progress and progress[name].get("status") == "done" and not args.force:
            logging.info(f"Skipping {name} (already processed). Use --force to reprocess.")
            processed_count += 1
            estimate_time(start_time, processed_count, total_count)
            continue

        pdf_output_dir = output_dir / name
        chunks = split_pdf(pdf, pdf_output_dir, args.background, args.force)

        progress[name] = {
            "status": "done",
            "chunks": len(chunks),
            "output_dir": str(pdf_output_dir)
        }
        save_progress(progress)

        logging.info(f"Split into {len(chunks)} chunk(s)")
        processed_count += 1
        estimate_time(start_time, processed_count, total_count)

    logging.info("=== PDF Splitter Completed ===")


if __name__ == "__main__":
    main()
