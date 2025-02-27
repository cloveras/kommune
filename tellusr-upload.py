import os
import requests
import json
import re
import traceback

# API Configuration
PROJECT = "kommune"
BASE_DIR = "/Volumes/home/kommune"  # Root directory containing all archives
BASE_URL = "https://christian.tellusrapp.com"
API_DOCS_URL = f"{BASE_URL}/tellusr/api/v1/{PROJECT}/update-many-docs"
API_UPLOAD_URL = f"{BASE_URL}/tellusr/api/v1/{PROJECT}/upload-file"
AUTH = ("", "")

# Path to progress log file
LOG_FILE = "uploaded_cases.log"


# Function to read processed cases from log file
def get_processed_cases():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as log:
            return set(log.read().splitlines())  # Load processed case paths
    return set()


# Function to save a processed case to the log
def mark_case_as_processed(case_path):
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(case_path + "\n")


# Function to parse details.txt with error handling
def parse_details_file(details_file):
    data = {}
    authors = []

    try:
        with open(details_file, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if ": " in line:  # Ensure the line has expected format before splitting
                    key, value = line.split(": ", 1)
                    if key == "DokumentID":
                        data["id"] = value
                    elif key == "ArkivsakID":
                        data["title"] = value
                    elif key == "Journaldato":
                        data["journal_date"] = value
                    elif key == "Brevdato":
                        data["letter_date"] = value
                    elif key == "Dokumentansvarlig":
                        data["responsible_person"] = value
                    elif key == "Avsender(e)":
                        continue  # Skip, next lines might contain authors
                elif line and not re.match(r"^\w+: ", line):  # No known prefix → assume author
                    authors.append(line)
                else:
                    print(f"⚠️ Skipping unrecognized line in {details_file}: {line}")

        data["authors"] = authors

        # Validate required fields
        if "id" not in data or "title" not in data:
            print(f"⚠️ Invalid details.txt: Missing required fields in {details_file}")
            return None  # Skip this case

    except Exception as e:
        print(f"❌ Error reading {details_file}: {e}")
        return None  # Skip this case

    return data


# Function to find attachments and assign suffixes
def find_attachments(case_path, base_id):
    attachments = []
    try:
        file_list = [
            f
            for f in os.listdir(case_path)
            if os.path.isfile(os.path.join(case_path, f))
        ]
        valid_files = [
            f
            for f in file_list
            if f.lower().endswith((".pdf", ".jpg", ".png", ".docx", ".xlsx"))
        ]

        for index, file_name in enumerate(valid_files, start=1):
            file_path = os.path.join(case_path, file_name)
            attachment_id = f"{base_id}-{index}"  # Assign -1, -2, -3, etc.
            attachments.append((attachment_id, file_path))

    except Exception as e:
        print(f"❌ Error finding attachments in {case_path}: {e}")

    return attachments


# Function to upload a single file using /upload-file
def upload_file(file_path, doc_id):
    file_name = os.path.basename(file_path)
    print(f"📤 Uploading attachment: {file_name} as {doc_id}...")

    try:
        with open(file_path, "rb") as file_data:
            files = {"file": (file_name, file_data)}
            params = {"id": doc_id, "saveCopy": "true", "generateThumbnail": "true"}
            response = requests.post(API_UPLOAD_URL, auth=AUTH, files=files, params=params)

        if response.status_code == 200:
            print(f"✅ Successfully uploaded: {file_name} (ID: {doc_id})")
            return file_name  # Return filename to reference in metadata
        else:
            print(f"❌ Failed to upload {file_name}: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error uploading file {file_name}: {e}")
        return None


# Function to upload document metadata with retry on duplicate ID
def upload_document(document):
    headers = {"Content-Type": "application/json"}
    attempt = 1
    original_id = document["id"]

    while True:
        try:
            payload = {"docs": [document]}
            response = requests.post(API_DOCS_URL, auth=AUTH, headers=headers, json=payload)

            if response.status_code == 200:
                print(f"✅ Successfully uploaded metadata: {document['title']} (ID: {document['id']})")
                return True
            elif "duplicate ID" in response.text.lower():
                new_id = f"{original_id}-{attempt + 1}"
                print(f"⚠️ Duplicate ID detected for {original_id}. Retrying with new ID: {new_id}")
                document["id"] = new_id  # Append increasing suffix
                attempt += 1
            else:
                print(f"❌ Failed to upload metadata: {document['title']} | Error: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Unexpected error uploading metadata: {e}")
            return False


# Main function to process cases one by one
def process_all_cases():
    processed_cases = get_processed_cases()  # Load progress
    print(f"🔍 Searching in: {BASE_DIR}")

    for archive_dir in os.listdir(BASE_DIR):
        archive_path = os.path.join(BASE_DIR, archive_dir)

        if not os.path.isdir(archive_path) or not archive_dir.startswith("archive-"):
            continue  # Skip non-archive directories

        print(f"\n📂 Processing archive: {archive_dir}")

        for root, dirs, files in os.walk(archive_path):
            if "details.txt" in files:
                if root in processed_cases:
                    print(f"⏭️ Skipping already processed case: {root}")
                    continue  # Skip already processed cases

                details_file = os.path.join(root, "details.txt")
                details = parse_details_file(details_file)
                if not details:
                    continue  # Skip if details.txt is invalid

                base_id = details["id"]
                attachments = find_attachments(root, base_id)

                print(f"\n📄 Found details.txt in: {root}")
                print(f"   ➡️ Document ID: {base_id}")
                print(f"   ➡️ Title: {details['title']}")
                print(f"   📎 Attachments: {[f[1] for f in attachments] if attachments else 'None'}")

                uploaded_files = []
                for attachment_id, file_path in attachments:
                    uploaded_file = upload_file(file_path, attachment_id)
                    if uploaded_file:
                        uploaded_files.append(uploaded_file)

                document = {
                    "id": base_id,
                    "title": details["title"],
                    "authors": details["authors"],
                    "content": f"Document related to {details['title']}",
                    "content_segmented": [{"content_segment": f"Details for {details['title']}"}],
                    "yourField1": "example",
                    "yourField2": [],
                    "yourField3": {},
                    "attachments": uploaded_files,
                }

                if upload_document(document):
                    mark_case_as_processed(root)  # Mark case as successfully processed


# Run the script
if __name__ == "__main__":
    process_all_cases()
