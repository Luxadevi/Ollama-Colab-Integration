# api_module.py
import streamlit as st
import requests
from shared import shared
import json
api_url = shared['api_endpoint']['url']
def get_json(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return str(e)



def show_model_details(model_name, api_url):
    # Check if the model name includes ":latest" and remove it
    if model_name.endswith(":latest"):
        model_name = model_name[:-7]  # Remove the last 7 characters, which is ":latest"
    
    # Construct the URL
    url = f"{api_url}/api/show"
    
    # Create the JSON payload
    payload = {
        "name": model_name
    }

    # Send a POST request with the JSON payload
    response = requests.post(url, json=payload)
    
    # Check the response
    if response.status_code != 200:
        st.error(f"Failed to fetch model details. Status code: {response.status_code}, Response: {response.text}")
        return

    model_data = response.json()

    # Display the model parameters in Markdown tables
    st.subheader(f"Details for model: {model_name}")
    
    parameters = model_data.get("parameters", "")
    parameters = parameters.split("\n") if parameters else []

    markdown_tables = {"Parameters": "| Parameter | Value |\n| --- | --- |"}
    stop_values = []  # To collect "stop" values

    for param in parameters:
        if param.strip():
            name, value = param.strip().split(None, 1)
            if name == "stop":
                stop_values.append(value)
            else:
                markdown_tables["Parameters"] += f"\n| {name} | {value} |"



    # Display the model file content
    st.text_area("Model File", model_data.get("modelfile", "No modelfile data"), height=375)
    # Display the Markdown tables
    for table_name, table_content in markdown_tables.items():
        st.markdown(f"**{table_name}**")
        st.markdown(table_content)

    # Display "stop" values in individual tables
    for i, stop_value in enumerate(stop_values, 1):
        st.subheader(f"Stop Sequence Parameter {i}")
        st.text(stop_value)
    # Display the template
    st.text_area("Template", model_data.get("template", "No template data"), height=200)

    # Display the license information
    st.text_area("License", model_data.get("license", "No license data"), height=100)

    # Display the details in a more structured way
    st.subheader("Additional Details")
    details = model_data.get("details", {})
    for key, value in details.items():
        st.write(f"{key}: {value}")