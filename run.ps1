# Verifica se usbipd è installato
if (-not (Get-Command usbipd -ErrorAction SilentlyContinue)) {
    Write-Output "usbipd non trovato. Scarico e installo..."

    Invoke-WebRequest -Uri "https://github.com/dorssel/usbipd-win/releases/latest/download/usbipd-win.msi" `
                      -OutFile "$env:TEMP\usbipd-win.msi"

    Start-Process msiexec.exe -Wait -ArgumentList "/i `"$env:TEMP\usbipd-win.msi`" /qn"
    Write-Output "usbipd installato."
} else {
    Write-Output "usbipd è già installato."
}

# Avvia il servizio (se non è già attivo)
Start-Service usbipd

# Mostra tutti i dispositivi USB condivisibili
Write-Output "Dispositivi USB disponibili:"
usbipd list

# Chiedi all’utente di inserire l'ID del dispositivo
$deviceId = Read-Host "Inserisci l'ID della webcam da attaccare (es: 1-4)"

# Collega il dispositivo alla WSL
usbipd wsl attach --busid $deviceId --wsl

Write-Output "Webcam con BusID $deviceId collegata a WSL"
