import streamlit as st
import requests  # Import the requests library
from shared import shared
from .api_module import get_json, show_model_details  # Importing show_model_details

api_url = shared['api_endpoint']['url']

def show_model_selector():
    st.title('Ollama Model Manager')
    st.text("Start by downloading your list of available models")
    
    if 'model_names' not in st.session_state:
        st.session_state['model_names'] = []

    fetch_button = st.button('Fetch Models')
    if fetch_button:
        json_data = get_json(f"{api_url}/api/tags")
        if isinstance(json_data, dict) and 'models' in json_data:
            st.session_state['model_names'] = [model['name'] for model in json_data['models']]
        else:
            st.error("Invalid JSON structure or error in fetching data")

    if st.session_state['model_names']:
        st.text("Show detailed model overview, or delete the selected model")
        selected_model = st.selectbox("Select a Model", st.session_state['model_names'])
        
        if st.button('Show Model Details'):
            show_model_details(selected_model, api_url)  # Ensure selected_model is correctly used

        if st.button('Delete Model'):
            if delete_model(selected_model, api_url):
                st.success(f"Model '{selected_model}' has been deleted.")
                # Update the model list
                st.session_state['model_names'].remove(selected_model)
            else:
                st.error("Failed to delete the model.")

def delete_model(model_name, api_url):
    try:
        # Define the URL for deleting a model
        delete_url = f"{api_url}/api/delete"

        # Create a JSON payload with the model name
        payload = {'name': model_name}

        # Send a DELETE request to delete the model
        response = requests.delete(delete_url, json=payload)

        # Check the response status code
        if response.status_code == 200:
            return True
        else:
            st.error(f"Error deleting model: {response.status_code}")
            return False

    except Exception as e:
        st.error(f"Error deleting model: {str(e)}")
        return False