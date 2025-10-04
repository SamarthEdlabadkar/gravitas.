import requests
import json
import time
import csv
from typing import Dict, Any, Optional, List

# --- Configuration ---
# Updated BASE_URL to target the metadata endpoint as requested
BASE_URL = "https://osdr.nasa.gov/osdr/data/osd/meta/"
START_INDEX = 1
END_INDEX = 883  # Iterating from 1 to 883 as in the original request
MAX_RETRIES = 3
DELAY_BETWEEN_RETRIES = 5  # seconds
OUTPUT_CSV_FILENAME = "nasa_osdr_metadata_live.csv" # Changed filename to reflect live writing

# Define the fields (header) for the CSV file
CSV_FIELDNAMES = ['osd_number', 'title', 'description', 'authorsList']

def fetch_metadata(index: int) -> Optional[Dict[str, Any]]:
    """
    Fetches and parses JSON metadata from the specified OSDR endpoint index with retry logic.

    Args:
        index (int): The OSD ID number to append to the BASE_URL.

    Returns:
        Optional[Dict[str, Any]]: The parsed JSON metadata dictionary on success, or None on failure.
    """
    url = f"{BASE_URL}{index}"
    print(f"\n--- Requesting URL: {url} (OSD ID {index} of {END_INDEX}) ---")

    for attempt in range(MAX_RETRIES):
        try:
            # Send the GET request with a timeout
            response = requests.get(url, timeout=10)

            # 1. Check for successful HTTP status code (e.g., 200 OK)
            if response.status_code == 200:
                print(f"Status: SUCCESS (200 OK)")

                # 2. Try to parse the response as JSON
                try:
                    data = response.json()
                    return data # Return the parsed data dictionary

                except json.JSONDecodeError:
                    print(f"Error: Could not decode JSON response for meta/{index}. Raw text: {response.text[:200]}...")
                    return None # Failed to decode JSON

            elif response.status_code == 404:
                print(f"Status: FAILED (404 Not Found) for meta/{index}. Endpoint may not exist.")
                return None # Stop retrying on 404

            else:
                # Handle other client/server errors
                print(f"Status: FAILED (HTTP {response.status_code}) for meta/{index}. Retrying...")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(DELAY_BETWEEN_RETRIES)
                else:
                    print(f"Error: Max retries reached for meta/{index}.")
                    return None

        except requests.exceptions.RequestException as e:
            # Handle network errors
            print(f"Connection Error for meta/{index} on attempt {attempt + 1}: {e}. Retrying in {DELAY_BETWEEN_RETRIES} seconds...")
            if attempt < MAX_RETRIES - 1:
                time.sleep(DELAY_BETWEEN_RETRIES)
            else:
                print(f"Fatal Error: Connection failed after {MAX_RETRIES} attempts for meta/{index}.")
                return None
    return None

def process_and_write_row(data: Dict[str, Any], osd_number: int, writer: csv.DictWriter, success_counter: list):
    """
    Extracts, formats, writes a single row to CSV, and prints the summary.
    """
    try:
        title = data.get('title', 'N/A')
        description = data.get('description', 'N/A')
        authors = data.get('authorsList', 'N/A')

        # --- CSV Preparation ---
        csv_row = {
            'osd_number': osd_number,
            'title': title,
            'description': description,
            # Convert the authors list to a semicolon-separated string
            'authorsList': "; ".join(authors) if isinstance(authors, list) else str(authors)
        }
        
        # Write the row to the CSV file
        writer.writerow(csv_row)
        success_counter[0] += 1

        # --- Terminal Summary (5 words of description) ---
        desc_words = description.split()
        summary_desc = " ".join(desc_words[:5]) + ("..." if len(desc_words) > 5 else "")
        author_count = len(authors) if isinstance(authors, list) else 0

        print(f"-> SUCCESS (OSD-{osd_number}): Wrote to CSV.")
        print(f"   [Summary] Title: '{title}' | Authors: {author_count} | Desc: '{summary_desc}'")

    except Exception as e:
        print(f"-> EXTRACTION/WRITE FAILED for OSD-{osd_number}. Error: {e}")
        # Note: Caller function will handle incrementing the fail_count
        raise # Re-raise to be caught by the main loop's error handling


if __name__ == "__main__":
    print(f"Starting programmatic metadata fetch and extraction from NASA OSDR for OSD IDs {START_INDEX} through {END_INDEX}...")
    print(f"Results will be written incrementally to '{OUTPUT_CSV_FILENAME}'.")

    success_count_list = [0] # Use a list to pass success count by reference to helper function
    fail_count = 0
    total_requests = END_INDEX - START_INDEX + 1

    # --- Setup CSV File Writing ---
    try:
        # Open the file once before the loop for incremental writing
        with open(OUTPUT_CSV_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDNAMES)
            writer.writeheader() # Write the header row once

            # --- Main Processing Loop ---
            for i in range(START_INDEX, END_INDEX + 1):
                fetched_data = fetch_metadata(i)

                if fetched_data:
                    try:
                        # Extract, write to CSV, and print summary
                        process_and_write_row(fetched_data, i, writer, success_count_list)

                    except Exception:
                        fail_count += 1
                else:
                    fail_count += 1
            
            # success_count is the first element of the list
            success_count = success_count_list[0] 

    except IOError as e:
        print(f"\nFATAL: Could not open or write to CSV file {OUTPUT_CSV_FILENAME}: {e}")
        success_count = success_count_list[0] # Get current count even if file failed later

    print("\n=============================================")
    print("Metadata Fetching and Extraction Process Complete.")
    print("=============================================")
    print(f"Total Requests Attempted: {total_requests}")
    print(f"Successfully Processed and Wrote to CSV: {success_count}")
    print(f"Failed Requests or Extraction Errors: {fail_count}")
    print(f"Final Data available in '{OUTPUT_CSV_FILENAME}'.")
    print("=============================================")
