#!/usr/bin/env python
# AI Summary: A CLI tool for splitting a PDF into multiple files based on specified page ranges.
# It uses `argparse` and `pypdf`, automatically adds a .pdf extension to filenames if missing.
# Output filenames can be provided or auto-generated.
# Usage: python pdfsplit.py <source.pdf> -p "1-5;6;7-10" [-f "p1;p2;p3"]
import argparse
import os
import sys
from pypdf import PdfReader, PdfWriter

def split_pdf(input_file, page_ranges_str, filenames_str):
    """
    Splits a PDF into multiple files based on given page ranges.
    If filenames are not provided, they are auto-generated.
    """
    # Parse page ranges, which can be 'start-end' or a single page number 'page'.
    try:
        valid_page_ranges = []
        raw_ranges = [r.strip() for r in page_ranges_str.split(';') if r.strip()]
        for r_str in raw_ranges:
            if '-' in r_str:
                parts = r_str.split('-')
                if len(parts) != 2:
                    raise ValueError(f"Invalid range '{r_str}'. It should be in 'start-end' format.")
                start, end = map(int, parts)
                if start > end:
                    print(f"Warning: In range '{r_str}', start page {start} is after end page {end}. Skipping this range.")
                    continue
                valid_page_ranges.append((start, end))
            else:
                page = int(r_str)
                valid_page_ranges.append((page, page))
    except ValueError as e:
        print(f"Error: Invalid page range format. Use 'start-end' or 'page', separated by ';'.\nDetails: {e}")
        sys.exit(1)

    # Handle filenames
    if filenames_str:
        filenames_raw = [f.strip() for f in filenames_str.split(';')]
        if len(valid_page_ranges) != len(filenames_raw):
            print("Error: The number of valid page ranges must match the number of provided output filenames.")
            sys.exit(1)
        # Ensure all provided filenames have a .pdf extension
        filenames = [f if f.lower().endswith('.pdf') else f + '.pdf' for f in filenames_raw]
    else:
        # Auto-generate filenames if not provided
        filenames = []
        base_name, _ = os.path.splitext(input_file)
        for start, end in valid_page_ranges:
            if start == end:
                filenames.append(f"{base_name}_page_{start}.pdf")
            else:
                filenames.append(f"{base_name}_pages_{start}_{end}.pdf")

    try:
        reader = PdfReader(input_file)
        total_pages = len(reader.pages)

        # Process each range and create a new PDF
        for (start_page, end_page), output_name in zip(valid_page_ranges, filenames):
            # User inputs are 1-based, library is 0-based.
            # A range '1-4' should include pages 1, 2, 3, 4.
            # This corresponds to indices 0, 1, 2, 3.
            start_index = start_page - 1
            end_index = end_page

            if not (0 <= start_index < end_index <= total_pages):
                print(f"Warning: Page range {start_page}-{end_page} is invalid for a PDF with {total_pages} pages. Skipping.")
                continue

            writer = PdfWriter()
            for i in range(start_index, end_index):
                writer.add_page(reader.pages[i])
            
            with open(output_name, 'wb') as output_pdf:
                writer.write(output_pdf)
            
            print(f"✅ Successfully created '{output_name}' with pages {start_page}-{end_page}.")

    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="A CLI tool to split a PDF into multiple files based on page ranges.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("filename", help="The path to the source PDF file. The .pdf extension is added if missing.")
    
    parser.add_argument(
        "-p", "--pages",
        required=True,
        help="A string of page ranges to extract, separated by semicolons.\nCan be a range (e.g., '1-4'), or a single page (e.g., '5').\nExample: \"1-4;5;12-16\""
    )

    parser.add_argument(
        "-f", "--filenames",
        help="A string of output filenames, corresponding to the page ranges.\nIf not provided, filenames will be auto-generated. The .pdf extension is added if missing.\nExample: \"chapter1;chapter2.pdf;chapter3\""
    )

    args = parser.parse_args()
    
    input_filename = args.filename
    if not input_filename.lower().endswith('.pdf'):
        input_filename += '.pdf'
    
    split_pdf(input_filename, args.pages, args.filenames)


if __name__ == "__main__":
    main()
