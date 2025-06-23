# ========================
# USBIPD Script for WSL
# ========================

function Is-Usbipd-Available {
    return (Get-Command usbipd -ErrorAction SilentlyContinue) -ne $null
}

# Check if usbipd is installed
if (-not (Is-Usbipd-Available)) {
    Write-Output "usbipd not found. Updating WSL and installing via winget..."

    wsl --update

    winget install usbipd

    # Force reload of current PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")

    if (-not (Is-Usbipd-Available)) {
        Write-Error "usbipd was installed but is not available in PATH. Restart the shell or PC and try again."
        exit 1
    }

    Write-Output "usbipd successfully installed."
} else {
    Write-Output "usbipd is already installed."
}

# Check and start the usbipd service
$service = Get-Service -Name "usbipd" -ErrorAction SilentlyContinue
if ($service -and $service.Status -ne "Running") {
    Start-Service usbipd
    Write-Output "usbipd service started."
} elseif (-not $service) {
    Write-Warning "The 'usbipd' service is not registered. A system reboot might be required."
}

# List USB devices
Write-Output "Available USB devices:"
usbipd list

# User input
$deviceId = Read-Host "Enter the webcam ID to attach (e.g., 2-6)"

# Bind the device as administrator
Write-Output "Administrator privileges required to bind the device..."
Start-Process "usbipd" -ArgumentList "bind --busid $deviceId" -Verb RunAs -Wait

# Attach the device to WSL
usbipd attach --busid $deviceId --wsl

Write-Output "Webcam with BusID $deviceId successfully attached to WSL."
