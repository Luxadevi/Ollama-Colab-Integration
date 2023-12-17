#!/bin/bash

# Global variable to identify if running in a Jupyter environment
IS_JUPYTER=false
if [ -d "/content/Ollama-Companion/" ]; then
    IS_JUPYTER=true
fi

# Function to check if a command exists in executable paths
is_command_installed() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a specific version of Python is installed
is_python_installed() {
    if is_command_installed python3; then
        local python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        if [[ "$python_version" < "3.10" ]]; then
            echo "Python 3.10 or later is required. Installed version is $python_version."
            return 1
        fi
        echo "Python 3.10 or later is already installed."
        return 0
    else
        echo "Python 3.10 is not installed."
        return 1
    fi
}

# Function to check if Docker is installed
is_docker_installed() {
    is_command_installed docker
}

# Function to install Docker based on OS
install_docker() {
    if is_docker_installed; then
        echo "Docker is already installed."
        return 0
    fi

    local os=$(detect_os)
    case "$os" in
        debian)
            sudo apt-get update && sudo apt-get install -y docker.io
            ;;
        redhat)
            sudo yum update && sudo yum install -y docker
            ;;
        arch)
            sudo pacman -Syu && sudo pacman -S docker
            ;;
        macos)
            brew install docker
            ;;
        *)
            echo "Unsupported OS for Docker installation."
            return 1
            ;;
    esac
    echo "Docker installed successfully."
    return 0
}

# Function to configure Docker
configure_docker() {
    local os=$(detect_os)
    if [ "$os" != "macos" ] && [ "$os" != "jupyter" ]; then
        sudo groupadd docker 2>/dev/null || true
        sudo usermod -aG docker $USER
        sudo systemctl start docker
        sudo systemctl enable docker
        echo "Docker configured successfully."
    else
        echo "Docker configuration not required for macOS or Jupyter environments."
    fi
    return 0
}

# Function to install essential packages
install_packages() {
    local packages=("gcc" "make" "aria2" "git" "pciutils" )
    local install_needed=false

    for package in "${packages[@]}"; do
        if ! is_command_installed "$package"; then
            install_needed=true
            break
        fi
    done

    if [ "$install_needed" = false ]; then
        echo "All essential packages are already installed."
        return 0
    fi

    local os=$(detect_os)
    case "$os" in
        debian)
            sudo apt-get update && sudo apt-get install -y "${packages[@]}"
            ;;
        redhat)
            sudo yum update && sudo yum install -y "${packages[@]}"
            ;;
        arch)
            sudo pacman -Syu && sudo pacman -S --noconfirm "${packages[@]}"
            ;;
        macos)
            brew install "${packages[@]}"
            ;;
        *)
            echo "Unsupported OS for package installation."
            return 1
            ;;
    esac
    echo "Packages installed successfully."
    return 0
}

# Function to change ownership and permissions of all files and directories
# Function to change ownership and permissions of all files and directories
change_file_ownership() {
    # Check if running in Jupyter environment
    if $IS_JUPYTER; then
        echo "In Jupyter environment, skipping chown commands."
        return 0
    fi

    local script_dir="$(dirname "$(realpath "$0")")"
    echo "Changing ownership of all files and directories in $script_dir for Linux environment..."

    # Change ownership to the current user for all files and directories
    find "$script_dir" -exec chown $USER {} \;

    # Change file permissions to read, write, and execute for the owner
    find "$script_dir" -type f -exec chmod u+rwx {} \;
    find "$script_dir" -type d -exec chmod u+rwx {} \;

    echo "Ownership and permissions changed successfully."
}
# Function to determine the operating system
detect_os() {
    if is_jupyter; then
        echo "jupyter"
        return 0
    fi

    local os_name=$(uname -s)
    case "$os_name" in
        Darwin)
            echo "macos"
            ;;
        Linux)
            if grep -qi ubuntu /etc/os-release; then
                echo "debian"
            elif grep -qi centos /etc/os-release; then
                echo "redhat"
            elif grep -qi arch /etc/os-release; then
                echo "arch"
            else
                echo "Unsupported Linux OS."
                return 1
            fi
            ;;
        *)
            echo "Unsupported OS."
            return 1
            ;;
    esac
    return 0
}

