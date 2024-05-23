import requests
from bs4 import BeautifulSoup
import json

# Existing list of URLs to scrape
urls = [
]

# Scrape the main library page to find additional model URLs
library_page_url = "https://ollama.com/library"
response = requests.get(library_page_url)
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    new_urls = []
    for h2 in soup.find_all("h2", class_="flex items-center mb-3 truncate text-lg font-medium underline-offset-2 group-hover:underline md:text-2xl"):
        link = h2.find_parent("a")
        if link and link.get("href"):
            new_url = f"https://ollama.com{link['href']}/tags"
            new_urls.append(new_url)

    # Check for any new URLs not in the current list
    new_urls_to_add = [url for url in new_urls if url not in urls]
    if new_urls_to_add:
        print(f"New URLs found and added to the list: {new_urls_to_add}")
        urls.extend(new_urls_to_add)
    else:
        print("No new URLs found.")
else:
    print(f"Failed to fetch the library page. Status code: {response.status_code}")

# Define a function to scrape the specified div elements
def scrape_div_elements(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            div_elements = soup.find_all("div", class_="break-all font-medium text-gray-900 group-hover:underline")
            values = [element.text.strip() for element in div_elements]
            return values
        else:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"An error occurred while scraping {url}: {str(e)}")
        return []

# Create a dictionary to store the scraped data
scraped_data = {}

# Loop through the list of URLs and scrape div elements
for url in urls:
    model_name = url.split("/")[-2]  # Extract model name from URL
    scraped_values = scrape_div_elements(url)
    scraped_data[model_name] = scraped_values

# Save the scraped data to a JSON file
with open("scraped_data.json", "w") as json_file:
    json.dump(scraped_data, json_file, indent=4)

print("Scraped data saved to 'scraped_data.json'.")
