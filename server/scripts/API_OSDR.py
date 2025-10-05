import requests
import csv
from datetime import datetime
import time
import json
import sys 

# --- Configuration ---
BASE_URL = "https://visualization.osdr.nasa.gov/biodata/api"
# Define the range of datasets to process
START_ID = 1
END_ID = 883

# Output file name and extension (all results will be appended to this file)
OUTPUT_FILE = "dataset_summary_all_OSD.csv"

# Define the column names for the CSV file (must be consistent)
CSV_HEADERS = [
    "accession_number", 
    "study_title", 
    "study_authors_combined", 
    "study_description", 
    "study_public_release_date_unix",
    "study_public_release_date_readable"
]
# ---------------------

def custom_reverse_whitespace_cleanup(text: str) -> str:
    """
    Applies the custom whitespace cleanup logic: iterates in reverse, removing 
    all single whitespaces but preserving one in a double-whitespace sequence.
    """
    if not text:
        return text

    # Reverse the string and convert it to a list of characters for manipulation
    chars = list(text[::-1])
    cleaned_chars_reverse = []
    prev_was_whitespace = False
    first_whitespace_removed = False

    for char in chars:
        if char == ' ':
            if prev_was_whitespace:
                # This is the second of two repeating whitespaces. Keep one.
                cleaned_chars_reverse.append(char)
                prev_was_whitespace = False
            else:
                # This is the first whitespace or a single one. Remove it.
                if not first_whitespace_removed:
                    first_whitespace_removed = True
                else:
                    pass  # Don't append the char
                
                prev_was_whitespace = True
        else:
            # Regular character, keep it.
            cleaned_chars_reverse.append(char)
            prev_was_whitespace = False

    # Join the reversed list and reverse it back to the original order
    return "".join(cleaned_chars_reverse)[::-1]


def get_and_clean_metadata(accession_number: str) -> dict | None:
    """
    Fetches and cleans metadata for a single accession number.
    Returns a dictionary of cleaned data or None on failure.
    Includes logic to set 1969 dates (negative Unix timestamps) to "N/A".
    """
    url = f"{BASE_URL}/v2/dataset/{accession_number}/"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status() 
        dataset_data = response.json()
        
        # Access the main metadata object
        metadata = dataset_data.get(accession_number, {}).get('metadata', {})
        
        if not metadata:
            raise ValueError(f"Metadata block is empty for {accession_number}.")

        # --- Extraction and Cleaning ---
        
        title = metadata.get('study title', 'N/A')
        
        # Authors
        study_person = metadata.get('study person', {})
        first_names = study_person.get('first name', '')
        last_names = study_person.get('last name', '')
        authors_combined = f"{first_names} {last_names}".strip().replace("  ", " ")

        # Description
        description_list = metadata.get('study description', [])
        temp_description = " ".join(s.strip() for s in description_list if s is not None).strip()
        description = custom_reverse_whitespace_cleanup(temp_description)

        # Date Conversion and 1969 Check
        release_unix = metadata.get('study public release date', 'N/A')
        release_readable = 'N/A'
        
        if isinstance(release_unix, int):
            # The Unix epoch starts Jan 1, 1970 (timestamp 0)
            # Negative values indicate times before the epoch (e.g., in 1969)
            if release_unix < 0:
                # Skip 1969 dates (negative timestamps) by setting to N/A
                release_unix = 'N/A'
            else:
                # Convert valid Unix timestamp
                release_readable = datetime.fromtimestamp(release_unix).strftime('%Y-%m-%d %H:%M:%S')
        
        # Ensure the Unix time is "N/A" if the readable time is "N/A" (e.g., if it was < 0)
        if release_readable == 'N/A':
            release_unix = 'N/A'
        print(f"Processed {accession_number} successfully.")

        # Prepare the data dictionary
        return {
            "accession_number": accession_number,
            "study_title": title,
            "study_authors_combined": authors_combined,
            "study_description": description,
            "study_public_release_date_unix": release_unix,
            "study_public_release_date_readable": release_readable
        }

    except (requests.exceptions.RequestException, ValueError, json.JSONDecodeError, KeyError) as e:
        # A failed request (404, 500, timeout) or data parsing error
        return None


def run_bulk_extraction():
    """
    Iterates through the dataset range, collects data, and writes to a single CSV file.
    """
    
    skipped_count = 0
    successful_count = 0
    
    # Check if the output file exists to determine if we should write headers
    try:
        with open(OUTPUT_FILE, 'r') as f:
            # File exists, do not write headers
            write_headers = False
    except FileNotFoundError:
        # File does not exist, write headers
        write_headers = True

    # Use 'a' mode to append to the file
    with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
        
        if write_headers:
            csv_writer.writeheader()

        print(f"Starting bulk extraction from OSD-{START_ID} to OSD-{END_ID}...")
        print(f"Results will be written to: {OUTPUT_FILE}")

        for i in range(START_ID, END_ID + 1):
            accession = f"OSD-{i}"
            
            # Fetch and process metadata
            data_row = get_and_clean_metadata(accession)
            
            if data_row:
                csv_writer.writerow(data_row)
                successful_count += 1
                # Prints a status update every 50 records
                if successful_count % 50 == 0:
                     print(f"✅ Processed {accession} ({successful_count} total successful)")
            else:
                skipped_count += 1
                # Prints a skipped status immediately
                # print(f"❌ Skipped {accession} (Not Accessible/Error)")
            
            # Add a small delay for API etiquette
            time.sleep(0.1)

    print("\n" + "=" * 50)
    print("BULK PROCESSING COMPLETE")
    print(f"Total datasets in range: {END_ID - START_ID + 1}")
    print(f"Successful records written to CSV: {successful_count}")
    print(f"Skipped/Failed to access files count: {skipped_count}")
    print("=" * 50)

if __name__ == "__main__":
    run_bulk_extraction()