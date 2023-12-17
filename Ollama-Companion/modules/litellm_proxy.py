import subprocess
import threading
import streamlit as st
import requests
import yaml
from shared import shared  # Importing the shared dictionary
from apscheduler.schedulers.background import BackgroundScheduler
import socket
import time
from pathlib import Path
scheduler = None  # Define it globally if it's used outside show_litellm_proxy_page

def initialize_directories():
    current_dir = Path(__file__).parent
    root_dir = current_dir.parent  # Set the root directory one level up
    log_dir = root_dir / 'logs'
    config_dir = root_dir / 'configs'
    return log_dir, config_dir

def is_process_running(process_name):
    try:
        process = subprocess.run(["pgrep", "-f", process_name], capture_output=True, text=True)
        return process.stdout != ""
    except subprocess.CalledProcessError:
        return False

def kill_process(process_name):
    try:
        subprocess.run(["pkill", "-f", process_name])
    except Exception as e:
        print(f"Error killing process {process_name}: {e}")

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    try:
        subprocess.run(["fuser", "-k", f"{port}/tcp"])
    except Exception as e:
        print(f"Error killing process on port {port}: {e}")

def start_litellm_proxy(log_file_path, config_file_path, append_to_log=False):
    def run_process():
        with open(log_file_path, "a" if append_to_log else "w") as log_file:
            process = subprocess.Popen(
                ["litellm", "--config", str(config_file_path), "--debug", "--add_function_to_prompt"],
                stdout=log_file,
                stderr=subprocess.STDOUT
            )
            process.communicate()

    litellm_thread = threading.Thread(target=run_process, daemon=True)
    litellm_thread.start()

def restart_litellm_proxy(log_file_path, config_file_path):
    # Start the proxy for the first time (creates new log file)
    start_litellm_proxy(log_file_path, config_file_path, append_to_log=False)
    # Wait for 4 seconds
    time.sleep(4)
    # Kill all LiteLLM instances
    kill_process("litellm")
    # Wait for 2 more seconds
    time.sleep(2)
    # Restart the proxy (appends to the existing log file)
    start_litellm_proxy(log_file_path, config_file_path, append_to_log=True)


