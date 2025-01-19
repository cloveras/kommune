import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from random import randint
from urllib.parse import urljoin
import sys

# Supported kommune configurations
KOMMUNE_CONFIG = {
    "vagan": {
        "base_url": "https://vagan.kommune.no/innsyn.aspx",
        "mid": "731",
        "output_dir": "./archive-vagan"
    },
    "vestvagoy": {
        "base_url": "https://www.vestvagoy.kommune.no/innsyn.aspx",
        "mid": "531",
        "output_dir": "./archive-vestvagoy"
    },
    "moskenes": {
        "base_url": "https://moskenes.kommune.no/innsyn.aspx",
        "mid": "364",
        "output_dir": "./archive-moskenes"
    },
    "flakstad": {
        "base_url": "https://flakstad.kommune.no/innsyn.aspx",
        "mid": "261",
        "output_dir": "./archive-flakstad"
    }
}

DATE_FORMAT = "%Y-%m-%d"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

def log(message):
    """Log a message."""
    print(message)

def fetch_page(url):
    """Fetch a page and return its HTML content."""
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text

def sanitize_string(value):
    """Sanitize string by normalizing whitespace and removing line breaks."""
    return " ".join(value.replace("\n", " ").split())

def sanitize_filename(name):
    """Sanitize filename by removing invalid characters."""
    name = sanitize_string(name)
    return "".join(c if c.isalnum() or c in " ._-()" else "_" for c in name).replace("/", "-")

def extract_case_links(soup, base_url):
    """Extracts all 'Gå til journalposten' links from the soup."""
    return [urljoin(base_url, a['href']) for a in soup.find_all('a', string='Gå til journalposten', href=True)]

def extract_pagination_links(soup, base_url):
    """Extracts pagination links from the current page."""
    return [urljoin(base_url, a['href']) for a in soup.find_all('a', href=True) if a.text.isdigit() or a.text.lower() == 'neste']

