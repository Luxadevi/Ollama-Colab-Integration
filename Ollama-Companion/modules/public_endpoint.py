import os
import threading
import time
import subprocess
import streamlit as st
from pathlib import Path

# Get the directory of the current module
module_dir = Path(__file__).parent

# Define the root directory (one level up from the current module directory)
root_dir = module_dir.parent

# Define the log directory and log file paths in the root directory
log_dir = root_dir / 'logs'
endpoint_log_path = log_dir / 'endpoint.log'

# Define the tools directory path in the root directory
tools_dir = root_dir / 'tools'

flask_thread = None

def flask_endpoint():
    # Set the path to your Flask endpoint script
    endpoint_path = tools_dir / 'endpoint.py'
    command = f"PYTHONUNBUFFERED=1 python3 {endpoint_path} > {endpoint_log_path} 2>&1"
    os.system(command)

def start_endpoint_and_get_last_2_lines():
    global flask_thread
    try:
        flask_thread = threading.Thread(target=flask_endpoint, daemon=True)
        flask_thread.start()

        time.sleep(15)

        cloudflare_url = None
        with open(endpoint_log_path, "r") as log_file:
            for line in log_file:
                if ".trycloudflare.com" in line:
                    cloudflare_url = line.split()[3]
                    break

        result = "Tunnel proxy setup successful\n\n"
        if cloudflare_url:
            ollama_endpoint = f"{cloudflare_url}"
            openai_endpoint = f"{cloudflare_url}/openai"
            result += f"Ollama endpoint is available at: [{ollama_endpoint}]({ollama_endpoint})\n\n"
            result += f"OpenAI API endpoint is available at: [{openai_endpoint}]({openai_endpoint})"

        return result
    except Exception as e:
        return f"Error: {str(e)}"

def kill_endpoint():
    try:
        # Find processes using port 5000 and kill them
        pids = subprocess.check_output(["lsof", "-t", "-i:5000"]).decode().splitlines()
        for pid in pids:
            subprocess.run(["kill", "-9", pid])

        return "Endpoint killed successfully."
    except Exception as e:
        return f"Error: {str(e)}"
    
def show_public_endpoint_page():
    st.title("Public Endpoint Management")

    if st.button("Start Endpoint"):
        result = start_endpoint_and_get_last_2_lines()
        
        # Check if result contains URLs and convert them to Markdown links
        if "Running on" in result:
            lines = result.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("* Running on"):
                    url = line.split()[3]
                    lines[i] = f"* Running on [link]({url})"
                elif line.startswith("* Traffic stats available on"):
                    url = line.split()[4]
                    lines[i] = f"* Traffic stats available on [link]({url})"
            result = '\n'.join(lines)
        
        # Display the result as Markdown
        st.markdown(result)

    if st.button("Kill Endpoint"):
        result = kill_endpoint()
        st.text(result)

    with st.expander("Public Endpoint Information"):
        st.markdown("""
        **Public Endpoint Management**

        This section is dedicated to managing and accessing the public endpoint for OpenAI and Ollama APIs.

        **Public Endpoint Controls**

        - **Start Public Endpoint:** Use this button to start the public endpoint. The endpoint will be accessible for interfacing with the OpenAI or Ollama API.
        - **Read Public Endpoint Log:** This section will display the last few lines of the log, providing insights into the endpoint's operation.
        - **Access Public Endpoint:** Once the endpoint is running, it will be accessible at specific URLs provided in the log output.
        - **Kill Public Endpoint:** If the endpoint is running and needs to be stopped, use this button to terminate it.

        Please be patient when starting or stopping the public endpoint as these actions may take some time to complete.
        """)
