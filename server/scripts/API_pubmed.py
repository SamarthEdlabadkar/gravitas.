import requests
import xml.etree.ElementTree as ET
import csv
import re
import time
from typing import List, Dict, Any, Optional

# --- Config ---
NCBI_API_URL = r"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
OUTPUT_CSV_FILENAME = r"server\static\extracted_article_data.csv"
INPUT_CSV_FILENAME = r"server\static\publications.csv"
TARGET_SECTIONS = ["Abstract", "Introduction", "Methods", "Results", "Discussion", "Outcomes", "Conclusion"]
# ---------------

def get_pmcid_from_url(url):
    match = re.search(r'(PMC\d+)', url, re.IGNORECASE)
    return match.group(1) if match else None

def extract_text(element: Optional[ET.Element]) -> str:
    """
    Extracts all  content from an XML element
    """
    if element is None:
        return ""
    text_parts = [text.strip() for text in element.itertext() if text and text.strip()]
    return " ".join(text_parts)

def extract_article_section(root: ET.Element, title_pattern):
    
    lower_pattern = title_pattern.lower()

    if lower_pattern == "abstract":
        return extract_text(root.find(".//abstract"))
    
    # General Outcomes
    if lower_pattern == "outcomes" or lower_pattern == "general outcomes":
        outcomes_elem = root.find(".//sec[@id='s4']")
        return extract_text(outcomes_elem)

    # Conclusion
    if lower_pattern == "conclusion":
        conclusion_elem = root.find(".//sec[@id='s5']")
        if conclusion_elem is not None:
            return extract_text(conclusion_elem)
        
    # Partial title match
    for title_elem in root.findall('.//sec/title'):
        if title_elem.text and lower_pattern in title_elem.text.lower():
            return extract_text(title_elem)

    # Sec-type attribute
    sec_elem = root.find(f".//sec[@sec-type='{lower_pattern}']")
    if sec_elem is not None:
        return extract_text(sec_elem)

    return ""

def fetch_and_parse_article(pmcid):
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
            root = ET.fromstring(xml_content)
            
            # Core Metadata
            article_title = extract_text(root.find(".//article-title"))
            journal_title = extract_text(root.find(".//journal-title"))
            doi = root.findtext(".//article-id[@pub-id-type='doi']")
            pub_year = root.findtext(".//pub-date/year")

            # Authors
            authors = []
            for contrib in root.findall(".//contrib-group/contrib[@contrib-type='author']"):
                surname = contrib.findtext(".//surname")
                given_names = contrib.findtext(".//given-names")
                initial = given_names.split()[0][0] if given_names else ''
                authors.append(f"{surname}, {initial}")
            author_list = "; ".join(authors)

            # Article Sections
            data_sections = {}
            for section in TARGET_SECTIONS:
                data_sections[section] = extract_article_section(root, section)
            
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
            
        except Exception as e:
            print(f"[{pmcid}] : Error occurred: {e}")
        
        if attempt < max_retries - 1:
            time.sleep(retry_delay * (2 ** attempt)) # Really dont want to get blacklisted
        
    print(f"[{pmcid}] Failed to process")
    return {"PMC_ID": pmcid, "Error": "Failed to fetch or parse data"}


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
    print(f"Input file not found")
except Exception as e:
    print(f"Error reading input CSV")

print(f"Found {len(articles_to_fetch)} PMC IDs")
output_fieldnames = [
    "PMC_ID", "DOI", "Title", "Journal", "Year", "Authors", 
    *TARGET_SECTIONS, 
    "Title_Input", "Link_Input", "Error"
]

processed_data: List[Dict[str, Any]] = []

for i, article in enumerate(articles_to_fetch):
    pmcid = article['PMC_ID']
    print(f"--- Processing {i + 1}/{len(articles_to_fetch)}: {pmcid} ---")
    data = fetch_and_parse_article(pmcid)
    data['Title_Input'] = article['Title_Input']
    data['Link_Input'] = article['Link_Input']
    
    processed_data.append(data)
    
    time.sleep(0.5) # Lets not get blacklisted

try:
    with open(OUTPUT_CSV_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=output_fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(processed_data)

    print(f"Data successfully saved")

except Exception as e:
    print(f"Error occurred: {e}")