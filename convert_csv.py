#!/usr/bin/env python3
"""
H5P Course Planner CSV Converter
=================================

Converts a multi-level course planning spreadsheet (exported as CSV) into
the flat hierarchical format expected by h5p_downloader.py.

Input format (course planner spreadsheet exported to CSV)
---------------------------------------------------------
- Rows 1–3 : Header / metadata rows (skipped automatically)
- Row 4+   : Data rows with the following column layout:

    Col 0  : (unused / row index)
    Col 1  : Course name
    Col 2  : Module name
    Col 3  : Section name
    Col 4  : Sub-section name  (becomes the "section" in output)
    Col 5  : Unit name         (used as the filename base)
    Col 6  : H5P content URL

Output format
-------------
CSV with columns: course, module, section, unit, content_url

Usage
-----
    python convert_csv.py <input_file.csv>
    python convert_csv.py "Course_Planner_2025.csv"

The output file is saved alongside the input with '_formatted' appended:
    Course_Planner_2025_formatted.csv
"""

import csv
import sys
import os
import re


def is_h5p_url(url: str) -> bool:
    """Return True if the URL points to an H5P content item."""
    # Matches any h5p.com hosted URL containing /content/
    return bool(re.search(r'h5p\.com/content/', url, re.IGNORECASE))


def convert_csv(input_file: str) -> str | None:
    """
    Convert a course planner CSV to the hierarchical format for h5p_downloader.

    Parameters
    ----------
    input_file : str
        Path to the raw course planner CSV.

    Returns
    -------
    str | None
        Path to the generated output file, or None on failure.
    """
    if not os.path.exists(input_file):
        print(f"Error: File not found — {input_file}")
        return None

    print(f"Reading: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        rows = list(csv.reader(f))

    print(f"Total rows: {len(rows)}")

    base_name   = os.path.splitext(input_file)[0]
    output_file = f"{base_name}_formatted.csv"

    # Output rows — start with header
    output_rows = [['course', 'module', 'section', 'unit', 'content_url']]

    # State tracking — values carry forward when cells are blank
    last_course     = ''
    last_module     = ''
    last_section    = ''
    last_subsection = ''

    h5p_count    = 0
    skipped_zip  = 0
    skipped_other = 0

    # Skip the first 3 header/metadata rows (index 0–2)
    for i, row in enumerate(rows[3:], start=4):
        # Need at least 7 columns and a non-empty URL column (index 6)
        if len(row) < 7 or not row[6].strip():
            continue

        if len(row) > 1 and row[1].strip():
            last_course = row[1].strip()
        if len(row) > 2 and row[2].strip():
            last_module = row[2].strip()
        if len(row) > 3 and row[3].strip():
            last_section = row[3].strip()
        if len(row) > 4 and row[4].strip():
            last_subsection = row[4].strip()  # sub-section becomes the folder-level "section"

        unit = row[5].strip() if len(row) > 5 else ''
        url  = row[6].strip()

        if is_h5p_url(url):
            output_rows.append([last_course, last_module, last_subsection, unit, url])
            h5p_count += 1
        elif url.lower().endswith('.zip') or '.zip' in url.lower():
            skipped_zip += 1
            print(f"  [SKIP] ZIP at row {i}: {unit or url}")
        else:
            skipped_other += 1

    # Write output file
    print(f"\nWriting: {output_file}")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(output_rows)

    # Summary
    print(f"\n{'='*60}")
    print("CONVERSION SUMMARY")
    print(f"{'='*60}")
    print(f"  Input file    : {input_file}")
    print(f"  Output file   : {output_file}")
    print(f"  H5P entries   : {h5p_count}")
    print(f"  ZIP (skipped) : {skipped_zip}")
    print(f"  Other skipped : {skipped_other}")
    print(f"{'='*60}")

    if h5p_count > 0:
        print("\nSample entries:")
        for j, row in enumerate(output_rows[1:4], 1):
            print(f"  {j}. [{row[0]}] {row[1]} / {row[2]} / {row[3]}")
        if h5p_count > 3:
            print(f"  ... and {h5p_count - 3} more")

    print(f"\nDone! Output: {output_file}")
    return output_file


def main():
    print("=" * 60)
    print("H5P Course CSV Converter")
    print("=" * 60)
    print()

    if len(sys.argv) < 2:
        print("Usage:   python convert_csv.py <input_csv_file>")
        print()
        print("Example:")
        print('  python convert_csv.py "Course_Planner_2025.csv"')
        print()
        print("Output: <input_file>_formatted.csv")
        sys.exit(1)

    output = convert_csv(sys.argv[1])

    if output:
        print()
        print("Next steps:")
        print(f"  1. Update config.json → set 'csv_file' to '{os.path.basename(output)}'")
        print("  2. Run: python h5p_downloader.py --config config.json")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
