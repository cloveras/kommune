import os
import requests
import json
import re

# API Configuration
PROJECT = "kommune"
BASE_DIR = "/Volumes/home/kommune"  # Root directory containing all archives
BASE_URL = "https://christian.tellusrapp.com"
API_DOCS_URL = f"{BASE_URL}/tellusr/api/v1/{PROJECT}/update-many-docs"
API_UPLOAD_URL = f"{BASE_URL}/tellusr/api/v1/{PROJECT}/upload-file"
AUTH = ("", "")

# Function to parse details.txt
def parse_details_file(details_file):
    data = {}
    authors = []

    with open(details_file, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line.startswith("DokumentID:"):
                data["id"] = line.split(": ", 1)[1]  # This ID will be used for both metadata & attachments
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

# Function to find all attachments and assign suffixes
def find_attachments(case_path, base_id):
    attachments = []
    file_list = [f for f in os.listdir(case_path) if os.path.isfile(os.path.join(case_path, f))]

    # Filter for valid file types
    valid_files = [f for f in file_list if f.lower().endswith((".pdf", ".jpg", ".png", ".docx", ".xlsx"))]

    for index, file_name in enumerate(valid_files, start=1):
        file_path = os.path.join(case_path, file_name)
        attachment_id = f"{base_id}-{index}"  # Assign -1, -2, -3, etc.
        attachments.append((attachment_id, file_path))

    return attachments

# Function to upload a single file using /upload-file
def upload_file(file_path, doc_id):
    file_name = os.path.basename(file_path)
    print(f"📤 Uploading attachment: {file_name} as {doc_id}...")

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

# Function to create the request payload for metadata
def create_payload(document):
    return {"docs": [document]}

# Function to upload document metadata with retry on duplicate ID
def upload_document(document):
    headers = {"Content-Type": "application/json"}
    attempt = 1
    original_id = document["id"]

    while True:
        payload = create_payload(document)
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

                base_id = details["id"]  # Use this ID for both metadata & files
                attachments = find_attachments(root, base_id)

                print(f"\n📄 Found details.txt in: {root}")
                print(f"   ➡️ Document ID: {base_id}")
                print(f"   ➡️ Title: {details['title']}")
                print(f"   📎 Attachments: {[f[1] for f in attachments] if attachments else 'None'}")

                # Upload attachments first, and collect file names
                uploaded_files = []
                for attachment_id, file_path in attachments:
                    uploaded_file = upload_file(file_path, attachment_id)
                    if uploaded_file:
                        uploaded_files.append(uploaded_file)

                # Create document metadata payload
                document = {
                    "id": base_id,
                    "title": details["title"],
                    "authors": details["authors"],
                    "content": f"Document related to {details['title']}",
                    "content_segmented": [{"content_segment": f"Details for {details['title']}"}],
                    "yourField1": "example",
                    "yourField2": [],
                    "yourField3": {},
                    "attachments": uploaded_files,  # Reference uploaded file names
                }

                # Upload metadata after attachments
                upload_document(document)

# Run the script
if __name__ == "__main__":
    process_all_cases()
