import os
import subprocess
import streamlit as st
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from pathlib import Path
from threading import Lock

# Initialize APScheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Global variables
scheduled_jobs = []
downloaded_files = []
download_queue = []
queue_lock = Lock()

def download_file_task():
    global download_queue, downloaded_files
    if download_queue:
        file_url, download_path, filename = download_queue.pop(0)
        file_path = download_path / filename
        command = [
            "aria2c", file_url,
            "--max-connection-per-server=16", "--split=8", "--min-split-size=1M", "--allow-overwrite=true",
            "-d", str(download_path), "-o", filename,
            "--continue=true"
        ]
        try:
            subprocess.run(command, check=True)
            downloaded_files.append(str(file_path))
        except subprocess.CalledProcessError as e:
            print(f"Error downloading {filename}: {str(e)}")

        # Schedule next download
        if download_queue:
            scheduler.add_job(download_file_task)

def queue_download(file_links_dict, model_name):
    global download_queue
    folder_name = model_name.split("/")[-1]
    current_dir = Path(__file__).parent
    download_path = current_dir.parent / f"/content/Ollama-Companion/llama.cpp/models/{folder_name}"
    download_path.mkdir(parents=True, exist_ok=True)

    with queue_lock:
        for file_name, file_url in file_links_dict.items():
            filename = Path(file_name).name
            download_queue.append((file_url, download_path, filename))

    # Start the first download
    if download_queue:
        scheduler.add_job(download_file_task)

    return "Download tasks have been queued."
def cancel_downloads():
    global scheduled_jobs, downloaded_files
    for job in scheduled_jobs:
        job.remove()
    scheduled_jobs.clear()

    for file_path in downloaded_files:
        if os.path.exists(file_path):
            os.remove(file_path)
    downloaded_files.clear()

    return "All queued downloads have been cancelled and files removed."

def construct_hf_repo_url(model_name):
    base_url = "https://huggingface.co/api/models/"
    return f"{base_url}{model_name}/tree/main"

def get_files_from_repo(url, repo_name):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            files_info = response.json()
            file_info_dict = {}
            file_links_dict = {}

            base_url = f"https://huggingface.co/{repo_name}/resolve/main/"
            for file in files_info:
                name = file.get('path', 'Unknown')
                size = file.get('size', 0)
                human_readable_size = f"{size / 1024 / 1024:.2f} MB"
                file_info_dict[name] = human_readable_size
                file_links_dict[name] = base_url + name

            return file_info_dict, file_links_dict
        else:
            return {}, {}
    except Exception as e:
        return {}, {}

def show_downloading_models_page():
    st.title("Model Downloader")

    model_name = st.text_input("Download PyTorch models from Hugginface", "Use the HuggingfaceUsername/Modelname")
    instruction = st.text("Instructions  . For example")
    if st.button("Get File List"):
        _, file_links = get_files_from_repo(construct_hf_repo_url(model_name), model_name)
        if file_links:
            st.session_state['file_links_dict'] = file_links
            files_info = "\n".join(f"{name}, Size: {size}" for name, size in file_links.items())
            st.text_area("Files Information", files_info, height=300)
        else:
            st.error("Unable to retrieve file links.")
            if 'file_links_dict' in st.session_state:
                del st.session_state['file_links_dict']

    if st.button("Download Files"):
        if 'file_links_dict' in st.session_state and st.session_state['file_links_dict']:
            queue_message = queue_download(st.session_state['file_links_dict'], model_name)
            st.text(queue_message)
        else:
            st.error("No files to download. Please get the file list first.")

    if st.button("Stop Downloads"):
        cancel_message = cancel_downloads()
        st.text(cancel_message)
    with st.expander("How to Download Model Files from Hugging Face", expanded=False):
        st.markdown("""
        **How to Download Model Files from Hugging Face**

        - First, visit the Hugging Face model page that you want to download. For example, if you want to download the model at this link: [https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2).

        - On the model page, locate the icon next to the username of the model's author. This icon typically looks like a clipboard or a copy symbol. Click on this icon to copy the Username/RepositoryName, which in this example is `mistralai/Mistral-7B-Instruct-v0.2`.

        - Paste the copied Username/RepositoryName `mistralai/Mistral-7B-Instruct-v0.2` directly into the input field.

        - Click the "Get file list" button or option to retrieve the list of files available in this repository.

        - Review the list of files to ensure you have the correct model files that you want to download.

        - Finally, click the "Download Model" button or option to initiate the download process for the selected model files.

        - The model files will be saved in the `llama.cpp/models` directory on your device.

        - Now you have successfully downloaded the model files from Hugging Face, and they are stored in the `llama.cpp/models` directory for your use.
        """)
