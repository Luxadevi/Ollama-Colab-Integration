import os
import subprocess
import streamlit as st
from shared import shared  # Importing the shared dictionary
from apscheduler.schedulers.background import BackgroundScheduler
from pathlib import Path
import sys

# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.start()

def list_gguf_files(models_dir):
    gguf_files = []
    if os.path.exists(models_dir):
        for model_folder in os.listdir(models_dir):
            hpq_folder = os.path.join(models_dir, model_folder, 'High-Precision-Quantization')
            if os.path.exists(hpq_folder) and os.path.isdir(hpq_folder):
                for file in os.listdir(hpq_folder):
                    if file.lower().endswith('.gguf'):
                        gguf_files.append(os.path.join(model_folder, 'High-Precision-Quantization', file))
    return gguf_files

def schedule_quantize_task(command):
    try:
        subprocess.run(command, check=True)
        return f"Task completed: {' '.join(command)}"
    except subprocess.CalledProcessError as e:
        return f"Error in task execution: {e}"

def trigger_command(modelpath, options, use_docker):
    if not any(options.values()):
        return "Error: Please select at least one quantization option."

    debug_output = ""
    base_dir = Path('llama.cpp', 'models')
    modelpath_path = Path(modelpath)
    model_name_only, model_file = modelpath_path.parts[-3], modelpath_path.name
    medium_precision_dir = base_dir / model_name_only / 'Medium-Precision-Quantization'
    medium_precision_dir.mkdir(parents=True, exist_ok=True)
               
    for option, selected in options.items():
        if selected:
            volume_path = base_dir.resolve().drive   # This will be 'D:' on Windows if base_dir is on D drive
            source_path = base_dir / model_name_only / 'High-Precision-Quantization' / model_file
            modified_model_file = model_file.lower().replace('f16.gguf', '').replace('q8_0.gguf', '').replace('f32.gguf', '')
            output_path = medium_precision_dir / f"{modified_model_file}-{option.upper()}.GGUF"
            absolute_path = os.getcwd().replace('\\', '/')

            
            if use_docker:
                
                docker_image = "luxaplexx/convert-compaan-ollama"

                #volume_path = base_dir.resolve().as_posix()  # On Unix-like systems, the full path is used

                base_dir = 'llama.cpp/models'

                output_path_in_docker = f"/models/{model_name_only}/Medium-Precision-Quantization/{modified_model_file}-{option.upper()}.GGUF"
                command = [
                    "docker", "run", "--rm",
                    "-v", f"{absolute_path}\\{base_dir}:/models",
                    docker_image, "quantize", f"/models/{model_name_only}/High-Precision-Quantization/{model_file}",
                    str(output_path_in_docker), option
                ]
            else:
                command = [str(base_dir / 'quantize'), str(source_path), str(output_path), option]

            print (command)

            scheduler.add_job(schedule_quantize_task, args=[command])
            debug_command_str = ' '.join(command)
            debug_output += f"Scheduled: {debug_command_str}\n"

    return debug_output if debug_output else "No options selected."


def show_medium_precision_quantization_page():
    st.title("Medium Precision Quantization")

    models_dir = os.path.join("llama.cpp", "models")
    gguf_files = list_gguf_files(models_dir)

    selected_gguf_file = st.selectbox("Select a GGUF File", gguf_files)
    options = {option: st.checkbox(label=option) for option in shared['checkbox_options']}
    use_docker = st.checkbox("Use Docker Container")

    run_commands = st.button("Run Selected Commands")

    if run_commands:
        # Check if no quantization type options are selected
        if not any(options.values()):
            st.error("Please select at least one quantization type before running commands.")
        # Proceed only if at least one quantization type is selected or if Docker is selected with a type
        elif any(options.values()) or (use_docker and any(options.values())):
            status = trigger_command(selected_gguf_file, options, use_docker)
            st.text_area("Debug Output", status, height=300)
        else:
            # This should not happen, but we include it for robustness
            st.error("Unexpected condition: No options selected.")

    with st.expander("Step Two: Model Quantization Q and Kquants", expanded=False):
        st.markdown("""
        **Step Two: Model Quantization Q and Kquants**

        In this step, you will perform model quantization using Q and Kquants. The files found in the `llama.cpp/models/modelname/High-Precision-Quantization` folder will be displayed here.

        **Instructions:**

        1. Select the GGUF file you want to quantize from the dropdown list.
        2. Check the boxes next to the quantization options you want to apply (Q, Kquants).
        3. Choose whether to use the native `llama.cpp` or a Docker container for compatibility.
        4. Click the "Run Selected Commands" button to schedule and execute the quantization tasks.
        5. The quantized models will be saved in the `/modelname/Medium-Precision-Quantization` folder.
        """)

