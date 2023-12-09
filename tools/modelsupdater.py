import requests
from bs4 import BeautifulSoup
import json

# List of URLs to scrape
urls = [
    "https://ollama.ai/library/mistral/tags",
    "https://ollama.ai/library/llama2/tags",
    "https://ollama.ai/library/codellama/tags",
    "https://ollama.ai/library/llama2-uncensored/tags",
    "https://ollama.ai/library/orca-mini/tags",
    "https://ollama.ai/library/vicuna/tags",
    "https://ollama.ai/library/wizard-vicuna-uncensored/tags",
    "https://ollama.ai/library/phind-codellama/tags",
    "https://ollama.ai/library/wizardcoder/tags",
    "https://ollama.ai/library/mistral-openorca/tags",
    "https://ollama.ai/library/nous-hermes/tags",
    "https://ollama.ai/library/zephyr/tags",
    "https://ollama.ai/library/wizard-math/tags",
    "https://ollama.ai/library/llama2-chinese/tags",
    "https://ollama.ai/library/stable-beluga/tags",
    "https://ollama.ai/library/falcon/tags",
    "https://ollama.ai/library/codeup/tags",
    "https://ollama.ai/library/everythinglm/tags",
    "https://ollama.ai/library/medllama2/tags",
    "https://ollama.ai/library/wizardlm-uncensored/tags",
    "https://ollama.ai/library/wizard-vicuna/tags",
    "https://ollama.ai/library/deepseek-coder/tags",
    "https://ollama.ai/library/open-orca-platypus2/tags",
    "https://ollama.ai/library/starcoder/tags",
    "https://ollama.ai/library/orca2/tags",
    "https://ollama.ai/library/dolphin2.2-mistral/tags",
    "https://ollama.ai/library/yarn-mistral/tags",
    "https://ollama.ai/library/openchat/tags",
    "https://ollama.ai/library/openhermes2.5-mistral/tags",
    "https://ollama.ai/library/samantha-mistral/tags",
    "https://ollama.ai/library/yi/tags",
    "https://ollama.ai/library/yarn-llama2/tags",
    "https://ollama.ai/library/sqlcoder/tags",
    "https://ollama.ai/library/openhermes2-mistral/tags",
    "https://ollama.ai/library/wizardlm/tags",
    "https://ollama.ai/library/neural-chat/tags",
    "https://ollama.ai/library/dolphin2.1-mistral/tags",
    "https://ollama.ai/library/mistrallite/tags",
    "https://ollama.ai/library/codebooga/tags",
    "https://ollama.ai/library/goliath/tags",
    "https://ollama.ai/library/nexusraven/tags",
    "https://ollama.ai/library/xwinlm/tags",
    "https://ollama.ai/library/alfred/tags",
    "https://ollama.ai/library/starling-lm/tags",
    "https://ollama.ai/library/magicoder/tags",
    "https://ollama.ai/library/stablelm-zephyr/tags"
]

# Define a function to scrape the specified div elements
def scrape_div_elements(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            div_elements = soup.find_all("div", class_="break-all text-lg text-gray-900 group-hover:underline")
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
