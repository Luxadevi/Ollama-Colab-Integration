import requests
from bs4 import BeautifulSoup
import json

# Existing list of URLs to scrape
urls = []

# Function to download and load the existing JSON data
def download_json(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to download existing JSON data. Status code: {response.status_code}")
        return {}

# URL of the existing JSON file
existing_json_url = "https://raw.githubusercontent.com/Luxadevi/Ollama-Colab-Integration/main/models.json"
existing_data = download_json(existing_json_url)

# Scrape the main library page to find additional model URLs
library_page_url = "https://ollama.com/library"
print("Fetching library page...")
response = requests.get(library_page_url)
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    new_urls = []
    print("Searching for new URLs in the library page...")
    for h2 in soup.find_all("h2", class_="truncate text-lg font-medium underline-offset-2 group-hover:underline md:text-2xl"):
        link = h2.find_parent("a")
        if link and link.get("href"):
            new_url = f"https://ollama.com{link['href']}/tags"
            new_urls.append(new_url)
            print(f"Found new URL: {new_url}")

    new_urls_to_add = [url for url in new_urls if url not in urls]
    if new_urls_to_add:
        print(f"New URLs found and added to the list: {new_urls_to_add}")
        urls.extend(new_urls_to_add)
    else:
        print("No new URLs found.")
else:
    print(f"Failed to fetch the library page. Status code: {response.status_code}")

# Function to scrape div elements
def scrape_div_elements(url):
    print(f"Scraping data from {url}...")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            div_elements = soup.find_all("div", class_="break-all font-medium text-gray-900 group-hover:underline")
            values = [element.text.strip() for element in div_elements]
            print(f"Data scraped successfully from {url}.")
            return values
        else:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"An error occurred while scraping {url}: {str(e)}")
        return []

# Scraping data
scraped_data = {}
for url in urls:
    model_name = url.split("/")[-2]
    print(f"Processing model: {model_name}")
    scraped_values = scrape_div_elements(url)
    scraped_data[model_name] = scraped_values

# Compare the existing data with the scraped data
new_items = {}
for key, value in scraped_data.items():
    if key not in existing_data or existing_data[key] != value:
        new_items[key] = value

if new_items:
    print("Changes or new items found:")
    print(json.dumps(new_items, indent=4))
else:
    print("No changes or new items found.")

# Save the scraped data to a JSON file
with open("scraped_data.json", "w") as json_file:
    json.dump(scraped_data, json_file, indent=4)

print("Scraped data saved to 'scraped_data.json'.")
