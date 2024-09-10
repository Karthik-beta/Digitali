# Define URLs for Python 3.10 and Node.js 20 LTS installers
$pythonUrl = "https://www.python.org/ftp/python/3.10.12/python-3.10.12-amd64.exe"
$nodeUrl = "https://nodejs.org/dist/v20.17.0/node-v20.17.0-x64.msi"

# Define file paths for the installers
$pythonInstaller = "python-3.10.12-amd64.exe"
$nodeInstaller = "node-v20.17.0-x64.msi"

# Download Python installer
Write-Output "Downloading Python 3.10 installer..."
Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller

# Download Node.js installer
Write-Output "Downloading Node.js 20 LTS installer..."
Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeInstaller

# Install Python 3.10
Write-Output "Installing Python 3.10..."
Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait

# Install Node.js 20 LTS
Write-Output "Installing Node.js 20 LTS..."
Start-Process -FilePath $nodeInstaller -ArgumentList "/quiet" -Wait

# Verify installations
Write-Output "Verifying Python installation..."
python --version

Write-Output "Verifying Node.js installation..."
node --version
npm --version

Write-Output "Installation complete."