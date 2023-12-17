# chat_interface.py

import streamlit as st
import base64
import requests
import json
import time
from shared import shared


# Importing necessary functions from model_selector.py
from .model_selector import show_model_selector, get_json, show_model_details


base_url = shared['api_endpoint']['url']

# Encodes images to base64 output as list
def images_to_base64(images):
    """Convert a list of image files to base64 encoding."""
    encoded_images = []
    for image_file in images:
        if image_file is not None:
            # Read the file and encode it
            file_bytes = image_file.getvalue()
            base64_encoded = base64.b64encode(file_bytes).decode("utf-8")
            encoded_images.append(base64_encoded)
    return encoded_images



# Here we create the request for a chat completion at /api/generate
def stream_response(prompt, base_url, model_name, encoded_images=None):
    url = f'{base_url}/api/generate'
    payload = {
        "model": model_name,  # Using the selected model
        "prompt": prompt
    }
    if encoded_images:
        payload["images"] = encoded_images

    headers = {'Content-Type': 'application/json'}

    # Print statement to log the request details
    # Using separators to remove extra whitespaces in the list
    # Uncomment print statements below to show the request sent to Ollama
    # print(f"Requesting URL: {url}")
    # print(f"Headers: {headers}")
    # print(f"Payload: {json.dumps(payload, separators=(',', ':'), indent=4)}")

    with requests.post(url, json=payload, headers=headers, stream=True) as response:
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    yield json.loads(line)
        else:
            print(f"Error: {response.status_code}")
            yield {"response": "Error in generating response"}

def show_chat_interface():
    st.title("Chat Interface")

    # Sidebar dropdown for Chat Options
    with st.sidebar:
        chat_option = st.selectbox("Chat Options", ["Standard Chat", "Slow Typing Mode", "Fast Typing Mode"])
        # Fetch models for model selection
        if 'model_names' not in st.session_state:
            st.session_state['model_names'] = []
        fetch_button = st.button('Fetch Models')
        if fetch_button:
            json_data = get_json(f"{base_url}/api/tags")
            if isinstance(json_data, dict) and 'models' in json_data:
                st.session_state['model_names'] = [model['name'] for model in json_data['models']]
            else:
                st.error("Invalid JSON structure or error in fetching data")
        # Model selection dropdown
        selected_model = st.selectbox("Select a Model", st.session_state['model_names'])
        # Image Uploader
        uploaded_images = st.file_uploader("Upload Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        encoded_images = images_to_base64(uploaded_images)
        if encoded_images:
            for uploaded_image in uploaded_images:
                st.image(uploaded_image, caption="Uploaded Image")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Here's the modified section
        with st.chat_message("assistant"):  
            message_placeholder = st.empty()
            full_response = ""

            # Pass the list of encoded images to the stream_response function
            for response_chunk in stream_response(prompt, base_url, selected_model, encoded_images):
                if 'response' in response_chunk:
                    assistant_response = response_chunk['response']
                    typing_speed = 0.03 if chat_option == "Slow Typing Mode" else 0.008
                    for char in assistant_response:
                        full_response += char
                        time.sleep(typing_speed)
                        message_placeholder.markdown(full_response + "▌", unsafe_allow_html=True)

            message_placeholder.markdown(full_response, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": full_response})