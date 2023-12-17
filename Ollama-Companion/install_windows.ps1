# Install Python 3.10
$pythonInstalled = Get-Command python | ForEach-Object { $_.Version.Major }

if ($pythonInstalled -notcontains 3.10 -and $pythonInstalled -notcontains 3.11) {
    winget install -e --id Python.Python.3.10
} else {
    Write-Host "Python 3.10 or 3.11 is already installed."
}


# Attempt to install Python requirements
# List of required libraries
$requiredLibs = @('streamlit', 'requests', 'flask', 'flask-cloudflared', 'httpx', 'litellm', 'huggingface_hub', 'asyncio', 'Pyyaml', 'APScheduler', 'cryptography', 'gradio','numpy','sentencepiece','gguf','torch','transformers' )

# Array to hold libraries that are not installed
$libsToInstall = @()

foreach ($lib in $requiredLibs) {
    try {
        pip show $lib | Out-Null
    } catch {
        $libsToInstall += $lib
    }
}

if ($libsToInstall.Length -gt 0) {
    Write-Host "The following libraries are not installed and will be installed:"
    Write-Host ($libsToInstall -join ", ")

    # Confirmation prompt
    $confirmation = Read-Host "Do you want to proceed with the installation? (Y/N)"
    if ($confirmation -eq 'Y') {
        try {
            pip install $libsToInstall -ErrorAction Stop
        } catch {
            Write-Host "An error occurred during pip install. Please relog your account and try running the script again."
            Exit
        }
    } else {
        Write-Host "Installation canceled."
    }
} else {
    Write-Host "All required libraries are already installed."
}


# Function to check if CMake is installed
function Check-CMakeInstalled {
    try {
        $cmakeVersion = cmake --version | Select-Object -First 1
        if ($cmakeVersion -like "cmake version*") {
            return $true
        }
    } catch {
        return $false
    }
}

# Check if CMake is installed
$cmakeInstalled = Check-CMakeInstalled

if (-not $cmakeInstalled) {
    Write-Host "CMake is not installed."

    # Ask for confirmation to install CMake
    $confirmation = Read-Host "Do you want to install CMake? (Y/N)"
    if ($confirmation -eq 'Y') {
        # Download and install CMake
        $cmakeInstaller = "https://github.com/Kitware/CMake/releases/download/v3.28.0/cmake-3.28.0-windows-x86_64.msi"
        $installerPath = "$env:TEMP\cmake_installer.msi"
        Invoke-WebRequest -Uri $cmakeInstaller -OutFile $installerPath
        Start-Process msiexec.exe -Wait -ArgumentList "/i $installerPath /quiet /norestart"
        Write-Host "CMake has been installed."
    } else {
        Write-Host "Installation of CMake canceled."
    }
} else {
    Write-Host "CMake is already installed."
}


# Build llama.cpp with CMake
if (Test-Path -Path ".\llama.cpp") {
    New-Item -Path ".\llama.cpp\build" -ItemType "directory" -Force
    Set-Location -Path ".\llama.cpp\build"
    cmake .. -DLLAMA_CUBLAS=ON
    cmake --build . --config Release
    Set-Location -Path "..\.."
}

# Function to check if aria2 is installed
function Check-Aria2Installed {
    try {
        $aria2Version = aria2c --version | Select-Object -First 1
        if ($aria2Version -like "aria2 version*") {
            return $true
        }
    } catch {
        return $false
    }
}

# Check if aria2 is installed
$aria2Installed = Check-Aria2Installed

if (-not $aria2Installed) {
    Write-Host "aria2 is not installed."

    # Ask for confirmation to install aria2
    $confirmation = Read-Host "Do you want to install aria2? (Y/N)"
    if ($confirmation -eq 'Y') {
        # Install aria2 using winget
        winget install --id=aria2.aria2 -e
        Write-Host "aria2 has been installed."
    } else {
        Write-Host "Installation of aria2 canceled."
    }
} else {
    Write-Host "aria2 is already installed."
}

#make non .exe copies of the .exe's
Get-ChildItem -Path ".\llama.cpp" -Recurse -Filter *.exe | ForEach-Object {
    $linkName = $_.FullName -replace '\.exe$', ''
    New-Item -ItemType HardLink -Path $linkName -Target $_.FullName
}

# fix up the installs the be in the places we expect.
Get-ChildItem -Path .\llama.cpp\build\bin\Release -Filter *.exe | Where-Object { $_.Name -notin @('benchmark.exe', 'test-c.exe', 'test-grad0.exe', 'test-grammar-parser.exe', 'test-llama-grammar.exe', 'test-quantize-fns.exe', 'test-quantize-perf.exe', 'test-rope.exe', 'test-sampling.exe', 'test-tokenizer-0-falcon.exe', 'test-tokenizer-0-llama.exe', 'test-tokenizer-1-bpe.exe', 'test-tokenizer-1-llama.exe') } | ForEach-Object { Copy-Item -Path $_.FullName -Destination .\llama.cpp -Verbose; if (Test-Path ($_.FullName -replace '\.exe$','')) { New-Item -ItemType HardLink -Path (Join-Path .\llama.cpp $_.BaseName) -Target $_.FullName } }


# Final message
Write-Host "Thanks for installing the windows version. This OS is not fully supported with Ollama but you can still use this program to interface with an Ollama endpoint or use the quantizing features."
