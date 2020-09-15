Original code taken from: https://github.com/rampage128/arduinoMmi/

# Show/hide cursor
Discussed in: https://bluewavestudio.io/community/showthread.php?tid=596

Open command line and execute
`sudo bwscursor show`

# Changes to Rapsberry Pi Config
Open /boot/config.txt

Add te following lines to enable uarts 3-5

    [audi-mmi]
    dtoverlay=uart3
    dtoverlay=uart4
    dtoverlay=uart5


# Tools
https://pimylifeup.com/raspberry-pi-visual-studio-code/

# Remote Debugging
https://www.linkedin.com/pulse/python-remote-debugging-visual-studio-code-raspberry-pi-mircea-dogaru/

# Open Auto Config
https://bluewavestudio.io/community/showthread.php?tid=593&pid=7208&highlight=openauto_controller_service#pid7208
    
    [Controller]
    Type=1
    Interface=/dev/ttyAMA0
    DoublePressSpeed=300