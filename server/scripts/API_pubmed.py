import requests
import xml.etree.ElementTree as ET
import csv
import re
import time
from typing import List, Dict, Any, Optional

# --- Configuration ---
NCBI_API_URL = r"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
OUTPUT_CSV_FILENAME = r"server\static\extracted_article_data.csv"
INPUT_CSV_FILENAME = r"server\static\publications.csv"

# Define the sections we want to extract from the XML body
TARGET_SECTIONS = [
    "Abstract", "Introduction", "Methods", "Results", 
    "Discussion", "Outcomes", "Conclusion"
]

def get_pmcid_from_url(url: str) -> Optional[str]:
    """
    Extracts the PMC ID (e.g., PMC4136787) from a PubMed Central URL.
    The pattern is usually /articles/PMC<number>/ or /PMC<number>
    """
    match = re.search(r'(PMC\d+)', url, re.IGNORECASE)
    return match.group(1) if match else None

def extract_text(element: Optional[ET.Element]) -> str:
    """
    Extracts all text content from an XML element, including text from nested tags.
    """
    if element is None:
        return ""
    
    # Use itertext() to get all text nodes from the element and its descendants
    # and join them, stripping whitespace from individual text parts.
    text_parts = [text.strip() for text in element.itertext() if text and text.strip()]
    return " ".join(text_parts)

def extract_article_section(root: ET.Element, title_pattern: str) -> str:
    """
    Locates a section by its title or sec-type and extracts its full text content.
    The section tag is often <sec>, but the abstract is <abstract>.
    """
    lower_pattern = title_pattern.lower()

    # Handle the Abstract section specifically (it's not always in a <sec> tag)
    if lower_pattern == "abstract":
        return extract_text(root.find(".//abstract"))
    
    # Handle General Outcomes (based on the previous inspection, it was sec id="s4")
    if lower_pattern == "outcomes" or lower_pattern == "general outcomes":
        outcomes_elem = root.find(".//sec[@id='s4']")
        return extract_text(outcomes_elem)

    # Handle Conclusion (based on the previous inspection, it was sec id="s5")
    if lower_pattern == "conclusion":
        conclusion_elem = root.find(".//sec[@id='s5']")
        # Fallback to general finding by title if the specific ID is not present
        if conclusion_elem is not None:
            return extract_text(conclusion_elem)
        
    # 1. Try finding by partial title match
    for title_elem in root.findall('.//sec/title'):
        if title_elem.text and lower_pattern in title_elem.text.lower():
            return extract_text(title_elem)

    # 2. Try finding by sec-type attribute
    sec_elem = root.find(f".//sec[@sec-type='{lower_pattern}']")
    if sec_elem is not None:
        return extract_text(sec_elem)

    return ""

def fetch_and_parse_article(pmcid: str) -> Dict[str, Any]:
    """
    Fetches XML for a given PMC ID and parses it into a dictionary of data.
    """
    params = {
        "db": "pmc",
        "id": pmcid,
        "retmode": "xml"
    }
    
    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            r = requests.get(NCBI_API_URL, params=params, timeout=30)
            r.raise_for_status()
            xml_content = r.text
            
            # Use ElementTree to parse the XML
            root = ET.fromstring(xml_content)
            
            # --- 1. Extract Core Metadata ---
            article_title = extract_text(root.find(".//article-title"))
            journal_title = extract_text(root.find(".//journal-title"))
            doi = root.findtext(".//article-id[@pub-id-type='doi']")
            pub_year = root.findtext(".//pub-date/year")

            # Authors (join first name initial and surname)
            authors = []
            for contrib in root.findall(".//contrib-group/contrib[@contrib-type='author']"):
                surname = contrib.findtext(".//surname")
                given_names = contrib.findtext(".//given-names")
                initial = given_names.split()[0][0] if given_names else ''
                authors.append(f"{surname}, {initial}")
            author_list = "; ".join(authors)

            # --- 2. Extract Article Sections ---
            data_sections = {}
            for section in TARGET_SECTIONS:
                data_sections[section] = extract_article_section(root, section)
            
            # Combine all extracted data
            article_data = {
                "PMC_ID": pmcid,
                "DOI": doi,
                "Title": article_title,
                "Journal": journal_title,
                "Year": pub_year,
                "Authors": author_list,
                **data_sections
            }
            
            return article_data
            
        except requests.exceptions.RequestException as e:
            print(f"[{pmcid}] Request Error (Attempt {attempt + 1}/{max_retries}): {e}")
        except ET.ParseError:
            print(f"[{pmcid}] XML Parse Error (Attempt {attempt + 1}/{max_retries}): Malformed XML returned.")
        except Exception as e:
            print(f"[{pmcid}] An unexpected error occurred: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(retry_delay * (2 ** attempt)) # Exponential backoff
        
    print(f"[{pmcid}] Failed to process article after {max_retries} attempts.")
    return {"PMC_ID": pmcid, "Error": "Failed to fetch or parse data"}


def main():
    """
    Main function to orchestrate reading input CSV, fetching data, and writing output CSV.
    """
    print(f"Reading article list from {INPUT_CSV_FILENAME}...")
    articles_to_fetch = []
    
    try:
        with open(INPUT_CSV_FILENAME, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                pmcid = get_pmcid_from_url(row['Link'])
                if pmcid:
                    articles_to_fetch.append({
                        "Title_Input": row['Title'],
                        "Link_Input": row['Link'],
                        "PMC_ID": pmcid
                    })
                else:
                    print(f"Warning: Could not find PMC ID in link: {row['Link']}")

    except FileNotFoundError:
        print(f"Error: Input file '{INPUT_CSV_FILENAME}' not found. Please create it first.")
        return
    except Exception as e:
        print(f"Error reading input CSV: {e}")
        return

    print(f"Found {len(articles_to_fetch)} PMC IDs to process.")
    
    # Prepare header for output CSV
    output_fieldnames = [
        "PMC_ID", "DOI", "Title", "Journal", "Year", "Authors", 
        *TARGET_SECTIONS, 
        "Title_Input", "Link_Input", "Error"
    ]
    
    processed_data: List[Dict[str, Any]] = []

    for i, article in enumerate(articles_to_fetch):
        pmcid = article['PMC_ID']
        print(f"--- Processing {i + 1}/{len(articles_to_fetch)}: {pmcid} ---")
        
        # Fetch and parse the data
        data = fetch_and_parse_article(pmcid)
        
        # Add the input data columns
        data['Title_Input'] = article['Title_Input']
        data['Link_Input'] = article['Link_Input']
        
        processed_data.append(data)
        
        # Be polite to the API
        time.sleep(0.5)

    # --- Write to CSV ---
    print(f"\nWriting results to {OUTPUT_CSV_FILENAME}...")
    try:
        with open(OUTPUT_CSV_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=output_fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(processed_data)

        print(f"✅ All data successfully saved to {OUTPUT_CSV_FILENAME}")

    except Exception as e:
        print(f"An error occurred while writing the CSV file: {e}")

if __name__ == "__main__":
    main()
