import requests
from openai import OpenAI
import logging
import os
from bs4 import BeautifulSoup

# Configuration and constants
BASE_URL = "https://codex.valiantys.com"
BEARER_TOKEN = ""
OPENAI_API_KEY = ""
MODEL = "gpt-4o"
PARENT_PAGE_ID = ""
OUTPUT_FOLDER = "sows"
MAX_PAGES = 300

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# Ensure the output folder exists
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def request_openai(text):
    """
    Translates text to a specified language using OpenAI.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                { 
                    "role": "user", 
                    "content": (
                        "Read this page and provide me the details of the contract. Should have: \n\n"
                        "- Customer \n "
                        "- VDX Number and the status of the VDX \n "
                        "- Project Type: Ex: ITSM Solution Design, Service Now to JSM Migration (please mention multiple, if it applies) \n "
                        "- Hours \n " 
                        "- Year \n " 
                        "- Costs \n "
                        "- Term Length \n "
                        "- Client Resposabilities \n "
                        "- In Scope and Out of Scope \n"
                        "- Total FTE \n "
                        "- Scope Type: LOE (Level of Effort), Time and Materials, Fixed Scope or anything else \n "
                        "- Deliverables (list) \n\n "
                        "Just give me the data. Don't write anything else"
                    )
                },
                { 
                    "role": "assistant", 
                    "content": "Ok" 
                },
                { 
                    "role": "user", 
                    "content": text 
                }
            ],
            temperature=0,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return ""

def get_child_pages(parent_page_id):
    """
    Get child pages with pagination.
    """
    url = f"{BASE_URL}/rest/api/content/{parent_page_id}/child/page"
    child_pages = []
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }

    while url and len(child_pages) < MAX_PAGES:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        child_pages.extend(data["results"])
        url = data["_links"].get("next")
        if url and not url.startswith("http"):
            url = BASE_URL + url

    logging.info(f"Total child pages fetched: {len(child_pages)}")
    return child_pages[:MAX_PAGES]

def get_page_storage_format(page_id):
    """
    Get page storage format.
    """
    url = f"{BASE_URL}/rest/api/content/{page_id}?expand=body.storage"
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["body"]["storage"]["value"]

def extract_text_from_html(html_content):
    """
    Extract text from HTML content.
    """
    soup = BeautifulSoup(html_content, features="html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    return soup.get_text()

def save_to_file(title, content):
    """
    Save content to a file with the title as filename if it doesn't already exist.
    """
    safe_title = "".join([c if c.isalnum() else "_" for c in title])
    file_path = os.path.join(OUTPUT_FOLDER, f"{safe_title}.txt")
    
    if os.path.exists(file_path):
        logging.info(f"File {file_path} already exists. Skipping.")
        return False
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    logging.info(f"Saved content to {file_path}")
    return True

def main(parent_page_id):
    child_pages = get_child_pages(parent_page_id)
    for page in child_pages:
        page_id = page["id"]
        page_title = page["title"]
        
        # Check if file exists before sending request to OpenAI
        safe_title = "".join([c if c.isalnum() else "_" for c in page_title])
        file_path = os.path.join(OUTPUT_FOLDER, f"{safe_title}.txt")
        
        if os.path.exists(file_path):
            logging.info(f"File {file_path} already exists. Skipping OpenAI request.")
            continue
        
        storage_format = get_page_storage_format(page_id)
        plain_text = extract_text_from_html(storage_format)
        response = request_openai(plain_text)
        save_to_file(page_title, response)

# Run the script
if __name__ == "__main__":
    main(PARENT_PAGE_ID)
