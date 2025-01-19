import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from random import randint
from urllib.parse import urljoin

BASE_URL = "https://vagan.kommune.no/innsyn.aspx"
DATE_FORMAT = "%Y-%m-%d"
OUTPUT_DIR = "./archive"
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

def sanitize_filename(name):
    """Sanitize filename by removing invalid characters."""
    name = " ".join(name.split())  # Remove excess whitespace
    return "".join(c if c.isalnum() or c in " ._-()" else "_" for c in name).replace("/", "-")

def extract_case_links(soup):
    """Extracts all 'Gå til journalposten' links from the soup."""
    return [urljoin(BASE_URL, a['href']) for a in soup.find_all('a', string='Gå til journalposten', href=True)]

def extract_pagination_links(soup):
    """Extracts pagination links from the current page."""
    return [urljoin(BASE_URL, a['href']) for a in soup.find_all('a', href=True) if a.text.isdigit() or a.text.lower() == 'neste']

def write_details_file(details_path, content):
    """Write the details file with a trailing newline."""
    with open(details_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n\n")  # Ensure trailing newline

def parse_case_details(case_html, is_censored, censor_reason=None):
    """Parses and formats case details into plain text."""
    soup = BeautifulSoup(case_html, "html.parser")

    # Extract table data
    details = []
    table = soup.find("table", class_="table hh i-bgw two")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            header = row.find("th").get_text(strip=True)
            value = " ".join(row.find("td").get_text(strip=True).split())  # Clean up line breaks and spaces
            details.append(f"{header.strip(':')}: {value}")  # Ensure no trailing colons in the header

    # Extract Avsender(e)
    sender_section = soup.find("h2", string="Avsender(e)")
    if sender_section:
        sender_div = sender_section.find_next("div", class_="dokmottakere")
        if sender_div:
            sender_text = sender_div.get_text(separator="\n", strip=True)
            details.append("\nAvsender(e):\n" + sender_text + "\n")

    # Extract Tekstdokument or add censor reason
    if is_censored:
        details.append(f"\nTekstdokument\n{censor_reason}")
    else:
        document_section = soup.find("h2", string="Tekstdokument")
        if document_section:
            document_list = document_section.find_next("ul", class_="innsyn_dok")
            if document_list:
                documents = document_list.find_all("a", href=True)
                document_titles = [doc.get_text(strip=True) for doc in documents]
                details.extend(document_titles)

    return "\n".join(details)


def process_case(case_url, date_dir):
    """Process a single case by downloading its details and documents."""
    case_html = fetch_page(case_url)
    soup = BeautifulSoup(case_html, "html.parser")

    journalpostid = case_url.split("journalpostid=")[1].split("&")[0]
    tekstdokument = soup.find("h2", string="Tekstdokument")
    is_censored = False
    censor_reason = None
    if tekstdokument:
        censor_text = tekstdokument.find_next("div", class_="content-text")
        if censor_text and "ikke offentlig" in censor_text.get_text():
            is_censored = True
            censor_reason = censor_text.get_text(strip=True)

    arkivsak_row = soup.find("th", string=lambda x: x and "ArkivsakID" in x)
    if arkivsak_row:
        arkivsak_id = " ".join(arkivsak_row.find_next("td").get_text(strip=True).split())
    else:
        arkivsak_id = "Unknown ID"

    case_dir_name = sanitize_filename(f"{journalpostid} - {arkivsak_id}")
    case_dir = os.path.join(date_dir, case_dir_name)
    if os.path.exists(case_dir):
        log(f"  {journalpostid}: Already processed.")
        return

    os.makedirs(case_dir, exist_ok=True)

    case_details = parse_case_details(case_html, is_censored, censor_reason)
    log(f"  {journalpostid}: {arkivsak_id}")

    details_path = os.path.join(case_dir, "details.txt")
    write_details_file(details_path, case_details)

    if not is_censored:
        document_links = soup.select(".innsyn_dok a")
        for link in document_links:
            file_url = urljoin(case_url, link['href'])
            file_name = sanitize_filename(link.get_text(strip=True))
            file_path = os.path.join(case_dir, file_name + ".pdf")
            try:
                doc_content = requests.get(file_url, headers=HEADERS).content
                with open(file_path, "wb") as f:
                    f.write(doc_content)
                log(f"    - {file_name}")
            except Exception as e:
                log(f"    - Error downloading document: {file_url} - {e}")

def process_date(date_url, date):
    log(date.strftime("%Y-%m-%d"))
    date_dir = os.path.join(OUTPUT_DIR, date.strftime("%Y/%m/%d"))
    os.makedirs(date_dir, exist_ok=True)

    while date_url:
        page_content = fetch_page(date_url)
        soup = BeautifulSoup(page_content, "html.parser")
        case_links = extract_case_links(soup)
        for case_link in case_links:
            process_case(case_link, date_dir)

        pagination_links = extract_pagination_links(soup)
        date_url = pagination_links[-1] if pagination_links and "neste" in pagination_links[-1].lower() else None

def main():
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    current_date = start_date

    while current_date <= end_date:
        date_url = f"{BASE_URL}?response=journalpost_postliste&MId1=731&scripturi=/innsyn.aspx&skin=infolink&fradato={current_date.strftime(DATE_FORMAT)}T00:00:00"
        try:
            process_date(date_url, current_date)
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
