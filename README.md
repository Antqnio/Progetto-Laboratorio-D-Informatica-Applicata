# Progetto-Laboratorio-D-Informatica-Applicata

To give wsl access to the webcam you need to install through windows powershell "usbipd" and then run usbipd attach --busid 1-5 --wsl with wsl opened.
If you succeded you should be able to see a file named video0 by using "ls -l /dev/video0" in wsl.
