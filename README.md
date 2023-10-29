# OLLAMA Google Colab Version



## Overview
This repository offers an all-encompassing solution to run large language models in the cloud via Ollama. Designed for secure and scalable access to cloud-hosted language models, this setup is especially beneficial for leveraging advanced AI capabilities from remote locations. It's ideal for researchers, developers, and businesses seeking to manage intensive computational tasks in the cloud.

### Features
- **NAT Tunneling**: Secure access to large language models in the cloud.
- **Background Processing**: Run Ollama and the NAT tunnel as background services for uninterrupted operations.
- **Monitoring**: Constant monitoring of Ollama and the NAT tunnel for dependable service.
- **Logging**: Comprehensive logging of Ollama and NAT tunnel activities for analysis and troubleshooting.
- **Interactive Modelfile Creator**: Customize responses from Ollama with an easy-to-use Modelfile creator.

## Installation
### 1. Dependencies
Follow our detailed installation guide to set up essential dependencies like CUDA, Ollama, and NAT tunneling configurations.

### 2. Setup Ollama and NAT Tunnel
Configure and launch the Ollama service and NAT tunnel using the provided scripts, ensuring secure operations with your secret password and endpoint IP address.

## Usage
### Running the Services
Initiate the Ollama and NAT tunnel services with the provided Python script. This script guarantees that both services will continuously operate in the background and will automatically restart if any issues occur.

### Self-Checks and Dynamic Monitoring
The setup includes self-check mechanisms and dynamic monitoring for the `natsrv.py` application, ensuring high availability and performance. Regular health checks and automated restarts help in maintaining continuous, trouble-free operation.

### Interactive Modelfile Creator
The Jupyter notebook interface allows for easy creation and deployment of custom Modelfiles. You can select desired models, adjust parameters, and define custom template variables for specific AI behaviors.

## Logs
Logs are auto-generated for Ollama and the NAT tunnel, offering insights into their operational status and assisting in troubleshooting. They are stored in:
- **Ollama Logs**: `ollama.log` and `ollama_error.log`
- **NAT Tunnel Logs**: `natsrv.log` and `natsrv_error.log`
- **General Status and Error Logs**: `status.log` and `error.log`

## Troubleshooting
- **Memory Issues**: Address crashes due to VRAM limitations by using smaller models or restarting the services.
- **Connectivity Issues**: Check your NAT tunnel configuration and ensure that necessary ports are forwarded properly.

## Contributing
Contributions are welcome! Fork the repository, make your changes, and submit a pull request.

## TODO
- Introduce dynamic log viewing features.
- Add more functions for improved interactions with the Ollama API.
- Develop a more intuitive setup and monitoring interface.

### Acknowledgements
Special thanks to [rofl0r](https://github.com/rofl0r) for developing the "nat-tunnel," which plays a crucial role in this setup.

## License
This project is licensed under the [MIT License](LICENSE.md).

---