def test_litellm_proxy():
    try:
        result = subprocess.run(
            ["curl", "--location", "http://127.0.0.1:8000/chat/completions",
             "--header", "Content-Type: application/json",
             "--data", '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "what llm are you"}]}'],
            capture_output=True, text=True
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Error executing curl command: {str(e)}"


def read_litellm_log(log_file_path):
    try:
        # Run the test_litellm_proxy function
        test_response = test_litellm_proxy()
        # print("Test LiteLLM Proxy Response:", test_response)

        time.sleep(2)
        with open(log_file_path, "r") as log_file:
            lines = log_file.readlines()

        for line in lines:
            if "LiteLLM: Proxy initialized with Config, Set models:" in line:
                model_lines = [line.strip() for line in lines[lines.index(line) + 1:] if line.strip()]
                return "\n".join([line.strip()] + model_lines)

        return "Relevant log information not found."
    except Exception as e:
        return f"Error: {str(e)}"

def poll_api(config_file_path, log_file_path):
    api_url = shared['api_endpoint']['url']
    response = requests.get(f"{api_url}/api/tags")
    if response.status_code == 200:
        json_data = response.json()
        model_names = [model['name'] for model in json_data.get('models', [])]
        if update_config_file(model_names, config_file_path):
            # Config file updated, restart LiteLLM Proxy
            restart_litellm_proxy(log_file_path, config_file_path)


def start_polling(config_file_path, log_file_path):
    if 'scheduler' not in st.session_state or st.session_state.scheduler is None:
        st.session_state.scheduler = BackgroundScheduler()
        st.session_state.scheduler.add_job(lambda: poll_api(config_file_path, log_file_path), 'interval', seconds=15)
        st.session_state.scheduler.start()
        st.success("Polling started")
    else:
        st.error("Polling is already running.")

def stop_polling():
    if 'scheduler' in st.session_state and st.session_state.scheduler:
        st.session_state.scheduler.shutdown()
        st.session_state.scheduler = None
        st.success("Polling stopped")
    else:
        st.error("Polling not started or already stopped")


        
def update_config_file(model_names, config_file_path):
    if not config_file_path.exists():
        print(f"Config file not found at {config_file_path}")
        return False

    with open(config_file_path, "r") as file:
        try:
            config = yaml.safe_load(file) or {}
        except yaml.YAMLError as e:
            print(f"Error reading config file: {e}")
            return False

    if 'model_list' not in config:
        config['model_list'] = []

    updated_models = set(f"ollama/{name}" for name in model_names)
    existing_models = set(model['model_name'] for model in config['model_list'])
    needs_update = False

    # Add new models
    for model_name in updated_models:
        if model_name not in existing_models:
            entry = {
                'model_name': model_name,
                'litellm_params': {
                    'model': model_name,
                    'api_base': shared['api_endpoint']['url'],
                    'json': True,
                    'drop_params': True
                }
            }
            config['model_list'].append(entry)
            print(f"Added new model: {model_name}")
            needs_update = True

    # Remove models that are no longer present
    original_model_count = len(config['model_list'])
    config['model_list'] = [model for model in config['model_list'] if model['model_name'] in updated_models]
    if len(config['model_list']) < original_model_count:
        removed_models = existing_models - updated_models
        print(f"Removed models from config file: {', '.join(removed_models)}")

    if needs_update or len(config['model_list']) < original_model_count:
        with open(config_file_path, "w") as file:
            yaml.dump(config, file, default_flow_style=False)
        print("Config file updated successfully.")
        return needs_update


### Interface creator

def show_litellm_proxy_page():
    global scheduler
    log_dir, config_dir = initialize_directories()
    log_file_path = log_dir / 'litellmlog'
    config_file_path = config_dir / 'config.yaml'

    st.title('OPENAI API Proxy')
    st.text("Start Litellm With the button below to convert Ollama traffic to Openai Traffic")
    # Define the scheduler variable outside the if statement
    scheduler = None

    # Button to start and restart the LiteLLM Proxy
    if st.button('Start LiteLLM'):
        threading.Thread(target=lambda: restart_litellm_proxy(log_file_path, config_file_path), daemon=True).start()
        st.success("LiteLLM Proxy start and restart sequence initiated")

    if st.button('Read LiteLLM Log'):
        log_output = read_litellm_log(log_file_path)
        st.text_area("Log Output", log_output, height=500)


    if st.write("Start creating new config files for LiteLLM. Whenever there is a new model detected, it will be added to the Config.yaml, and the proxy will be restarted."):
        pass
    if st.button('Start Polling'):
        start_polling(config_file_path, log_file_path)

    if st.button('Stop Polling'):
        stop_polling()

    if st.button('Kill Existing LiteLLM Processes'):
            litellm_process_name = "litellm"
            if is_process_running(litellm_process_name):
                kill_process(litellm_process_name)
                st.success(f"Killed existing {litellm_process_name} processes")
            else:
                st.info("No LiteLLM processes found")

    # Button to free up port 8000 if it's in use
    if st.button('Free Up Port 8000'):
        litellm_port = 8000
        if is_port_in_use(litellm_port):
            kill_process_on_port(litellm_port)
            st.success(f"Freed up port {litellm_port}")
        else:
            st.info(f"Port {litellm_port} is not in use")
    if st.button('Test LiteLLM Proxy'):
        test_response = test_litellm_proxy()
        st.text_area("Test LiteLLM Proxy Response", test_response, height=150)

    with st.expander("LiteLLM Proxy Management"):
        st.markdown("""
        **LiteLLM Proxy Management**

        This section allows you to manage and interact with the LiteLLM Proxy, which is used to convert OpenAI GPT models to the OpenAI API standard.

        **LiteLLM Proxy Controls**

        - **Start LiteLLM Proxy:** Click this button to start the LiteLLM Proxy. The proxy will run in the background and facilitate the conversion process.
        - **Read LiteLLM Log:** Use this button to read the LiteLLM Proxy log, which contains relevant information about its operation.
        - **Start Polling:** Click to initiate polling. Polling checks for updates to the ollama API and adds any new models to the configuration.
        - **Stop Polling:** Use this button to stop polling for updates.
        - **Kill Existing LiteLLM Processes:** If there are existing LiteLLM processes running, this button will terminate them.
        - **Free Up Port 8000:** Click this button to free up port 8000 if it's currently in use.

        Please note that starting the LiteLLM Proxy and performing other actions may take some time, so be patient and wait for the respective success messages.

        **LiteLLM Proxy Log**

        The "Log Output" section will display relevant information from the LiteLLM Proxy log, providing insights into its operation and status.
        """)