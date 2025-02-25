import os
import requests
import json
import re

# API Configuration
PROJECT = "kommune"
BASE_DIR = "/Volumes/home/kommune"  # Root directory containing all archives
BASE_URL = "https://christian.tellusrapp.com"
API_URL = f"{BASE_URL}/tellusr/api/v1/{PROJECT}/update-many-docs"
AUTH = ("", "")

# Function to parse details.txt
def parse_details_file(details_file):
    data = {}
    authors = []

    with open(details_file, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line.startswith("DokumentID:"):
                data["id"] = line.split(": ", 1)[1]
            elif line.startswith("ArkivsakID:"):
                data["title"] = line.split(": ", 1)[1]
            elif line.startswith("Journaldato:"):
                data["journal_date"] = line.split(": ", 1)[1]
            elif line.startswith("Brevdato:"):
                data["letter_date"] = line.split(": ", 1)[1]
            elif line.startswith("Dokumentansvarlig:"):
                data["responsible_person"] = line.split(": ", 1)[1]
            elif line.startswith("Avsender(e):"):
                continue
            elif line and not re.match(r"^\w+: ", line):
                authors.append(line)

    data["authors"] = authors
    return data

# Function to find all attachments
def find_attachments(case_path):
    attachments = []
    for file_name in os.listdir(case_path):
        file_path = os.path.join(case_path, file_name)
        if os.path.isfile(file_path) and file_name.lower().endswith((".pdf", ".jpg", ".png", ".docx", ".xlsx")):
            attachments.append(file_name)
    return attachments

# Function to create the request payload
def create_payload(document):
    return {"docs": [document]}

# Function to upload a single document with retry on duplicate ID
def upload_document(document):
    headers = {"Content-Type": "application/json"}
    attempt = 1
    original_id = document["id"]

    while True:
        payload = create_payload(document)
        response = requests.post(API_URL, auth=AUTH, headers=headers, json=payload)

        if response.status_code == 200:
            print(f"✅ Successfully uploaded: {document['title']}")
            return True
        elif "duplicate ID" in response.text.lower():
            new_id = f"{original_id}-{attempt + 1}"
            print(f"⚠️ Duplicate ID detected for {original_id}. Retrying with new ID: {new_id}")
            document["id"] = new_id  # Append increasing suffix
            attempt += 1
        else:
            print(f"❌ Failed to upload: {document['title']} | Error: {response.text} (Status: {response.status_code})")
            return False

# Main function to process cases one by one
def process_all_cases():
    if not os.path.exists(BASE_DIR):
        print(f"❌ ERROR: Base directory not found: {BASE_DIR}")
        return

    print(f"🔍 Searching in: {BASE_DIR}")

    # Process each archive directory separately
    for archive_dir in os.listdir(BASE_DIR):
        archive_path = os.path.join(BASE_DIR, archive_dir)

        if not os.path.isdir(archive_path) or not archive_dir.startswith("archive-"):
            continue  # Skip non-archive directories

        print(f"\n📂 Processing archive: {archive_dir}")

        # Traverse subdirectories
        for root, dirs, files in os.walk(archive_path):
            if "details.txt" in files:
                details_file = os.path.join(root, "details.txt")
                details = parse_details_file(details_file)

                if not details.get("id") or not details.get("title"):
                    print(f"⚠️ Skipping {details_file}, missing required fields.")
                    continue

                attachments = find_attachments(root)

                print(f"\n📄 Found details.txt in: {root}")
                print(f"   ➡️ Document ID: {details['id']}")
                print(f"   ➡️ Title: {details['title']}")
                print(f"   📎 Attachments: {attachments if attachments else 'None'}")

                document = {
                    "id": details["id"],
                    "title": details["title"],
                    "authors": details["authors"],
                    "content": f"Document related to {details['title']}",
                    "content_segmented": [{"content_segment": f"Details for {details['title']}"}],
                    "yourField1": "example",
                    "yourField2": [],
                    "yourField3": {},
                    "attachments": attachments,
                }

                # Upload one document at a time
                upload_document(document)

# Run the script
if __name__ == "__main__":
    process_all_cases()
