import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from random import randint
from urllib.parse import urljoin
import sys
import argparse
import magic

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

def parse_case_details(case_html, sanitized_arkivsak_id, is_censored, censor_reason=None, downloaded_files=None):
    """Parse and format case details into plain text."""
    soup = BeautifulSoup(case_html, "html.parser")
    details = []

    # Extract table data
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
    elif downloaded_files:
        details.extend(downloaded_files)

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
    if tekstdokument:
        censor_text = tekstdokument.find_next("div", class_="content-text")
        if censor_text and "ikke offentlig" in censor_text.get_text():
            is_censored = True
            censor_reason = censor_text.get_text(strip=True)

    # Log case details
    log(f"  {journalpostid}: {arkivsak_id}")

    # Download documents and prepare file list
    downloaded_files = []
    if not is_censored:
        document_section = soup.find("h2", string="Tekstdokument")
        if document_section:
            document_list = document_section.find_next("ul", class_="innsyn_dok")
            if document_list:
                documents = document_list.find_all("a", href=True)
                for doc in documents:
                    file_url = urljoin(case_url, doc['href'])
                    original_name = sanitize_filename(doc.get_text(strip=True))

                    try:
                        # Fetch file
                        response = requests.get(file_url, headers=HEADERS, stream=True)
                        response.raise_for_status()

                        # Use MIME type detection to determine the correct suffix
                        mime = magic.Magic(mime=True)
                        mime_type = mime.from_buffer(response.content[:4096])
                        ext = mime_type.split("/")[-1]
                        ext = f".{ext}" if ext else ".bin"

                        # Add the extension if not already present
                        if not original_name.endswith(ext):
                            original_name += ext

                        file_path = os.path.join(case_dir, original_name)

                        # Avoid overwriting existing files unless forced
                        if os.path.exists(file_path) and not force:
                            log(f"    - Skipping duplicate: {os.path.basename(file_path)}")
                            continue

                        # Save the file
                        with open(file_path, "wb") as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)

                        log(f"    - {os.path.basename(file_path)}")
                        downloaded_files.append(os.path.basename(file_path))
                    except Exception as e:
                        log(f"    - Error downloading document: {file_url} - {e}")

    # Parse and write details
    case_details = parse_case_details(case_html, arkivsak_id, is_censored, censor_reason, downloaded_files)
    details_path = os.path.join(case_dir, "details.txt")
    write_details_file(details_path, case_details)

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
    parser = argparse.ArgumentParser(description="Download case data for a specified kommune and date range.")
    parser.add_argument("kommune", type=str, help="Name of the kommune (e.g., vagan, vestvagoy).")
    parser.add_argument("start_date", type=str, help="Start date in YYYY-MM-DD format.")
    parser.add_argument("stop_date", type=str, help="Stop date in YYYY-MM-DD format.")
    parser.add_argument("-f", "--force", action="store_true", help="Force re-download of existing data.")

    args = parser.parse_args()

    kommune = args.kommune.lower()
    start_date = args.start_date
    stop_date = args.stop_date
    force = args.force

    if kommune not in KOMMUNE_CONFIG:
        print(f"Error: Unknown kommune '{kommune}'. Supported kommune names: {', '.join(KOMMUNE_CONFIG.keys())}")
        return

    try:
        start_date = datetime.strptime(start_date, DATE_FORMAT)
        stop_date = datetime.strptime(stop_date, DATE_FORMAT)
    except ValueError as e:
        print(f"Error: Invalid date format. Dates must be in YYYY-MM-DD format. ({e})")
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