# Function to clone the llama.cpp repository
clone_repository() {
    if $IS_JUPYTER; then
        mkdir -p /content/Ollama-Companion
        if git clone https://github.com/ggerganov/llama.cpp.git /content/Ollama-Companion/llama.cpp; then
            echo "Repository cloned successfully into Jupyter environment."
        else
            echo "Failed to clone repository into Jupyter environment."
            return 1
        fi
    elif git clone https://github.com/ggerganov/llama.cpp.git; then
        echo "Repository cloned successfully."
    else
        echo "Failed to clone repository."
        return 1
    fi
    return 0
}


install_python_requirements() {
    local required_packages=("streamlit" "requests" "flask" "flask-cloudflared" "httpx" "litellm" "huggingface_hub" "asyncio" "Pyyaml" "httpx" "APScheduler" "cryptography" "pycloudflared" "numpy==1.24.4" "sentencepiece==0.1.98" "transformers>=4.34.0" "gguf>=0.1.0" "protobuf>=4.21.0" "torch==2.1.1" "transformers==4.35.2")

    for package in "${required_packages[@]}"; do
        if pip install "$package"; then
            echo "$package installed successfully."
        else
            echo "Failed to install $package."
            return 1
        fi
    done

    echo "All required Python packages installed successfully."
    return 0
}
build_llama_cpp() {
    if $IS_JUPYTER; then
        # Jupyter Notebook specific build steps
        if [ -d "/content/Ollama-Companion/llama.cpp" ]; then
            if make -C /content/Ollama-Companion/llama.cpp; then
                echo "llama.cpp built successfully in Jupyter Notebook environment."
            else
                echo "Failed to build llama.cpp in Jupyter Notebook environment."
                return 1
            fi
        else
            echo "/content/Ollama-Companion/llama.cpp directory not found."
            return 1
        fi
    else
        # Existing logic for other environments
        if [ -d "llama.cpp" ]; then
            cd llama.cpp || return 1
            if make; then
                echo "llama.cpp built successfully using make."
            else
                echo "Failed to build llama.cpp using make."
                return 1
            fi
            cd - || return 1
        else
            echo "llama.cpp directory not found."
            return 1
        fi
    fi
    return 0
}

install_ollama() {
    if $IS_JUPYTER; then
        mkdir -p /content/Ollama-Companion
        curl https://ollama.ai/install.sh > /content/Ollama-Companion/ollama_install.sh
        chmod +x /content/Ollama-Companion/ollama_install.sh
        /content/Ollama-Companion/ollama_install.sh
        echo "Ollama installed in Jupyter environment."
    else
        read -p "Do you want to install Ollama on this host? (y/n) " answer
        case $answer in
            [Yy]* )
                curl https://ollama.ai/install.sh | sh
                echo "Ollama installed on this host."
                ;;
            * )
                echo "Ollama installation skipped."
                ;;
        esac
    fi
}

# Function to run the key_generation script
run_key_generation() {
    local script_dir="$(dirname "$(realpath "$0")")"
    pushd "$script_dir" > /dev/null || return 1
    if python3 "./key_generation.py"; then
        echo "Key generation script executed successfully."
    else
        echo "Key generation script execution failed."
        popd > /dev/null || return 1
        return 1
    fi
    popd > /dev/null || return 1
    return 0
}

main() {
    local os=$(detect_os)

    if [ "$os" = "Unsupported OS." ]; then
        echo "Exiting due to unsupported OS."
        exit 1
    fi

    if ! is_python_installed; then
        echo "Python 3.10 or later is required but not installed. Exiting."
        exit 1
    fi

    install_docker "$os" && configure_docker "$os"
    install_packages "$os"
    clone_repository
    build_llama_cpp
    install_python_requirements
    change_file_ownership
    install_ollama
    # Run the key generation script with the correct path
    run_key_generation "$(dirname "$(realpath "$0")")"

    echo "Installation complete."
}

main
