import requests
import time
import os
import csv  # Import the csv library
import re   # Import re for regular expression matching

# --- Configuration (Mandatory: Fill these out) ---
# NCBI requests that you provide an email and tool name. 
# Providing an API key (obtainable via your NCBI account) significantly 
# increases the request rate limit from 3 to 10 requests per second.
USER_EMAIL = "krishkalathiya@gmail.com"  # <-- REQUIRED: Replace with your email
TOOL_NAME = "MyPmcDownloaderScript"   # <-- REQUIRED: A descriptive name for your script
API_KEY = "75b9ccde4088e853b8412e19287673d80e08"   

# --- Constants ---
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
DB_NAME = "pmc"
BATCH_SIZE = 250  # Number of IDs per API request (max is 10,000, but 250 is safer for stability)
DELAY_SECONDS = 1.0 # Delay between batches (1 sec is safe for unkeyed requests)
INPUT_FILE = "pmc_data.csv" # Updated to CSV file name
OUTPUT_DIR = "downloaded_pmc_xml"

def extract_pmcid_from_url(url):
    """
    Extracts the numerical PMC ID from a full PMC article URL.
    E.g., "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4136787/" -> "4136787"
    """
    # Regex to find the PMC ID which follows /PMC(\d+)/
    match = re.search(r'PMC(\d+)', url, re.IGNORECASE)
    if match:
        # Return the captured group (the digits)
        return match.group(1)
    return None

def read_pmc_ids(filename):
    """Reads IDs from the CSV file, extracting the PMC ID from the URL column (index 1)."""
    print(f"Reading data from CSV file: {filename}...")
    pmc_ids = []
    
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            
            # Skip header row
            try:
                # Store header, assuming the first row is the header
                header = next(reader) 
                if len(header) < 2:
                    print(f"Warning: CSV header has fewer than two columns. Proceeding assuming header is: {header}")
            except StopIteration:
                print(f"Error: CSV file '{filename}' is empty.")
                return []
            
            # Process data rows
            # We start line counting from 2 (after the header)
            for i, row in enumerate(reader, 2): 
                if len(row) < 2:
                    print(f"Skipping line {i}: Row does not have a URL column (second column).")
                    continue
                
                url = row[1].strip() # URL is consistently in the second column (index 1)
                pmcid = extract_pmcid_from_url(url)
                
                if pmcid:
                    pmc_ids.append(pmcid)
                else:
                    # Log the row that failed to parse
                    print(f"Warning: Could not extract PMC ID from URL on line {i}: {url}")

        print(f"Successfully extracted {len(pmc_ids)} valid PMC IDs.")
        return pmc_ids
        
    except FileNotFoundError:
        print(f"Error: Input file '{filename}' not found. Please ensure your CSV is named '{filename}'.")
        return []

def fetch_and_save_articles(pmc_ids):
    """Fetches articles in batches and saves the raw XML."""
    if not pmc_ids:
        print("No valid PMC IDs found to process.")
        return

    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

    total_ids = len(pmc_ids)
    # Calculate number of batches needed
    num_batches = (total_ids + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Total IDs to fetch: {total_ids}. Processing in {num_batches} batches (Size: {BATCH_SIZE}).")

    successful_fetches = 0
    
    for i in range(num_batches):
        start_index = i * BATCH_SIZE
        end_index = min(start_index + BATCH_SIZE, total_ids)
        batch = pmc_ids[start_index:end_index]
        batch_ids_str = ",".join(batch)
        
        print(f"\n--- Starting Batch {i + 1}/{num_batches} (IDs {start_index + 1} to {end_index}) ---")

        # API Parameters
        params = {
            "db": DB_NAME,
            "id": batch_ids_str,
            "retmode": "xml",     # Retrieve in XML format
            "rettype": "full",    # Retrieve the full article (including text)
            "email": USER_EMAIL,  # Required by NCBI for bulk operations
            "tool": TOOL_NAME     # Required by NCBI for bulk operations
        }
        
        # Add API key if provided
        if API_KEY:
            params["api_key"] = API_KEY
            print("Using API key for enhanced rate limit.")
        
        # --- Make the API Request ---
        try:
            response = requests.get(BASE_URL, params=params, timeout=30)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            
            # --- Save the Response ---
            # Save the entire batch response as a single XML file
            output_filename = os.path.join(OUTPUT_DIR, f"pmc_batch_{i+1:03d}.xml")
            with open(output_filename, "w", encoding="utf-8") as outfile:
                outfile.write(response.text)
            
            print(f"Successfully saved XML for {len(batch)} articles to: {output_filename}")
            successful_fetches += len(batch)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching batch {i + 1}: {e}")
            print("Skipping batch and moving to the next one.")
        
        # --- Rate Limiting Delay ---
        if i < num_batches - 1:
            print(f"Waiting {DELAY_SECONDS} seconds before next batch...")
            time.sleep(DELAY_SECONDS)

    print("\n--- Download Complete ---")
    print(f"Total successful article records fetched: {successful_fetches}")
    print(f"Check the '{OUTPUT_DIR}' directory for your XML files.")


if __name__ == "__main__":
    # Check for mandatory configuration
    if USER_EMAIL == "your.email@example.com":
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("! ERROR: Please edit pmc_downloader.py and set USER_EMAIL and TOOL_NAME. !")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    else:
        # Step 1: Read the IDs
        pmc_ids = read_pmc_ids(INPUT_FILE)
        
        # Step 2: Fetch and save the data
        fetch_and_save_articles(pmc_ids)
