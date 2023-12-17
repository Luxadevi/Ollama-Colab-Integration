# main.py

import streamlit as st
import importlib
from shared import modules_to_import
# Imported models are listed in shared.py
# Dynamically import each module and its functions
for module_name, function_list in modules_to_import.items():
    module = importlib.import_module(f"modules.{module_name}")
    for function_name in function_list:
        if hasattr(module, function_name):
            globals()[function_name] = getattr(module, function_name)
        else:
            print(f"Warning: {function_name} not found in {module_name}")




def main():
    
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Choose a Page", ["Model Selector", "Interactive Modelfile Creator", "Chat Interface", "Set Ollama API Url",
                                              "LiteLLM Proxy", "Public Endpoint", "Downloading Models",
                                              "High Precision Quantization", "Medium Precision Quantization",
                                              "Upload to HF", "Token-encrypt"])



    if page == "Model Selector":
        show_model_selector()
    elif page == "Interactive Modelfile Creator":
        model_name_key = "model_creator_name_input"  # Unique key for this instance
 
        display_model_creator()  # Ensure this function also uses unique keys for widgets

        
    elif page == "Chat Interface":
        show_chat_interface()    
    elif page == "Set Ollama API Url":
        show_ollama_api_configurator()
    elif page == "LiteLLM Proxy":
        show_litellm_proxy_page()
    elif page == "Public Endpoint":
        show_public_endpoint_page()
    elif page == "Downloading Models":
        show_downloading_models_page()
    elif page == "High Precision Quantization":
        show_high_precision_quantization_page()
    elif page == "Medium Precision Quantization":
        show_medium_precision_quantization_page()
    elif page == "Upload to HF": 
        show_model_management_page()
    elif page == "Token-encrypt":
        show_token_encrypt_page()        

    


    
if __name__ == "__main__":
    main()
    

