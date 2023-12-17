import subprocess
import threading
import queue
import streamlit as st
from shared import shared
from pathlib import Path
import sys

# Initialize queue and start a background thread for processing commands
command_queue = queue.Queue()

def process_queue():
    while True:
        model_folder, out_type, use_docker = command_queue.get()
        result = run_command(model_folder, out_type, use_docker)
        print(result)
        command_queue.task_done()

def run_command(model_folder, out_type, use_docker):
    base_dir = Path("llama.cpp/models")
    input_dir = base_dir / model_folder
    target_dir = input_dir / "High-Precision-Quantization"
    output_file = f"{model_folder}-{out_type}.GGUF"

    target_dir.mkdir(parents=True, exist_ok=True)

    if use_docker:
        docker_image = "luxaplexx/convert-compaan-ollama"
        # Docker volume paths need to be in Linux format even on Windows
        if sys.platform.startswith('win'):
            volume_path = base_dir.resolve().drive  # This will be 'D:' on Windows if base_dir is on D drive
        else:
            volume_path = base_dir.resolve().as_posix()  # On Unix-like systems, the full path is used
        output_path = Path(f"./models/{model_folder}/High-Precision-Quantization/{output_file}").as_posix()
        command = [
            "docker", "run", "--rm",
            "-v", f"{volume_path}/models",
            docker_image, "convert", Path("./models") / model_folder,
            "--outfile", output_path.as_posix(),
            "--outtype", out_type.lower()
        ]
    else:
        command = [
            "python3", str(Path("llama.cpp/convert.py")),
            str(input_dir),
            "--outfile", str(target_dir / output_file),
            "--outtype", out_type.lower()
        ]


    try:
        subprocess.run(command, check=True)
        return "Command completed successfully."
    except subprocess.CalledProcessError as e:
        return f"Error in command execution: {e}"


def trigger_command(model_folder, options, use_docker):
    if not any(options.values()):
        return "Error: No quantization type selected."
    for option in options:
        if options[option]:
            command_queue.put((model_folder, option.lower(), use_docker))
    return "Commands queued. They will run sequentially."

def show_high_precision_quantization_page():
    st.title("High Precision Quantization")

    models_dir = Path("llama.cpp/models/")
    model_folders = [f.name for f in models_dir.iterdir() if f.is_dir()] if models_dir.exists() else ["Directory not found"]

    model_folder = st.selectbox("Select a Model Folder", model_folders)
    options = {option: st.checkbox(label=option) for option in shared['checkbox_high_options']}
    use_docker = st.checkbox("Use Docker Container")

    if st.button("Run Commands"):
        if not any(options.values()):
            st.error("Please select at least one quantization type before running commands.")
        elif use_docker and not any(options.values()):
            st.error("Please select at least one quantization type along with the Docker option.")
        else:
            status = trigger_command(model_folder, options, use_docker)
            st.text(status)


    with st.expander("Step One: Model Conversion with High Precision", expanded=False):
        st.markdown("""
        **Step One: Model Conversion with High Precision**


        **Conversion Process:**

        1. **Select a Model Folder:** Choose a folder containing the model you wish to convert, found within `llama.cpp/models`.
        2. **Set Conversion Options:** Select the desired conversion options from the provided checkboxes (e.g., Q, Kquants).
        3. **Docker Container Option:** Opt to use a Docker container for added flexibility and compatibility.
        4. **Execute Conversion:** Click the "Run Commands" button to start the conversion process.
        5. **Output Location:** Converted models will be saved in the `High-Precision-Quantization` subfolder within the chosen model folder.

        Utilize this process to efficiently convert models while maintaining high precision and compatibility with `llama.cpp`.
        """)
    # Start the thread to process commands
threading.Thread(target=process_queue, daemon=True).start()