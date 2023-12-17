import streamlit as st
from shared import shared  # Importing the shared dictionary
from pathlib import Path

def update_shared_file(new_url):
    try:
        shared_file = Path('shared.py')
        
        # Read the current contents of the file
        lines = shared_file.read_text().splitlines()

        # Find and modify the api_endpoint line
        for i, line in enumerate(lines):
            if line.strip().startswith("'api_endpoint':"):
                start = line.find('{')
                end = line.rfind('}') + 1
                dict_str = line[start:end]
                shared_dict = eval(dict_str)  # Using eval to convert string to dict
                shared_dict['url'] = new_url  # Modify the url
                new_line = f"    'api_endpoint': {shared_dict},\n"
                lines[i] = new_line
                break

        # Write the modified contents back to the file
        shared_file.write_text('\n'.join(lines))

        return "API Endpoint URL updated successfully!"
    except Exception as e:
        return f"Error: {e}"

def is_valid_url(url):
    return url.startswith("http://") or url.startswith("https://")

def show_ollama_api_configurator():
    st.title("Ollama API Configuration")

    # Instructions for setting the API URL
    st.info("Set the IP or URL where Ollama is running. For local instances, typically use `http://127.0.0.1:11434`.")

    # Display and allow editing of the API endpoint URL
    current_url = st.text_input("API Endpoint URL", value=shared['api_endpoint']['url'])

    if st.button("Update"):
        if is_valid_url(current_url):
            message = update_shared_file(current_url)
            st.success(message)
            st.write("Updated API Endpoint URL:", current_url)
        else:
            st.error("Invalid URL. Please ensure it starts with http:// or https://")

# Uncomment this line to run this script directly for testing
# show_ollama_api_configurator()
