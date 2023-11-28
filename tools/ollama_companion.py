import gradio as gr
import json
import subprocess
import requests
import re
import os
import threading
import yaml
import subprocess
import threading
import logging.handlers
import httpx
import sys
import os
import time
from flask import Flask, request, Response
import requests
from flask_cloudflared import run_with_cloudflared
import gradio as gr
from threading import Thread
import sys
import logging.handlers


script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
config_path = os.path.join(script_dir, './config.yaml')
litellm_proxycmd = "PYTHONUNBUFFERED=1 litellm --config ./config.yaml >> litellmlog 2>&1 &"


polling_active = False
endpointcmd = "PYTHONUNBUFFERED=1 python3 ./endpoint.py >> endpoint.log 2>&1 &"
kill_endpointcmd = "pkill -f './endpoint.py'"


# Global variables for dropdown options
option_1_global = None
option_2_global = None
cloudflare_url = None
# Fetching models data from the URL
url = "https://raw.githubusercontent.com/Luxadevi/Ollama-Colab-Integration/main/models.json"
response = requests.get(url)
json_data = response.json()

# Structuring the data
options_1 = list(json_data.keys())  # ['mistral', 'llama2', 'codellama', ...]
options_2 = json_data  # The entire JSON data

# Parameters with their default values and ranges
parameters = {
    'mirostat': [0, [0, 1, 2]],  # Dropdown
    'mirostat_eta': [0.1, (0.0, 1.0)],
    'mirostat_tau': [0.1, (0.0, 1.0)],
    'num_ctx': [4096, (1024, 8192)],
    'num_gqa': [256, (128, 512)],
    'num_gpu': [1, (1, 250)],
    'num_thread': [1, (1, 30)],
    'repeat_last_n': [0, (0, 32000)],
    'repeat_penalty': [1.0, (0.5, 2.0)],
    'temperature': [0.8, (0.1, 1.0)],
    'seed': [None, (0, 10000)],  # None indicates no default value
    'tfs_z': [1, (1, 20)],  # Slider from 1 to 20
    'num_predict': [256, (128, 512)],
    'top_k': [0, (0, 100)],
    'top_p': [1.0, (0.1, 1.0)]
}
def initialize_log_files():
    log_files = ["litellmlog", "endpoint.log", "endpoint_openai.log"]
    for log_file in log_files:
        log_file_path = os.path.join(script_dir, log_file)
        if not os.path.exists(log_file_path):
            open(log_file_path, 'w').close()
            print(f"Created log file: {log_file}")
        else:
            print(f"Log file already exists: {log_file}")

def kill_litellm_proxy():
    try:
        # Command to kill the LiteLLM proxy process
        kill_command = "pkill -f 'litellm --config'"

        # Execute the kill command
        os.system(kill_command)

        return "LiteLLM proxy process terminated."
    except Exception as e:
        return f"Error: {str(e)}"
def start_litellm_proxy_and_read_log():
    try:
        # Start the LiteLLM proxy using subprocess
        subprocess.Popen([litellm_proxycmd], shell=True)



        # Wait for some time for the proxy to start and log
        time.sleep(15)

        # Read the log file and search for specific lines
        log_file_path = "./litellmlog"
        with open(log_file_path, "r") as log_file:
            lines = log_file.readlines()

        # Find and return the relevant lines
        for i, line in enumerate(lines):
            if "LiteLLM: Proxy initialized with Config, Set models:" in line:
                # Assuming the model names are listed in the following lines
                model_lines = [lines[i + j].strip() for j in range(1, len(lines) - i) if lines[i + j].strip()]
                return "\n".join([line.strip()] + model_lines)

        return "Relevant log information not found."
    except Exception as e:
        return f"Error: {str(e)}"

def poll_api():
    global polling_active
    while polling_active:
        response = requests.get("http://127.0.0.1:11434/api/tags")
        if response.status_code == 200:
            json_data = response.json()
            model_names = [model['name'] for model in json_data.get('models', [])]
            update_config_file(model_names)
        time.sleep(15)

def start_polling():
    global polling_active
    polling_active = True
    threading.Thread(target=poll_api).start()
    return "Polling started"

