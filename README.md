# Progetto-Laboratorio-D-Informatica-Applicata

To give wsl access to the webcam, you need to install through windows powershell "usbipd" and then run usbipd attach:

wsl --update
winget install usbipd
usbipd list
usbipd --busid 1-5 --wsl

This whole procedure can be replicated by launching "run.ps1".
If you succeded, you should be able to see a file named "video0" by using "ls -l /dev/video0" in wsl.
