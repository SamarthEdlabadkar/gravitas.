import requests
import csv
from datetime import datetime
import time
import json

# --- Config ---
BASE_URL = "https://visualization.osdr.nasa.gov/biodata/api"
START_ID = 1
END_ID = 883
OUTPUT_FILE = "dataset_summary_all_OSD.csv"
CSV_HEADERS = ["accession_number", "study_title", "study_authors_combined", "study_description", "study_public_release_date_unix","study_public_release_date_readable"]
# ---------------------

def custom_reverse_whitespace_cleanup(text: str) -> str:
    """
    Applies the custom whitespace cleanup logic: iterates in reverse, removing 
    all single whitespaces but preserving one in a double-whitespace sequence.
    """
    if not text:
        return text

    # Reverse the string and convert it to a list of characters
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
    Returns a dictionary of cleaned data or None if fail.
    If dates is in 1969 set "N/A".
    """
    url = f"{BASE_URL}/v2/dataset/{accession_number}/"
    
    try:
        response = requests.get(url, timeout=25)
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
            if release_unix < 0:
                release_unix = 'N/A'
            else:
                release_readable = datetime.fromtimestamp(release_unix).strftime('%Y-%m-%d %H:%M:%S')
        if release_readable == 'N/A':
            release_unix = 'N/A'
            
        print(f"Processed {accession_number}")
        
        
        return {
            "accession_number": accession_number,
            "study_title": title,
            "study_authors_combined": authors_combined,
            "study_description": description,
            "study_public_release_date_unix": release_unix,
            "study_public_release_date_readable": release_readable
        }

    except (requests.exceptions.RequestException, ValueError, json.JSONDecodeError, KeyError) as e:
        return None

skipped_count = 0
successful_count = 0

# Check if the output file exists to determine if we should write headers
try:
    with open(OUTPUT_FILE, 'r') as f:
        write_headers = False
except FileNotFoundError:
    # File does not exist, write headers
    write_headers = True

with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as csvfile:
    csv_writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
    if write_headers:
        csv_writer.writeheader()

    print(f"Extraction from OSD-{START_ID} to OSD-{END_ID}...")

    for i in range(START_ID, END_ID + 1):
        accession = f"OSD-{i}"
        data_row = get_and_clean_metadata(accession)
        
        if data_row:
            csv_writer.writerow(data_row)
            successful_count += 1
        else:
            skipped_count += 1
        time.sleep(0.1) #sleep so that you dont get black listed for DoS lol

print("\n" + "=" * 50)
print(f"Total datasets in range: {END_ID - START_ID + 1}")
print(f"Successful: {successful_count}")
print(f"Failed: {skipped_count}")
print("=" * 50)