def write_details_file(details_path, content):
    """Write the details file with a trailing newline."""
    with open(details_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n\n")  # Ensure trailing newline

def download_documents(documents, case_dir):
    """Download all documents for the case."""
    doc_names = []
    for doc in documents:
        doc_url = doc["href"]
        doc_name = sanitize_filename(doc.get_text(strip=True))
        doc_path = os.path.join(case_dir, doc_name)
        try:
            response = requests.get(doc_url, headers=HEADERS)
            response.raise_for_status()
            with open(doc_path, "wb") as f:
                f.write(response.content)
            doc_names.append(doc_name)
            log(f"        - {doc_name}")
        except Exception as e:
            log(f"        - Failed: {doc_url}: {e}")
    return doc_names

def parse_case_details(case_html, sanitized_arkivsak_id, is_censored, censor_reason=None):
    """Parse and format case details into plain text."""
    soup = BeautifulSoup(case_html, "html.parser")

    # Extract table data
    details = []
    table = soup.find("table", class_="table hh i-bgw two")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            header = row.find("th").get_text(strip=True).rstrip(":")
            value = sanitize_string(row.find("td").get_text(strip=True))
            if header == "ArkivsakID":
                details.append(f"{header}: {sanitized_arkivsak_id}")
            else:
                details.append(f"{header}: {value}")

    # Extract sender
    sender_section = soup.find("h2", string="Avsender(e)")
    if sender_section:
        sender_div = sender_section.find_next("div", class_="dokmottakere")
        if sender_div:
            sender_text = sender_div.get_text(separator="\n", strip=True)
            details.append("\nAvsender(e):\n" + sender_text + "\n")

    # Add documents
    if is_censored:
        details.append("\nTekstdokument\n" + censor_reason)
    else:
        document_section = soup.find("h2", string="Tekstdokument")
        if document_section:
            document_list = document_section.find_next("ul", class_="innsyn_dok")
            if document_list:
                documents = document_list.find_all("a", href=True)
                document_titles = [doc.get_text(strip=True) for doc in documents]
                details.extend(document_titles)

    return "\n".join(details)

def process_case(case_url, date_dir, base_url, force=False):
    """Process a single case by downloading its details and documents."""
    case_html = fetch_page(case_url)
    soup = BeautifulSoup(case_html, "html.parser")

    journalpostid = case_url.split("journalpostid=")[1].split("&")[0]
    arkivsak_row = soup.find("th", string=lambda x: x and "ArkivsakID" in x)
    if arkivsak_row:
        arkivsak_id_raw = arkivsak_row.find_next("td").get_text(separator=" ", strip=True)
        arkivsak_id = sanitize_string(arkivsak_id_raw)
    else:
        log(f"  {journalpostid}: ArkivsakID not found, skipping case.")
        return

    case_dir_name = sanitize_filename(f"{journalpostid} {arkivsak_id}")
    case_dir = os.path.join(date_dir, case_dir_name)
    if os.path.exists(case_dir) and not force:
        log(f"  {journalpostid}: Already processed.")
        return

    os.makedirs(case_dir, exist_ok=True)

    # Determine censorship
    tekstdokument = soup.find("h2", string="Tekstdokument")
    is_censored = False
    censor_reason = None
    documents = []
    if tekstdokument:
        censor_text = tekstdokument.find_next("div", class_="content-text")
        if censor_text and "ikke offentlig" in censor_text.get_text():
            is_censored = True
            censor_reason = censor_text.get_text(strip=True)
        else:
            document_list = tekstdokument.find_next("ul", class_="innsyn_dok")
            if document_list:
                documents = document_list.find_all("a", href=True)

    # Download documents
    downloaded_files = download_documents(documents, case_dir)

    # Parse and write details
    case_details = parse_case_details(case_html, arkivsak_id, is_censored, censor_reason)
    details_path = os.path.join(case_dir, "details.txt")
    write_details_file(details_path, case_details)

    # Log progress
    log(f"  {journalpostid}: {arkivsak_id}")

def process_date(kommune_config, date, force=False):
    """Processes a specific date URL, including all paginated pages."""
    base_url = kommune_config["base_url"]
    date_url = f"{base_url}?response=journalpost_postliste&MId1={kommune_config['mid']}&scripturi=/innsyn.aspx&skin=infolink&fradato={date.strftime(DATE_FORMAT)}T00:00:00"
    log(date.strftime("%Y-%m-%d"))
    date_dir = os.path.join(kommune_config["output_dir"], date.strftime("%Y/%m/%d"))
    os.makedirs(date_dir, exist_ok=True)

    while date_url:
        page_content = fetch_page(date_url)
        soup = BeautifulSoup(page_content, "html.parser")

        # Extract case links from the current page
        case_links = extract_case_links(soup, base_url)
        for case_link in case_links:
            process_case(case_link, date_dir, base_url, force)

        # Find the "neste" link and continue pagination
        next_link = soup.find("a", string="neste")
        if next_link:
            date_url = urljoin(base_url, next_link["href"])
        else:
            date_url = None

def main():
    if len(sys.argv) < 4:
        print("Usage: python download.py <kommune> <start-date> <stop-date> [-f]")
        print(f"Supported kommune names: {', '.join(KOMMUNE_CONFIG.keys())}")
        return

    kommune = sys.argv[1].lower()
    start_date = datetime.strptime(sys.argv[2], DATE_FORMAT)
    stop_date = datetime.strptime(sys.argv[3], DATE_FORMAT)
    force = "-f" in sys.argv

    if kommune not in KOMMUNE_CONFIG:
        print(f"Error: Unknown kommune '{kommune}'. Supported kommune names: {', '.join(KOMMUNE_CONFIG.keys())}")
        return

    kommune_config = KOMMUNE_CONFIG[kommune]

    current_date = start_date
    while current_date <= stop_date:
        try:
            process_date(kommune_config, current_date, force)
            if randint(1, 3) == 1:
                sleep_time = randint(1, 5)
                log(f"(Sleeping {sleep_time} seconds)")
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            log("Script stopped by user")
            break
        except Exception as e:
            log(f"Error processing date {current_date}: {e}")
        current_date += timedelta(days=1)

if __name__ == "__main__":
    main()
