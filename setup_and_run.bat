@echo off
echo ComicCrafter AI - Setup and Launch Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python 3.10 and try again.
    echo You can download Python from https://www.python.org/downloads/
    pause
    exit /b
)

REM Check if Git is installed
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Git is not installed or not in PATH. Git is required for downloading components.
    echo You can download Git from https://git-scm.com/downloads
    pause
    exit /b
)

REM Create virtual environment if it doesn't exist
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create models directory if it doesn't exist
if not exist models (
    mkdir models
)

REM Check and download Mistral 7B if not present
if not exist models\mistral-7b-instruct-v0.2.Q4_K_M.gguf (
    echo Mistral 7B model not found. Downloading...
    
    REM Install GDOWN for downloading large files from Google Drive
    pip install gdown
    
    REM Download the Mistral 7B model (quantized version for better performance)
    echo Downloading Mistral 7B model (this may take a while)...
    
    REM First try huggingface-cli
    pip install huggingface_hub
    python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='TheBloke/Mistral-7B-Instruct-v0.2-GGUF', filename='mistral-7b-instruct-v0.2.Q4_K_M.gguf', local_dir='models')"
    
    REM Check if download was successful
    if not exist models\mistral-7b-instruct-v0.2.Q4_K_M.gguf (
        echo Failed to download Mistral 7B model using huggingface_hub.
        echo Please download it manually from https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/blob/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf
        echo and place it in the 'models' folder.
    ) else (
        echo Mistral 7B model downloaded successfully.
    )
)

REM Check and download Stable Diffusion WebUI if not present
if not exist stable-diffusion-webui (
    echo Stable Diffusion WebUI not found. Downloading...
    git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
    
    REM Download Stable Diffusion 1.5 model
    if not exist stable-diffusion-webui\models\Stable-diffusion (
        mkdir stable-diffusion-webui\models\Stable-diffusion
    )
    
    echo Downloading Stable Diffusion 1.5 model (this may take a while)...
    pip install huggingface_hub
    python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='runwayml/stable-diffusion-v1-5', filename='v1-5-pruned-emaonly.safetensors', local_dir='stable-diffusion-webui/models/Stable-diffusion')"
    
    REM Check if download was successful
    if not exist stable-diffusion-webui\models\Stable-diffusion\v1-5-pruned-emaonly.safetensors (
        echo Failed to download Stable Diffusion 1.5 model.
        echo Please download it manually from https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors
        echo and place it in the 'stable-diffusion-webui\models\Stable-diffusion' folder.
    ) else (
        echo Stable Diffusion 1.5 model downloaded successfully.
    )
    
    REM Run Stable Diffusion WebUI install script
    cd stable-diffusion-webui
    echo Running Stable Diffusion WebUI install script (this may take a while)...
    call webui-user.bat
    cd ..
)

REM Start Stable Diffusion WebUI in a new window
echo Starting Stable Diffusion WebUI...
start cmd /c "cd stable-diffusion-webui && webui.bat --api"

REM Wait for Stable Diffusion to start
echo Waiting for Stable Diffusion to initialize (60 seconds)...
timeout /t 60 /nobreak

REM Start the Streamlit app and open in browser automatically
echo Launching ComicCrafter AI...
start "" http://localhost:8501
streamlit run app/main.py

REM Keep the window open if there's an error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred. Please check the output above.
    pause
)

exit /b 