def stop_polling():
    global polling_active
    polling_active = False
    return "Polling stopped"
def is_litellm_running():
    """Check if LiteLLM is currently running."""
    try:
        # Using subprocess to check if litellm process is running
        result = subprocess.run(["pgrep", "-f", "litellm --config"], capture_output=True, text=True)
        return result.stdout != ""
    except Exception as e:
        print(f"Error checking if LiteLLM is running: {e}")
        return False

def restart_litellm():
    """Restart the LiteLLM process."""
    try:
        # Kill the current LiteLLM process
        kill_litellm_proxy()
        # Wait for a moment to ensure the process has been killed
        time.sleep(5)
        # Start the LiteLLM process again
        start_litellm_proxy_and_read_log()
        print("LiteLLM proxy restarted successfully.")
    except Exception as e:
        print(f"Error restarting LiteLLM: {e}")

def update_config_file(model_names):
    global current_model_list
    config_file_path = "./config.yaml"

    # Read the existing content of the config file
    with open(config_file_path, "r") as file:
        try:
            config = yaml.safe_load(file) or {}
        except yaml.YAMLError as e:
            print(f"Error reading config file: {e}")
            return

    # Ensure 'model_list' key exists in the configuration
    if 'model_list' not in config:
        config['model_list'] = []

    existing_models = {model['model_name'] for model in config['model_list']}

    # Flag to check if the config file needs updating
    needs_update = False

    # Update the 'model_list' with new models
    for model_name in model_names:
        full_model_name = f"ollama/{model_name}"
        if full_model_name not in existing_models:
            entry = {
                'model_name': full_model_name,
                'litellm_params': {
                    'model': full_model_name,
                    'api_base': "http://127.0.0.1:11434",
                    'json': True
                }
            }
            config['model_list'].append(entry)
            existing_models.add(full_model_name)  # Add to existing models set
            needs_update = True

    # Write the updated content back to the YAML file and restart LiteLLM if necessary
    if needs_update:
        with open(config_file_path, "w") as file:
            yaml.dump(config, file, default_flow_style=False, sort_keys=False)
        # Check if LiteLLM is running and restart it
        if is_litellm_running():
            restart_litellm()

def start_openai_proxy():
    try:
        # Specify the command to start the OpenAI proxy endpoint
        openai_endpointcmd = "PYTHONUNBUFFERED=1 python3 ./endpointopenai.py >> endpoint_openai.log 2>&1 &"

        # Start the OpenAI proxy endpoint
        subprocess.Popen(openai_endpointcmd, shell=True)

        # Wait for 15 seconds (adjust as needed)
        time.sleep(15)

        # Read the last 2 lines from the endpoint_openai.log file
        log_file_path = "./endpoint_openai.log"
        with open(log_file_path, "r") as log_file:
            lines = log_file.readlines()
            last_2_lines = "".join(lines[-2:])  # Concatenate the last 2 lines

        return last_2_lines
    except Exception as e:
        return f"Error: {str(e)}"
def start_endpoint_and_get_last_2_lines():
    try:
        # Start the Flask endpoint (use subprocess.Popen as before)
        subprocess.Popen(endpointcmd, shell=True)

        # Wait for 15 seconds (adjust as needed)
        time.sleep(15)

        # Read the last 2 lines from the endpoint.log file
        log_file_path = "./endpoint.log"
        with open(log_file_path, "r") as log_file:
            lines = log_file.readlines()
            last_2_lines = "".join(lines[-2:])  # Concatenate the last 2 lines

        return last_2_lines
    except Exception as e:
        return f"Error: {str(e)}"
def kill_endpoint():
    try:
        # Specify the commands to kill both processes
        kill_endpointcmd = "pkill -f './endpoint.py'"
        kill_openai_endpointcmd = "pkill -f './endpointopenai.py'"

        # Execute the kill commands for both processes
        os.system(kill_endpointcmd)
        os.system(kill_openai_endpointcmd)

        return "Endpoints killed successfully."
    except Exception as e:
        return f"Error: {str(e)}"



