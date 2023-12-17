# modelfile_templater.py
import streamlit as st
import requests
from shared import shared
def load_model_data():
    url = "https://raw.githubusercontent.com/Luxadevi/Ollama-Colab-Integration/main/models.json"
    response = requests.get(url)
    return response.json()

def show_model_dropdowns():
    json_data = load_model_data()
    if not json_data:
        st.error("Failed to load model data.")
        return None, None

    model_providers = list(json_data.keys())
    selected_provider = st.selectbox("Select Model Provider", model_providers, key="model_provider")
    models = json_data.get(selected_provider, [])
    selected_model = st.selectbox("Select Model", models, key="model_selection")
    return selected_provider, selected_model

def show_parameter_sliders():
    params = {}
    for param, (default, range_) in shared['parameters'].items():
        key = f"param_{param}"
        if param == 'mirostat':
            params[param] = st.selectbox(param, range_, key=key)  # Use the options from shared['parameters']
        else:
            params[param] = st.slider(param, min_value=range_[0], max_value=range_[1], value=default, key=key)
    return params

def show_model_name_input(key):
    return st.text_input("Model Name", key=key)

def display_model_creator():
    st.title("Model File Creator")
    selected_provider, selected_model = show_model_dropdowns()
    model_name = show_model_name_input("model_name_creator")
    additional_modelfile_content = st.text_area("Additional Modelfile Content", key="modelfile_content_creator")
    option_system_prompt = st.text_area("Optional System Prompt", key="option_system_prompt_creator")

    stop_sequences = manage_stop_sequences()
    parameters = show_parameter_sliders()
    print_payload_details = st.checkbox("Print Payload Details on Webpage")
    submit_button = st.button("Build and Deploy Model")

    if submit_button and model_name:
        modelfile_content = construct_modelfile_content(selected_provider, selected_model, additional_modelfile_content, option_system_prompt, stop_sequences, parameters)
        result = create_model(model_name, modelfile_content, print_payload_details)
        st.write(result)

def manage_stop_sequences():
    stop_sequences = []
    for i in range(10):  # Allows up to 10 stop sequences
        seq = st.text_input(f"Stop Sequence {i+1}", key=f"stop_sequence_{i}")
        if seq:
            stop_sequences.append(seq)
        else:
            break  # Stop adding more inputs once an empty one is found
    return stop_sequences

def construct_modelfile_content(provider, model, additional_content, system_prompt, stop_seqs, params):
    modelfile_content = f"FROM {provider}:{model}\n{additional_content}"
    for seq in stop_seqs:
        modelfile_content += f"\nPARAMETER stop {seq}"
    if system_prompt:
        modelfile_content += f"\nSYSTEM {system_prompt}"
    for param, value in params.items():
        default_value = shared['parameters'][param][0]
        if value != default_value:
            modelfile_content += f"\nPARAMETER {param} {value}"
    return modelfile_content
def create_model(name, modelfile_content, print_payload):
    try:
        data = {"name": name, "modelfile": modelfile_content}
        if print_payload:
            st.write("Request Data:", data)

        output_content = ""
        text_area_placeholder = st.empty()
        with requests.post(f"{shared['api_endpoint']['url']}/api/create", json=data, stream=True) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        output_content += decoded_line + "\n"
                        text_area_placeholder.text_area("Model Build Output", output_content, height=300)
                return "Model created successfully."
            else:
                return f"Request failed: {response.text}"
    except Exception as e:
        return f"Error creating model: {str(e)}"
