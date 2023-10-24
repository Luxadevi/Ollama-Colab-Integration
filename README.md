# OLLAMA Google Colab Version



## Overview

OLLAMA is a tool designed for running OLLAMA models in a Google Colab environment with minimal resource costs. This version utilizes NAT tunneling to make your OLLAMA instance publicly accessible, allowing users to interact with it from external locations.
### Disclaimer 

This is a work in progres subject to change.

### Features

- Simplified installation of the latest CUDA drivers.
- GPU information retrieval through `pciutils`.
- Installation of OLLAMA for language model operations.
- Setup of a tunnel to access the OLLAMA API.
- Simulated port utilization for the tunnel.
- Download of a model file for testing.
- Modelfile under /content/ with modelcodellama:13b-instruct


## Setup

To use OLLAMA in Google Colab, follow these setup steps:

1. **CUDA Drivers and Toolkit Installation:**

    Download and install the latest CUDA drivers and toolkit for GPU support.

2. **OLLAMA Installation:**

    Install OLLAMA for running language models.

3. **Model File Download:**

    Download a model file for testing purposes. The file should be saved in the `/content/` directory.

4. **NAT Tunneling Setup:**

    To make your OLLAMA instance publicly accessible, set up NAT tunneling:

    - Download the NAT tunneling tool (details provided in the repository).
    - Ensure at least one port is exposed to receive connections.
    - On the server side, run `natsrv.py` with the appropriate configuration.

5. **Tunneling:**

    Start the tunnel application to establish the connection. A Python script simulates a port being in use.

## Usage

To use OLLAMA in Google Colab with public access:

1. **Start Tunneling:**

    - Run the command to initiate NAT tunneling and connect to the server.
    - Input your IP address and a secret when prompted.

2. **Running OLLAMA:**

    Choose one of the following options to run OLLAMA:

    - Run OLLAMA in the terminal output for debugging and initial setup.
    - Run OLLAMA in the background for production use.

    Detailed commands are available in the repository.

3. **Check OLLAMA Status:**

    To check the status of your OLLAMA instance, use the provided command.
### TODO 

Develop a way to run Ollama as a service and restart itself when exited.


## Note

- Ensure that you have the latest drivers and CUDA toolkit installed for GPU support.
- For users behind an HTTP proxy, some adjustments may be required.
- Keep in mind that OLLAMA may close after a period of inactivity, so monitor its responsiveness.

Thanks to rofl0r for developing the nat-tunnel python app
https://github.com/rofl0r/nat-tunnel
This README provides an overview of the OLLAMA Google Colab version, its features, and guidance on setup and usage. The actual commands and code can be found in the .inypb file.