def build_curl_command(model_name, modelfile_content, stop_sequence, *args):
    try:
        # Check if 'FROM' is present in the modelfile_content
        if 'FROM' not in modelfile_content:
            modelfile_content = f"FROM {option_1_global}:{option_2_global}" + modelfile_content

        for param, value in zip(parameters.keys(), args):
            default = parameters[param][0]
            if value != default:
                if param == 'mirostat':
                    modelfile_content += f"\nPARAMETER {['disabled', 'Mirostat 1', 'Mirostat 2.0'][value]}"
                else:
                    modelfile_content += f"\nPARAMETER {param} {value}"

        if stop_sequence:  # Add stop sequence if provided
            modelfile_content += f"\nPARAMETER stop {stop_sequence}"

        data = {
            "name": model_name,
            "modelfile": modelfile_content
        }
        curl_command = f"curl http://localhost:11434/api/create -d '{json.dumps(data)}'"
        process = subprocess.run(curl_command, shell=True, capture_output=True, text=True)
        return curl_command, process.stdout or process.stderr
    except Exception as e:
        return "", f"Error: {str(e)}"
def create_model_manually(model_name, modelfile_content, stream_response):
    try:
        data = {
            "name": model_name,
            "modelfile": modelfile_content,
            "stream": stream_response
        }
        response = requests.post("http://localhost:11434/api/create", json=data)
        return response.json()
    except Exception as e:
        return {"curl_command": "", "execution_output": f"Error: {str(e)}"}
def show_model_details(model_name):
    data = {"name": model_name}
    curl_command = f"curl http://localhost:11434/api/show -d '{json.dumps(data)}'"
    process = subprocess.run(curl_command, shell=True, capture_output=True, text=True)
    output = process.stdout or process.stderr

    try:
        # Parse the JSON data
        json_data = json.loads(output)

        # Extracting the specific keys
        license_info = json_data.get('license', 'Not available')
        modelfile_info = json_data.get('modelfile', 'Not available')
        parameters_info = json.dumps(json_data.get('parameters', {}), indent=4)
        template_info = json_data.get('template', 'Not available')

        return license_info, modelfile_info, parameters_info, template_info
    except json.JSONDecodeError:
        # Return a tuple with error message if it's not valid JSON
        return (output, "", "", "")
def list_models():
    url = "http://127.0.0.1:11434/api/tags"
    response = requests.get(url)
    models = response.json().get('models', [])
    return "\n".join([model['name'] for model in models])
def create_model_manually(model_name, modelfile_content, stream_response):
    try:
        data = {
            "name": model_name,
            "modelfile": modelfile_content,
            "stream": stream_response
        }
        response = requests.post("http://localhost:11434/api/create", json=data)
        return response.json()
    except Exception as e:
        return {"curl_command": "", "execution_output": f"Error: {str(e)}"}

def main():
    initialize_log_files()
    with gr.Blocks(theme='ParityError/LimeFace') as app:


        gr.Markdown("Ollama Companion")

        with gr.Tab("ModelFile Templater"):
            with gr.Row():
                model_name = gr.Textbox(label="Model Name", placeholder="Enter model name")
                modelfile_content_input = gr.Textbox(lines=10, label="Modelfile Content", placeholder="Enter modelfile content")
                stop_sequence = gr.Textbox(label="Stop Sequence", placeholder="Enter stop sequence")
                d1 = gr.Dropdown(choices=options_1, label="Model-Provider")
                d2 = gr.Dropdown([])

                def update_second(first_val):
                    d2 = gr.Dropdown(options_2[first_val])
                    return d2

                d1.input(update_second, d1, d2)

                outputs = gr.Textbox()

                def print_results(option_1, option_2):
                    global option_1_global, option_2_global  # Declare them as global
                    option_1_global = option_1  # Update global variable
                    option_2_global = option_2  # Update global variable
                    return f"You selected '{option_1}:{option_2}' in the second dropdown."

                d2.input(print_results, [d1, d2], outputs)

            parameter_inputs = []
            for param, (default, range_) in parameters.items():
                if isinstance(range_, list):  # Dropdown parameter
                    parameter_inputs.append(gr.Dropdown(label=param, choices=range_, value=default))
                elif range_ is None:  # Boolean parameter
                    parameter_inputs.append(gr.Checkbox(label=param, value=default))
                elif isinstance(range_, tuple):  # Numeric parameter with a range
                    parameter_inputs.append(
                        gr.Slider(label=param, minimum=range_[0], maximum=range_[1], value=default))

            submit_button = gr.Button("Build and deploy Model")
            curl_command_output = gr.Textbox(label="API Call")
            execution_output = gr.Textbox(label="Execution Output", interactive=False)

            submit_button.click(
                build_curl_command,
                inputs=[model_name, modelfile_content_input, stop_sequence] + parameter_inputs,
                outputs=[curl_command_output, execution_output]
            )
        with gr.Tab("Model Info"):
            with gr.Row():
                model_name_input = gr.Textbox(label="Model Name", placeholder="Enter model name for details")
                model_info_button = gr.Button("Get Model Info")
                model_list_button = gr.Button("List All Models")

            license_output = gr.Textbox(label="License", interactive=False)
            modelfile_output = gr.Textbox(label="Modelfile", interactive=False)
            parameters_output = gr.Textbox(label="Parameters", interactive=False)
            template_output = gr.Textbox(label="Template", interactive=False)
            model_list_output = gr.Textbox(label="List of Models", interactive=False)

            model_info_button.click(
                fn=show_model_details,
                inputs=[model_name_input],
                outputs=[license_output, modelfile_output, parameters_output, template_output]
            )

            model_list_button.click(fn=list_models, inputs=[], outputs=[model_list_output])
        with gr.Tab("Public Endpoint"):
            # Button to start the original endpoint
            start_endpoint_button = gr.Button("Start Public Endpoint")

            # Text box to display the last 2 lines
            last_2_lines_output = gr.Textbox(label="Last 2 Lines", interactive=False)

            # Set the action for the button click
            start_endpoint_button.click(start_endpoint_and_get_last_2_lines, inputs=[], outputs=[last_2_lines_output])

            # Button to start the OpenAI proxy endpoint
            start_openai_button = gr.Button("Start Public OpenAI Endpoint")

            # Text box to display the last 2 lines for the OpenAI proxy endpoint
            openai_last_2_lines_output = gr.Textbox(label="OpenAI Last 2 Lines", interactive=False)

            # Set the action for the button click
            start_openai_button.click(start_openai_proxy, inputs=[], outputs=[openai_last_2_lines_output])

            # Button to kill the endpoint
            kill_endpoint_button = gr.Button("Kill Both Endpoints")

            # Set the action for the button click
            kill_endpoint_button.click(kill_endpoint, inputs=[], outputs=[last_2_lines_output])
        with gr.Tab("LiteLLM-Proxy"):
            # Textboxes for displaying logs and status
            litellm_log_output = gr.Textbox(label="LiteLLM Log Output", interactive=False, lines=10)
            litellm_kill_status = gr.Textbox(label="LiteLLM Kill Status", interactive=False, lines=10)
            polling_status = gr.Textbox(label="Polling Status", interactive=False, lines=10)

            # Buttons for starting, stopping, and killing the proxy
            with gr.Row():
                start_litellm_button = gr.Button("Start LiteLLM Proxy")
                kill_litellm_button = gr.Button("Kill LiteLLM Proxy")
                start_polling_button = gr.Button("Start Polling")
                stop_polling_button = gr.Button("Stop Polling")

            # Link the buttons to their respective functions
            start_litellm_button.click(
                fn=start_litellm_proxy_and_read_log,
                inputs=[],
                outputs=[litellm_log_output]
            )

            kill_litellm_button.click(
                fn=kill_litellm_proxy,
                inputs=[],
                outputs=[litellm_kill_status]
            )

            start_polling_button.click(
                fn=start_polling,
                inputs=[],
                outputs=[polling_status]
            )

            stop_polling_button.click(
                fn=stop_polling,
                inputs=[],
                outputs=[polling_status]
            )




    app.launch(share=True)

if __name__ == "__main__":
    main()